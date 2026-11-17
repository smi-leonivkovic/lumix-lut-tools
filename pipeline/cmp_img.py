import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, lutgrid as L
from PIL import Image
a = L.read_tiff(sys.argv[1]); b = L.read_tiff(sys.argv[2])
d = np.abs(a - b).max(2) * 255
print(f'{os.path.basename(sys.argv[1])}: LUT vs LightCraft  mean {d.mean():.2f}  p95 {np.percentile(d,95):.2f}  p99 {np.percentile(d,99):.2f}  (8-bit units)')
if len(sys.argv) > 3:
    to8 = lambda x: (np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(np.concatenate([to8(b), to8(a)], 1)).save(sys.argv[3], quality=90)
