#!/usr/bin/env python3
"""Fit a 33^3 LUT mapping default renders -> preset renders of the same raws.

  fit_lut.py PAIRDIR PRIOR.cube OUT.cube [--title T] [--lam L,...] [--mu M] [--holdout K]

Least squares on trilinear weights + lam * |second differences|^2 (smooth) + mu * |L - prior|^2
(only matters where photos have no colours). Picks lam on held-out images, refits on all.
"""
import sys, os, glob, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as sla
import lutgrid as L

def trilinear_matrix(x, n):
    g = np.clip(x, 0, 1) * (n - 1)
    i = np.minimum(np.floor(g).astype(np.int64), n - 2); f = g - i
    rows, cols, vals = [], [], []
    m = len(x); r = np.arange(m)
    for dr in (0, 1):
        for dg in (0, 1):
            for db in (0, 1):
                w = (f[:, 0] if dr else 1 - f[:, 0]) * (f[:, 1] if dg else 1 - f[:, 1]) * (f[:, 2] if db else 1 - f[:, 2])
                idx = (i[:, 0] + dr) + (i[:, 1] + dg) * n + (i[:, 2] + db) * n * n
                rows.append(r); cols.append(idx); vals.append(w)
    return sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(m, n ** 3))

def second_diff(n):
    N = n ** 3; mats = []
    idx = np.arange(N).reshape(n, n, n)  # [b][g][r]
    for ax in range(3):
        a = np.moveaxis(idx, ax, 0)
        c0, c1, c2 = a[:-2].ravel(), a[1:-1].ravel(), a[2:].ravel()
        k = len(c0); r = np.arange(k)
        mats.append(sp.csr_matrix((np.concatenate([np.ones(k), -2 * np.ones(k), np.ones(k)]),
                                   (np.concatenate([r, r, r]), np.concatenate([c0, c1, c2]))), shape=(k, N)))
    return sp.vstack(mats).tocsr()

BALANCE = 0  # >0: cap samples per colour bin (16^3 bins) so rare colours (near-whites, saturated) weigh as much as common ones


def load_pairs(files, per_img, rng):
    X, Y = [], []
    pool = per_img * 4 if BALANCE else per_img
    for f in files:
        a = L.read_tiff(f).reshape(-1, 3); b = L.read_tiff(f.replace('_def.tif', '_pre.tif')).reshape(-1, 3)
        if a.shape != b.shape: continue
        ok = (a.max(1) < 0.995)  # drop clipped input
        a, b = a[ok], b[ok]
        k = rng.choice(len(a), min(pool, len(a)), replace=False)
        X.append(a[k]); Y.append(b[k])
    X, Y = np.concatenate(X), np.concatenate(Y)
    if BALANCE:
        q = np.minimum((X * 16).astype(int), 15)
        bins = q[:, 0] * 256 + q[:, 1] * 16 + q[:, 2]
        order = rng.permutation(len(X)); bins_o = bins[order]
        srt = np.argsort(bins_o, kind='stable'); b_sorted = bins_o[srt]
        first = np.searchsorted(b_sorted, b_sorted, side='left')
        rank = np.arange(len(b_sorted)) - first
        keep = order[srt[rank < BALANCE]]
        X, Y = X[keep], Y[keep]
    return X, Y

def solve(X, Y, prior, n, lam, mu, D):
    A = trilinear_matrix(X, n)
    scale = (n ** 3) / len(X)  # data term ~ O(1) per node on average
    M = (A.T @ A) * scale + lam * (D.T @ D) + mu * sp.identity(n ** 3)
    M = M.tocsc(); lu = sla.splu(M)
    out = np.zeros((n ** 3, 3))
    for c in range(3):
        out[:, c] = lu.solve((A.T @ Y[:, c]) * scale + mu * prior[:, c])
    return np.clip(out, 0, 1)

def score(table, n, files):
    errs = []
    for f in files:
        a = L.read_tiff(f); b = L.read_tiff(f.replace('_def.tif', '_pre.tif'))
        if a.shape != b.shape: continue
        errs.append(np.abs(L.apply_lut(table, n, a) - b).max(2).ravel() * 255)
    e = np.concatenate(errs)
    return e.mean(), np.percentile(e, 95)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pairdir'); ap.add_argument('prior'); ap.add_argument('out')
    ap.add_argument('--title', default='LightCraft'); ap.add_argument('--lam', default='0.03,0.3,3,30')
    ap.add_argument('--mu', type=float, default=1e-3); ap.add_argument('--holdout', type=int, default=20)
    ap.add_argument('--per-img', type=int, default=30000)
    ap.add_argument('--balance', type=int, default=0, help='max samples per 16^3 colour bin (0 = off)')
    a = ap.parse_args()
    global BALANCE; BALANCE = a.balance
    rng = np.random.default_rng(0)
    files = sorted(glob.glob(os.path.join(a.pairdir, '*_def.tif')))
    rng.shuffle(files)
    test, train = files[:a.holdout], files[a.holdout:]
    n, prior = L.load_cube(a.prior)
    D = second_diff(n)
    X, Y = load_pairs(train, a.per_img, rng)
    print(f'{len(train)} train / {len(test)} test images, {len(X)} samples')
    pm, p95 = score(prior, n, test); print(f'prior (grid LUT)   held-out: mean {pm:.2f}  p95 {p95:.2f}')
    best = None
    for lam in [float(v) for v in a.lam.split(',')]:
        t = solve(X, Y, prior, n, lam, a.mu, D)
        m, q = score(t, n, test); print(f'lam {lam:<6} held-out: mean {m:.2f}  p95 {q:.2f}')
        if best is None or m < best[1]: best = (lam, m)
    Xa, Ya = load_pairs(files, a.per_img, rng)
    t = solve(Xa, Ya, prior, n, best[0], a.mu, D)
    L.write_cube(a.out, t, n, a.title, 'STD')
    print(f'wrote {a.out} (lam {best[0]}, all {len(files)} images)')

if __name__ == '__main__':
    main()
