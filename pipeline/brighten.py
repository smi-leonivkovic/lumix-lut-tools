#!/usr/bin/env python3
"""Bright variant of a camera LUT: lift midtones before the look, with a soft shoulder so highlights don't clip.

  brighten.py IN.cube OUT.cube [--amount 0.6] [--gamma 1.6] [--title T]

Pre-curve on luminance (hue/saturation kept): f(L) = L + amount * ((1 - (1-L)^gamma) - L).
amount 0.6, gamma 1.6: mid grey 0.50 -> 0.60 (about +0.4 stop), slope at white 0.4 (soft roll-off), f(1) = 1.
Expose so the zebras are clean; the LUT supplies the brightness.
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import lutgrid as L

ap = argparse.ArgumentParser()
ap.add_argument('inp'); ap.add_argument('out')
ap.add_argument('--amount', type=float, default=0.6); ap.add_argument('--gamma', type=float, default=1.6)
ap.add_argument('--title')
a = ap.parse_args()
n, lut = L.load_cube(a.inp)
idx = np.arange(n ** 3)
x = np.stack([idx % n, (idx // n) % n, idx // (n * n)], 1) / (n - 1)
lum = x @ np.array([.2126, .7152, .0722])
f = lum + a.amount * ((1 - (1 - lum) ** a.gamma) - lum)
scale = np.where(lum > 1e-6, f / np.maximum(lum, 1e-6), 1.0)
pre = x * scale[:, None]
over = pre.max(1)  # keep saturated colours in gamut: blend toward the lifted grey instead of clipping
k = np.where(over > 1, (1 - f) / np.maximum(over - f, 1e-6), 1.0)
pre = f[:, None] + (pre - f[:, None]) * k[:, None]
out = np.clip(L.apply_lut(lut, n, pre[None])[0], 0, 1)
L.write_cube(a.out, out, n, a.title or os.path.splitext(os.path.basename(a.out))[0], 'STD')
g = np.linspace(0, 1, 6); ramp = L.apply_lut(out, n, np.stack([g, g, g], 1)[None])[0]
base = L.apply_lut(lut, n, np.stack([g, g, g], 1)[None])[0]
for gi, b, r in zip(g, base, ramp):
    print(f'in {gi*255:5.0f}: original {b.mean()*255:5.0f} -> bright {r.mean()*255:5.0f}')
print('wrote', a.out)
