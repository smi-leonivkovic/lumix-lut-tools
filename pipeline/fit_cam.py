#!/usr/bin/env python3
"""Fit G: camera Standard JPEG -> LightCraft default render (from CAMDIR/*_cam.npy, *_lcd.npy), then
compose OUT(x) = F(G(x)) with the fitted preset LUT F.

  fit_cam.py CAMDIR F.cube OUT.cube [--title T] [--g-out G.cube]
"""
import sys, os, glob, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import lutgrid as L, fit_lut as FL

def load(files, per, rng):
    X, Y = [], []
    for f in files:
        a = np.load(f); b = np.load(f.replace('_cam.npy', '_lcd.npy'))
        ok = (a.max(1) < 0.99) & (b.max(1) < 0.99)
        a, b = a[ok], b[ok]
        k = rng.choice(len(a), min(per, len(a)), replace=False)
        X.append(a[k]); Y.append(b[k])
    return np.concatenate(X), np.concatenate(Y)

def err(table, n, X, Y):
    p = L.apply_lut(table, n, X[None])[0]
    return (np.abs(p - Y).max(1) * 255).mean()

ap = argparse.ArgumentParser()
ap.add_argument('camdir'); ap.add_argument('F'); ap.add_argument('out')
ap.add_argument('--title', default='LightCraft'); ap.add_argument('--g-out')
a = ap.parse_args()
rng = np.random.default_rng(0)
files = sorted(glob.glob(f'{a.camdir}/*_cam.npy'))
n = 33; idx = np.arange(n ** 3)
ident = np.stack([idx % n, (idx // n) % n, idx // (n * n)], 1) / (n - 1)
D = FL.second_diff(n)
# leave-one-out over images for lam/mu choice
grid = [(lam, mu) for lam in (1, 10, 100) for mu in (0.01, 0.1, 1)]
scores = {g: [] for g in grid}; base = []
for i, f in enumerate(files):
    tr = files[:i] + files[i + 1:]
    X, Y = load(tr, 40000, rng); Xt, Yt = load([f], 40000, rng)
    base.append(err(ident, n, Xt, Yt))
    for lam, mu in grid:
        t = FL.solve(X, Y, ident, n, lam, mu, D)
        scores[(lam, mu)].append(err(t, n, Xt, Yt))
print(f'no correction (identity): mean {np.mean(base):.2f}')
for g in grid:
    print(f'lam {g[0]:<4} mu {g[1]:<5} leave-one-out: mean {np.mean(scores[g]):.2f}')
best = min(grid, key=lambda g: np.mean(scores[g]))
X, Y = load(files, 40000, rng)
G = FL.solve(X, Y, ident, n, best[0], best[1], D)
if a.g_out:
    L.write_cube(a.g_out, G, n, 'S9 Standard to LightCraft default', 'STD')
nF, F = L.load_cube(a.F)
out = np.clip(L.apply_lut(F, nF, G[None])[0], 0, 1)
L.write_cube(a.out, out, n, a.title, 'STD')
print(f'best lam {best[0]} mu {best[1]}; wrote {a.out}')
