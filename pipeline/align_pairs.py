# align_pairs.py CAMDIR JPGDIR...
# For each CAMDIR/X_lc.tif (LightCraft default render of X.RW2) find camera X.JPG, bring both to 512 px wide,
# search a small scale/shift for best alignment, save X_lcd.npy / X_cam.npy pixel pairs.
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, lutgrid as L
from PIL import Image, ImageOps

def resize(img, w, h, mode=Image.BOX):
    return np.stack([np.asarray(Image.fromarray(img[..., c].astype(np.float32), 'F').resize((w, h), mode)) for c in range(3)], 2)

lum = lambda x: x @ np.array([.2126, .7152, .0722])
C = sys.argv[1]
for f in sorted(glob.glob(f'{C}/*_lc.tif')):
    b = os.path.basename(f)[:-7]
    jp = next((p for d in sys.argv[2:] for p in [f'{d}/{b}.JPG'] if os.path.exists(p)), None)
    if jp is None:
        print(b, 'no jpeg'); continue
    lc = L.read_tiff(f); ja = np.asarray(ImageOps.exif_transpose(Image.open(jp)).convert('RGB'), np.float32) / 255
    if (ja.shape[0] > ja.shape[1]) != (lc.shape[0] > lc.shape[1]):
        print(b, 'orientation mismatch', ja.shape, lc.shape); continue
    W = 512; H = round(W * lc.shape[0] / lc.shape[1])
    lci = resize(lc, W, H); ji = resize(ja, W, H)
    m = 24; best = None
    for s in [0.97, 0.98, 0.99, 1.0, 1.01, 1.02, 1.03]:
        ww, hh = round(W * s), round(H * s)
        sc = resize(lci, ww, hh, Image.BILINEAR)
        for dy in range(-8, 9, 2):
            for dx in range(-8, 9, 2):
                y0 = (hh - H) // 2 + dy; x0 = (ww - W) // 2 + dx
                ys, ye = y0 + m, y0 + H - m; xs, xe = x0 + m, x0 + W - m
                if ys < 0 or xs < 0 or ye > hh or xe > ww:
                    continue
                a = sc[ys:ye, xs:xe]; bj = ji[m:H - m, m:W - m]
                e = np.corrcoef(lum(a).ravel(), lum(bj).ravel())[0, 1]
                if best is None or e > best[0]:
                    best = (e, s, dx, dy, a, bj)
    e, s, dx, dy, a, bj = best
    print(f'{b}: corr {e:.4f} scale {s} shift {dx},{dy}')
    np.save(f'{C}/{b}_lcd.npy', a.reshape(-1, 3)); np.save(f'{C}/{b}_cam.npy', bj.reshape(-1, 3))
