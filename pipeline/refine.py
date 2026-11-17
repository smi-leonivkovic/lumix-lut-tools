#!/usr/bin/env python3
"""Iteration step: refine a look LUT directly on camera-JPEG -> preset-on-RAW pairs from tethered frames.

  refine.py TETHERDIR NAME PRIOR.cube OUT.cube [--lam 1,3,10] [--mu 0.3,1,3]

Uses the target renders evaluate.py left in TETHERDIR/eval_NAME. The prior (F∘G) keeps colours the room never
showed; hold-one-WB-group-out picks lam/mu. Prints held-out error for prior vs refined.
"""
import argparse, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import lutgrid as L, fit_lut as FL
from evaluate import align, jpeg

ap = argparse.ArgumentParser()
ap.add_argument('tether'); ap.add_argument('name'); ap.add_argument('prior'); ap.add_argument('out')
ap.add_argument('--key', type=int, default=0, help='field of the file name (split on _) that defines hold-out groups')
ap.add_argument('--lam', default='1,3,10'); ap.add_argument('--mu', default='0.3,1,3')
a = ap.parse_args()
ev = os.path.join(a.tether, f'eval_{a.name}')
pairs = {}
for jp in sorted(glob.glob(f'{a.tether}/*_s00.JPG')):
    b = os.path.basename(jp)[:-4]
    t, j = align(L.read_tiff(f'{ev}/{b}_target.tif'), jpeg(jp))
    X, Y = j.reshape(-1, 3), t.reshape(-1, 3)
    ok = (X.max(1) < 0.99) & (Y.max(1) < 0.99)
    pairs[b] = (X[ok].astype(np.float64), Y[ok].astype(np.float64))
groups = sorted({b.split('_')[a.key] for b in pairs})
n, prior = L.load_cube(a.prior)
D = FL.second_diff(n)
err = lambda tab, X, Y: (np.abs(L.apply_lut(tab, n, X[None])[0] - Y).max(1) * 255).mean()
cat = lambda keys: tuple(np.concatenate([pairs[k][i] for k in keys]) for i in (0, 1))
grid = [(float(l), float(m)) for l in a.lam.split(',') for m in a.mu.split(',')]
res = {g: [] for g in grid}; base = []
for g in groups:
    tr = [k for k in pairs if k.split('_')[a.key] != g]; te = [k for k in pairs if k.split('_')[a.key] == g]
    X, Y = cat(tr); Xt, Yt = cat(te)
    base.append(err(prior, Xt, Yt))
    for lam, mu in grid:
        res[(lam, mu)].append(err(FL.solve(X, Y, prior, n, lam, mu, D), Xt, Yt))
print(f'prior {os.path.basename(a.prior)}: held-out-WB mean {np.mean(base):.2f}')
for g in grid:
    print(f'lam {g[0]:<4} mu {g[1]:<4}: held-out-WB mean {np.mean(res[g]):.2f}')
best = min(grid, key=lambda g: np.mean(res[g]))
X, Y = cat(list(pairs))
L.write_cube(a.out, FL.solve(X, Y, prior, n, best[0], best[1], D), n, a.name, 'STD')
print(f'best lam {best[0]} mu {best[1]}; wrote {a.out}')
