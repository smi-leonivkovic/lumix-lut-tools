# flat_check.py make DIR K  |  flat_check.py cmp DIR CUBE...
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, lutgrid as L
mode, d = sys.argv[1], sys.argv[2]
if mode == 'make':
    n = 33; rng = np.random.default_rng(1); ks = rng.choice(n**3, int(sys.argv[3]), replace=False)
    for k in ks:
        rgb = np.array([k % n, (k // n) % n, k // (n*n)]) / (n - 1)
        L.write_tiff16(f'{d}/flat_{k}.tif', np.round(np.broadcast_to(rgb, (256, 256, 3)) * 65535))
    json.dump([int(k) for k in ks], open(f'{d}/nodes.json', 'w'))
else:
    ks = json.load(open(f'{d}/nodes.json'))
    truth = np.array([L.read_tiff(f'{d}/out_{k}.tif')[96:160, 96:160].reshape(-1, 3).mean(0) for k in ks])
    for c in sys.argv[3:]:
        n, t = L.load_cube(c); e = np.abs(t[ks] - truth).max(1) * 255
        print(f'{os.path.basename(c):24s} vs flat fields: mean {e.mean():.2f}  max {e.max():.2f}')
