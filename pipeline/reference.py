#!/usr/bin/env python3
"""Reference image for a look on real photos: Standard | Standard + LUT | preset on RAW, one row per photo.

  reference.py NAME OUT.jpg RW2...

Standard stands in as the LightCraft default render (camera Standard is ~4/255 from it, see docs/LOG.md).
"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import lutgrid as L

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name, out, raws = sys.argv[1], sys.argv[2], sys.argv[3:]
tmp = os.path.join(R, 'data', 'reference'); os.makedirs(tmp, exist_ok=True)
n, lut = L.load_cube(os.environ.get('REF_LUT', f'{R}/luts/LC_{name}.cube'))


def render(rw2, settings, tag):
    o = os.path.join(tmp, os.path.basename(rw2)[:-4] + f'_{tag}.tif')
    if not os.path.exists(o):
        subprocess.run([f'{R}/pipeline/render.sh', rw2, o, '--settings', settings, '--size', '900',
                        '--library', os.environ.get('LIGHTCRAFT_LIBRARY', os.path.expanduser('~/Pictures/LightCraft Library'))], check=True, capture_output=True)
    return L.read_tiff(o)


to8 = lambda x: (np.clip(x, 0, 1) * 255 + .5).astype(np.uint8)
rows = []
for f in raws:
    std = render(f, f'{R}/settings/default_nospatial.json', 'std')
    tgt = render(f, f'{R}/settings/{name}_nospatial.json', name)
    lc = np.clip(L.apply_lut(lut, n, std.astype(np.float64)), 0, 1)
    e = np.abs(lc - tgt).max(2).mean() * 255
    print(f'{os.path.basename(f)}: LUT vs preset-on-RAW {e:.2f}/255')
    rows.append([to8(std), to8(lc), to8(tgt)])
h = min(r[0].shape[0] for r in rows)
rows = [[Image.fromarray(p).resize((round(p.shape[1] * h / p.shape[0]), h)) for p in r] for r in rows]
gap, top = 8, 40
W = max(sum(p.width for p in r) + gap * 2 for r in rows)
sheet = Image.new('RGB', (W, top + len(rows) * (h + gap)), (20, 20, 20))
d = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 24)
except OSError:
    font = ImageFont.load_default()
x = 0
for i, lab in enumerate(['Standard (camera, no LUT)', os.environ.get('REF_LABEL', f'Standard + LC {name} LUT'), f'{name} on RAW (target)']):
    d.text((x + 10, 8), lab, fill=(235, 235, 235), font=font); x += rows[0][i].width + gap
for k, r in enumerate(rows):
    x = 0
    for p in r:
        sheet.paste(p, (x, top + k * (h + gap))); x += p.width + gap
sheet.save(out, quality=88)
print('wrote', out)
