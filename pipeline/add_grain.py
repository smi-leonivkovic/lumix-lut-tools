#!/usr/bin/env python3
"""Write a camera LUT with grain: Lab-style header (TITLE, #LUMIXPHOTOSTYLE, #GRAINEFFECT, #COLORNOISE, LUT_3D_SIZE),
no DOMAIN lines (format verified on a DC-S9 2.1).

  add_grain.py IN.cube OUT.cube LEVEL [--colornoise 0] [--style STD] [--title T]
"""
import argparse
ap = argparse.ArgumentParser()
ap.add_argument('inp'); ap.add_argument('out'); ap.add_argument('level', type=int)
ap.add_argument('--colornoise', type=int, default=0); ap.add_argument('--style', default='STD'); ap.add_argument('--title')
a = ap.parse_args()
lines = open(a.inp).read().split('\n')
data = [l for l in lines if l and (l[0].isdigit() or l[0] == '-')]
size = round(len(data) ** (1 / 3))
assert size ** 3 == len(data), 'not a 3D LUT'
title = a.title or next((l.split('"')[1] for l in lines if l.startswith('TITLE')), 'LUT')
hdr = [f'TITLE "{title}"', f'#LUMIXPHOTOSTYLE {a.style}', f'#GRAINEFFECT L{a.level}', f'#COLORNOISE L{a.colornoise}', f'LUT_3D_SIZE {size}']
open(a.out, 'w').write('\n'.join(hdr + data) + '\n')
