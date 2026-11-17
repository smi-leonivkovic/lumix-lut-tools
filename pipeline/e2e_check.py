#!/usr/bin/env python3
"""End-to-end: camera JPEG -> (G fitted without this photo) -> F  vs  preset on the RW2.

  e2e_check.py CAMDIR F.cube PRESET_SETTINGS.json OUTDIR NAME...   (NAME = P1059861; RW2/JPG looked up in JPGDIRS env)
"""
import sys, os, glob, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageOps
import lutgrid as L, fit_lut as FL, fit_cam_lib as FC

camdir, Fp, settings, outdir = sys.argv[1:5]
names = sys.argv[5:]
dirs = os.environ['JPGDIRS'].split(':')
T = os.path.dirname(os.path.abspath(__file__))
n = 33; nF, F = L.load_cube(Fp)
idx = np.arange(n ** 3); ident = np.stack([idx % n, (idx // n) % n, idx // (n * n)], 1) / (n - 1)
D = FL.second_diff(n); rng = np.random.default_rng(0)
for name in names:
    src = next(d for d in dirs if os.path.exists(f'{d}/{name}.RW2'))
    files = [f for f in sorted(glob.glob(f'{camdir}/*_cam.npy')) if not os.path.basename(f).startswith(name)]
    X, Y = FC.load(files, 40000, rng)
    G = FL.solve(X, Y, ident, n, 1.0, 0.1, D)
    final = np.clip(L.apply_lut(F, nF, G[None])[0], 0, 1)
    ref = f'{outdir}/{name}_rawpreset.tif'
    if not os.path.exists(ref):
        subprocess.run([f'{T}/render.sh', f'{src}/{name}.RW2', ref, '--settings', settings, '--size', '1600',
                        '--library', os.environ.get('LIGHTCRAFT_LIBRARY', os.path.expanduser('~/Pictures/LightCraft Library'))], check=True, capture_output=True)
    r = L.read_tiff(ref)
    j = np.asarray(ImageOps.exif_transpose(Image.open(f'{src}/{name}.JPG')).convert('RGB'), np.float32) / 255
    j = np.stack([np.asarray(Image.fromarray(j[..., c], 'F').resize((r.shape[1], r.shape[0]), Image.BOX)) for c in range(3)], 2)
    out = L.apply_lut(final, n, j.astype(np.float64))
    e = np.abs(out - r).max(2) * 255
    print(f'{name}: camera JPEG + LUT vs preset on RAW: mean {e.mean():.2f}  median {np.median(e):.2f}  p95 {np.percentile(e, 95):.2f}')
    to8 = lambda x: (np.clip(x, 0, 1) * 255 + .5).astype(np.uint8)
    Image.fromarray(np.concatenate([to8(j), to8(r), to8(out)], 1)).save(f'{outdir}/{name}_e2e.jpg', quality=88)
