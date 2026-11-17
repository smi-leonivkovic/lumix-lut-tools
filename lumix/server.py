"""lumix-server: local HTTP service that owns the camera and serves live view + settings (for the Swift app).

  python -m lumix.server [--port 8765] [--size 1280x960]

GET  /stream   MJPEG (multipart/x-mixed-replace), pushes every new frame immediately, never buffers
GET  /frame    latest JPEG
GET  /state    JSON: status, fps, timings, options (label/value lists the camera offers), current values (labels)
POST /set      JSON {"key": ..., "label": ...}   (labels as listed in /state options)
POST /af, /shutter, /undo, /size {"size": "1280x960"}
Binds to 127.0.0.1 only.
"""
import argparse
import json
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import liveview, settings
from .ptp import Camera


class CameraService:
    def __init__(self, size):
        self.size = size
        self.cond = threading.Condition()
        self.jpg, self.seq = None, 0
        self.cmds = queue.Queue()
        self.opts, self.current, self.original = {}, {}, {}
        self.status, self.fps, self.t_fetch = 'connecting', 0.0, 0.0
        self.running = True
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        while self.running:
            try:
                with Camera() as cam:
                    self.opts = settings.options(cam)
                    self.current = {k: settings.read(cam, k) for k in self.opts}
                    if not self.original:
                        self.original = dict(self.current)
                    liveview.set_size(cam, *self.size)
                    liveview.start(cam)
                    self.status = 'live'
                    n, t_fps, t_read = 0, time.time(), time.time()
                    while self.running:
                        self.handle_cmds(cam)
                        if time.time() - t_read > 2:
                            self.current = {k: settings.read(cam, k) for k in self.opts}; t_read = time.time()
                        t0 = time.perf_counter()
                        jpg, _ = liveview.frame(cam)
                        self.t_fetch = time.perf_counter() - t0
                        with self.cond:
                            self.jpg, self.seq = jpg, self.seq + 1
                            self.cond.notify_all()
                        n += 1
                        if time.time() - t_fps >= 1:
                            self.fps, n, t_fps = n / (time.time() - t_fps), 0, time.time()
                    liveview.stop(cam)
            except Exception as e:
                self.status = f'camera: {e}'[:160]
                time.sleep(2)

    def handle_cmds(self, cam):
        changed = False
        while not self.cmds.empty():
            cmd = self.cmds.get()
            try:
                if cmd == 'af':
                    rc = liveview.autofocus(cam); self.status = 'AF ok' if rc == 0x2001 else f'AF {rc:#x}'
                elif cmd == 'shutter':
                    rc = liveview.shutter(cam); self.status = 'shot taken' if rc == 0x2001 else f'shutter {rc:#x}'
                elif cmd == 'undo':
                    for k, v in self.original.items():
                        if v is not None and settings.read(cam, k) != v:
                            settings.write(cam, k, v)
                    self.status = 'all settings restored'
                elif cmd[0] == 'set':
                    settings.write(cam, cmd[1], cmd[2])
                    self.status = f'{cmd[1]} = {settings.label_of(self.opts, cmd[1], cmd[2])}'
                elif cmd[0] == 'size':
                    liveview.stop(cam); liveview.set_size(cam, *cmd[1]); liveview.start(cam)
                    self.size = cmd[1]; self.status = f'live view {cmd[1][0]}x{cmd[1][1]}'
                changed = True
            except Exception as e:
                self.status = f'not accepted: {e}'[:160]
        if changed:
            self.current = {k: settings.read(cam, k) for k in self.opts}

    def wait_frame(self, after_seq, timeout=2.0):
        with self.cond:
            self.cond.wait_for(lambda: self.seq != after_seq, timeout=timeout)
            return self.jpg, self.seq

    def state(self):
        return {'status': self.status, 'fps': round(self.fps, 1), 'fetch_ms': round(self.t_fetch * 1000, 1),
                'size': f'{self.size[0]}x{self.size[1]}',
                'options': {k: [l for l, _ in v] for k, v in self.opts.items()},
                'current': {k: settings.label_of(self.opts, k, v) for k, v in self.current.items()}}


def make_handler(svc):
    class H(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def log_message(self, *a):
            pass

        def send(self, code, body, ctype='application/json'):
            self.send_response(code)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == '/state':
                return self.send(200, json.dumps(svc.state()).encode())
            if self.path == '/frame':
                jpg, _ = svc.wait_frame(-1, 0)
                return self.send(200, jpg or b'', 'image/jpeg')
            if self.path == '/stream':
                self.send_response(200)
                self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Connection', 'close')
                self.end_headers()
                seq = -1
                try:
                    while svc.running:
                        jpg, seq = svc.wait_frame(seq)
                        if not jpg:
                            continue
                        self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n' % len(jpg))
                        self.wfile.write(jpg + b'\r\n')
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return
            self.send(404, b'{}')

        def do_POST(self):
            n = int(self.headers.get('Content-Length') or 0)
            body = json.loads(self.rfile.read(n) or b'{}') if n else {}
            if self.path in ('/af', '/shutter', '/undo'):
                svc.cmds.put(self.path[1:])
            elif self.path == '/set':
                key, label = body.get('key'), body.get('label')
                value = next((v for l, v in svc.opts.get(key, []) if l == label), None)
                if value is None:
                    return self.send(400, json.dumps({'error': f'unknown {key}/{label}'}).encode())
                svc.cmds.put(('set', key, value))
            elif self.path == '/size':
                w, h = (int(x) for x in body.get('size', '1280x960').split('x'))
                svc.cmds.put(('size', (w, h)))
            else:
                return self.send(404, b'{}')
            self.send(200, b'{"ok": true}')
    return H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--size', default='1280x960', choices=['640x480', '960x720', '1280x960'])
    a = ap.parse_args()
    svc = CameraService(tuple(int(x) for x in a.size.split('x')))
    srv = ThreadingHTTPServer(('127.0.0.1', a.port), make_handler(svc))
    srv.daemon_threads = True
    print(f'lumix-server on http://127.0.0.1:{a.port}', flush=True)
    try:
        srv.serve_forever()
    finally:
        svc.running = False


if __name__ == '__main__':
    main()
