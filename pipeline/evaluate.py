#!/usr/bin/env python3
"""End-to-end check on tethered frames: does camera-JPEG + our LUT look like the preset on the RAW?

  evaluate.py TETHERDIR NAME LUT.cube [LUT2.cube ...] [--cam-style 49]

For every Standard frame (…_s00) renders the RAW with settings/NAME_e2e.json (preset, spatial effects off,
lens correction on so the framing matches the camera JPEG), applies each LUT to the camera JPEG and reports the
error. If frames of --cam-style exist (the camera's own LUT slot), they are scored against their own RAW too.
Writes TETHERDIR/eval_NAME/sheet.jpg: rows = frames, columns = camera LUT | each LUT | target.
"""
import argparse, glob, os, subprocess, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageOps
import lutgrid as L

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resize(img, w, h, mode=Image.BOX):
    return np.stack([np.asarray(Image.fromarray(img[..., c].astype(np.float32), 'F').resize((w, h), mode)) for c in range(3)], 2)


def jpeg(p):
    return np.asarray(ImageOps.exif_transpose(Image.open(p)).convert('RGB'), np.float32) / 255


def render(rw2, out, settings):
    if not os.path.exists(out):
        subprocess.run([f'{R}/pipeline/render.sh', rw2, out, '--settings', settings, '--size', '768',
                        '--library', os.environ.get('LIGHTCRAFT_LIBRARY', os.path.expanduser('~/Pictures/LightCraft Library'))], check=True, capture_output=True)
    return L.read_tiff(out)


def align(target, img):
    """best small scale/shift of target onto img (both full-res float), return cropped pair at 512 wide"""
    W = 512; H = round(W * target.shape[0] / target.shape[1])
    t = resize(target, W, H); j = resize(img, W, H)
    lum = lambda x: x @ np.array([.2126, .7152, .0722])
    m = 24; best = None
    for s in [0.98, 0.99, 1.0, 1.01, 1.02]:
        ww, hh = round(W * s), round(H * s)
        sc = resize(t, ww, hh, Image.BILINEAR)
        for dy in range(-6, 7, 2):
            for dx in range(-6, 7, 2):
                y0 = (hh - H) // 2 + dy; x0 = (ww - W) // 2 + dx
                if y0 + m < 0 or x0 + m < 0 or y0 + H - m > hh or x0 + W - m > ww:
                    continue
                a = sc[y0 + m:y0 + H - m, x0 + m:x0 + W - m]; b = j[m:H - m, m:W - m]
                c = np.corrcoef(lum(a).ravel(), lum(b).ravel())[0, 1]
                if best is None or c > best[0]:
                    best = (c, a, b)
    return best[1], best[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tether'); ap.add_argument('name'); ap.add_argument('luts', nargs='+')
    ap.add_argument('--cam-style', default='49')
    a = ap.parse_args()
    settings = f'{R}/settings/{a.name}_e2e.json'
    out = os.path.join(a.tether, f'eval_{a.name}'); os.makedirs(out, exist_ok=True)
    luts = [(os.path.basename(p), *L.load_cube(p)) for p in a.luts]
    err = lambda x, y: np.abs(x - y).max(2) * 255
    scores = {k: [] for k in ['camera'] + [l[0] for l in luts]}
    rows = []
    for jp in sorted(glob.glob(f'{a.tether}/*_s00.JPG')):
        b = os.path.basename(jp)[:-4]
        tgt = render(jp[:-4] + '.RW2', f'{out}/{b}_target.tif', settings)
        t, j = align(tgt, jpeg(jp))
        row = []
        cj = jp.replace('_s00.', f'_s{a.cam_style}.')
        if os.path.exists(cj):
            ct = render(cj[:-4] + '.RW2', f'{out}/{b}_camtarget.tif', settings)
            t2, c2 = align(ct, jpeg(cj))
            scores['camera'].append(err(c2, t2).mean()); row.append(c2)
        for name, n, tab in luts:
            o = np.clip(L.apply_lut(tab, n, j.astype(np.float64)), 0, 1)
            scores[name].append(err(o, t).mean()); row.append(o)
        row.append(t); rows.append(row)
    res = {k: (float(np.mean(v)), float(np.median(v))) for k, v in scores.items() if v}
    for k, (m, md) in res.items():
        print(f'{k:32s} mean {m:5.2f}  median {md:5.2f}  (/255, max channel, {len(scores[k])} frames)')
    json.dump(res, open(f'{out}/scores.json', 'w'), indent=1)
    to8 = lambda x: (np.clip(x, 0, 1) * 255 + .5).astype(np.uint8)
    pick = rows[::max(1, len(rows) // 6)][:6]
    w = min(r[0].shape[1] for r in pick); h = min(r[0].shape[0] for r in pick)
    sheet = np.concatenate([np.concatenate([to8(c[:h, :w]) for c in r], 1) for r in pick], 0)
    Image.fromarray(sheet).save(f'{out}/sheet.jpg', quality=85)
    print('sheet:', f'{out}/sheet.jpg (columns: camera LUT | ' + ' | '.join(l[0] for l in luts) + ' | target)')


if __name__ == '__main__':
    main()
