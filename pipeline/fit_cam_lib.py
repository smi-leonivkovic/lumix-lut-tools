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

