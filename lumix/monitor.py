"""lumix-monitor: live view window for a LUMIX on USB, with histogram, zebras, LUT preview, AF and shutter.

  python -m lumix.monitor [--lut-dir DIR]

Keys: space = shutter, f = AF, z = zebras, l = next LUT preview (from --lut-dir), q = quit.
"""
import argparse
import glob
import io
import os
import queue
import threading
import time
import tkinter as tk

import numpy as np
from PIL import Image, ImageDraw, ImageTk

from . import liveview
from .ptp import Camera


def put_latest(q, item):
    """Keep only the newest item: drop whatever is waiting."""
    try:
        q.get_nowait()
    except queue.Empty:
        pass
    q.put(item)


def load_cube(path):
    rows, n = [], None
    for line in open(path):
        t = line.split()
        if not t:
            continue
        if t[0] == 'LUT_3D_SIZE':
            n = int(t[1])
        elif t[0][0].isdigit() or t[0][0] in '-.':
            rows.append([float(x) for x in t[:3]])
    return n, np.array(rows, np.float32).reshape(n, n, n, 3)  # [b][g][r]


def apply_lut(img, lut):
    n, t = lut
    a = np.asarray(img, np.float32) / 255 * (n - 1)
    i = np.clip(np.rint(a).astype(int), 0, n - 1)  # nearest node: fast enough for a preview
    out = t[i[..., 2], i[..., 1], i[..., 0]]
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))


class Monitor:
    def __init__(self, lut_dir=None, size=(1280, 960)):
        self.size = size
        self.raw = queue.Queue(maxsize=1)      # newest JPEG from USB
        self.ready = queue.Queue(maxsize=1)    # newest processed PIL image
        self.cmds = queue.Queue()
        self.t_fetch = self.t_proc = 0.0
        self.running = True
        self.zebras = False
        self.luts = sorted(glob.glob(os.path.join(lut_dir, '*.cube'))) if lut_dir else []
        self.lut_i = -1
        self.lut = None
        self.status = 'connecting…'
        self.root = tk.Tk()
        self.root.title('lumix-monitor')
        self.root.configure(bg='#111')
        self.view = tk.Label(self.root, bg='#111')
        self.view.pack(padx=8, pady=8)
        bar = tk.Frame(self.root, bg='#111'); bar.pack(fill='x', padx=8, pady=(0, 8))
        for text, fn in (('AF (f)', self.af), ('Shutter (space)', self.shoot), ('Zebras (z)', self.toggle_zebras),
                         ('LUT preview (l)', self.next_lut), ('Quit (q)', self.quit)):
            tk.Button(bar, text=text, command=fn).pack(side='left', padx=3)
        self.info = tk.Label(bar, text='', fg='#ddd', bg='#111', font=('Menlo', 11))
        self.info.pack(side='left', padx=10)
        self.root.bind('<space>', lambda e: self.shoot()); self.root.bind('f', lambda e: self.af())
        self.root.bind('z', lambda e: self.toggle_zebras()); self.root.bind('l', lambda e: self.next_lut())
        self.root.bind('q', lambda e: self.quit()); self.root.protocol('WM_DELETE_WINDOW', self.quit)
        self.fps_t, self.fps_n, self.fps = time.time(), 0, 0.0
        threading.Thread(target=self.usb_loop, daemon=True).start()
        threading.Thread(target=self.proc_loop, daemon=True).start()
        self.root.after(5, self.ui_loop)

    # USB thread: owns the camera
    def usb_loop(self):
        try:
            with Camera() as cam:
                if self.size:
                    liveview.set_size(cam, *self.size)
                liveview.start(cam)
                self.status = 'live'
                while self.running:
                    while not self.cmds.empty():
                        cmd = self.cmds.get()
                        rc = liveview.autofocus(cam) if cmd == 'af' else liveview.shutter(cam)
                        self.status = f'{cmd}: {"ok" if rc == 0x2001 else hex(rc)}'
                    t0 = time.perf_counter()
                    jpg, _hdr = liveview.frame(cam)
                    self.t_fetch = time.perf_counter() - t0
                    put_latest(self.raw, jpg)
                liveview.stop(cam)
        except Exception as e:
            self.status = f'error: {e}'

    def proc_loop(self):
        while self.running:
            try:
                jpg = self.raw.get(timeout=0.2)
            except queue.Empty:
                continue
            t0 = time.perf_counter()
            img = Image.open(io.BytesIO(jpg)).convert('RGB')
            if self.lut:
                img = apply_lut(img, self.lut)
            a = np.asarray(img)
            if self.zebras:
                hot = a.max(2) >= 250
                if hot.any():
                    yy, xx = np.indices(hot.shape)
                    a = a.copy(); a[hot & (((xx + yy) // 4) % 2 == 0)] = (255, 0, 160)
                    img = Image.fromarray(a)
            self.draw_histogram(img, a[::4, ::4])
            self.t_proc = time.perf_counter() - t0
            put_latest(self.ready, img)

    def ui_loop(self):
        if not self.running:
            return
        try:
            img = self.ready.get_nowait()
        except queue.Empty:
            img = None
        if img is not None:
            self.tkimg = ImageTk.PhotoImage(img)
            self.view.configure(image=self.tkimg)
            self.fps_n += 1
            if time.time() - self.fps_t >= 1:
                self.fps, self.fps_n, self.fps_t = self.fps_n / (time.time() - self.fps_t), 0, time.time()
            lut_name = os.path.basename(self.luts[self.lut_i]) if self.lut else 'camera'
            self.info.configure(text=f'{self.fps:4.1f} fps | fetch {self.t_fetch*1000:4.1f} ms | process '
                                     f'{self.t_proc*1000:4.1f} ms | view: {lut_name} | {self.status}')
        self.root.after(2, self.ui_loop)

    def draw_histogram(self, img, a):
        w, h = 256, 90
        hist = np.histogram(a.mean(2), bins=w, range=(0, 255))[0].astype(float)
        hist = hist / max(hist.max(), 1) * (h - 4)
        d = ImageDraw.Draw(img, 'RGBA')
        x0, y0 = img.width - w - 12, img.height - h - 12
        d.rectangle([x0, y0, x0 + w, y0 + h], fill=(0, 0, 0, 140))
        for x, v in enumerate(hist):
            d.line([x0 + x, y0 + h - 2, x0 + x, y0 + h - 2 - v], fill=(230, 230, 230, 220))

    def af(self): self.cmds.put('af')
    def shoot(self): self.cmds.put('shutter')
    def toggle_zebras(self): self.zebras = not self.zebras

    def next_lut(self):
        if not self.luts:
            self.status = 'no LUT folder (--lut-dir)'; return
        self.lut_i += 1
        if self.lut_i >= len(self.luts):
            self.lut_i, self.lut = -1, None
        else:
            self.lut = load_cube(self.luts[self.lut_i])

    def quit(self):
        self.running = False
        self.root.after(300, self.root.destroy)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--lut-dir', help='folder of .cube files to preview on the Mac (Standard-based LUTs)')
    ap.add_argument('--size', default='1280x960', choices=['640x480', '960x720', '1280x960'], help='live view size')
    a = ap.parse_args()
    w, h = (int(x) for x in a.size.split('x'))
    Monitor(a.lut_dir, (w, h)).root.mainloop()


if __name__ == '__main__':
    main()
