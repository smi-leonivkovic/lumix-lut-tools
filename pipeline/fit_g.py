#!/usr/bin/env python3
"""Fit G: camera Standard JPEG -> LightCraft default render, from aligned pairs (X_cam.npy / X_lcd.npy).

  fit_g.py PAIRDIR G.cube [--lam 0.3,1,3,10] [--mu 0.1]

Validation holds out one white-balance group at a time (file prefix up to the first '_'), so a frame is never
scored by a model that saw the same WB setting.
"""
import argparse, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import lutgrid as L, fit_lut as FL, fit_cam_lib as FC

ap = argparse.ArgumentParser()
ap.add_argument('pairdir'); ap.add_argument('out')
ap.add_argument('--key', type=int, default=0, help='field of the file name (split on _) that defines hold-out groups')
ap.add_argument('--lam', default='0.3,1,3,10'); ap.add_argument('--mu', type=float, default=0.1)
ap.add_argument('--per', type=int, default=40000)
a = ap.parse_args()
rng = np.random.default_rng(0)
files = sorted(glob.glob(f'{a.pairdir}/*_cam.npy'))
groups = sorted({os.path.basename(f).split('_')[a.key] for f in files})
n = 33; idx = np.arange(n ** 3)
ident = np.stack([idx % n, (idx // n) % n, idx // (n * n)], 1) / (n - 1)
D = FL.second_diff(n)
err = lambda t, X, Y: (np.abs(L.apply_lut(t, n, X[None])[0] - Y).max(1) * 255).mean()
lams = [float(v) for v in a.lam.split(',')]
res = {l: [] for l in lams}; base = []
for g in groups:
    tr = [f for f in files if os.path.basename(f).split('_')[a.key] != g]
    te = [f for f in files if os.path.basename(f).split('_')[a.key] == g]
    X, Y = FC.load(tr, a.per, rng); Xt, Yt = FC.load(te, a.per, rng)
    base.append(err(ident, Xt, Yt))
    for l in lams:
        res[l].append(err(FL.solve(X, Y, ident, n, l, a.mu, D), Xt, Yt))
print(f'{len(files)} frames, {len(groups)} WB groups')
print(f'no correction: mean {np.mean(base):.2f}/255')
for l in lams:
    print(f'lam {l:<5} hold-out-WB: mean {np.mean(res[l]):.2f}   per group ' + ' '.join(f'{v:.2f}' for v in res[l]))
best = min(lams, key=lambda l: np.mean(res[l]))
X, Y = FC.load(files, a.per, rng)
L.write_cube(a.out, FL.solve(X, Y, ident, n, best, a.mu, D), n, 'S9 Standard to LightCraft default', 'STD')
print(f'best lam {best}; wrote {a.out}')
