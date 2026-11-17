#!/usr/bin/env python3
"""Overview sheet: one row per look (camera Standard + LUT), same photos in every row.
  overview.py OUT.jpg LOOK... (uses data/reference/*_std.tif as the Standard stand-in)"""
import glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import lutgrid as L
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out, looks = sys.argv[1], sys.argv[2:]
stds = [L.read_tiff(f) for f in sorted(glob.glob(f'{R}/data/reference/*_std.tif'))]
H = 260
to8 = lambda x: (np.clip(x, 0, 1) * 255 + .5).astype(np.uint8)
def tile(a): im = Image.fromarray(to8(a)); return im.resize((round(im.width * H / im.height), H))
rows = [('Standard (no LUT)', [tile(s) for s in stds])]
for lk in looks:
    n, t = L.load_cube(f'{R}/luts/LC_{lk}.cube')
    rows.append((lk, [tile(np.clip(L.apply_lut(t, n, s.astype(np.float64)), 0, 1)) for s in stds]))
lab, gap = 230, 6
W = lab + sum(p.width for p in rows[0][1]) + gap * len(rows[0][1])
sheet = Image.new('RGB', (W, len(rows) * (H + gap)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
try: font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 26)
except OSError: font = ImageFont.load_default()
for k, (name, tiles) in enumerate(rows):
    y = k * (H + gap); d.text((12, y + H // 2 - 14), name, fill=(235, 235, 235), font=font); x = lab
    for p in tiles: sheet.paste(p, (x, y)); x += p.width + gap
sheet.save(out, quality=85); print('wrote', out, sheet.size)
