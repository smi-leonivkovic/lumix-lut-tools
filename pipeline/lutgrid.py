#!/usr/bin/env python3
"""Build a 3D LUT from a LightCraft render of a colour grid.

  lutgrid.py make  OUT.tif [--n 33] [--patch 8] [--seed S]   -> grid image + OUT.tif.json layout
  lutgrid.py read  RENDER.tif LAYOUT.json OUT.cube [--title T] [--style STD]
  lutgrid.py diff  A.cube B.cube
  lutgrid.py apply LUT.cube IN.tif OUT.tif        (tetrahedral, for checks)
"""
import json, struct, sys, argparse
import numpy as np

# ---------- minimal TIFF I/O (uncompressed, 8/16-bit, chunky RGB[A]) ----------

def write_tiff16(path, img):
    h, w, _ = img.shape
    data = img.astype('<u2').tobytes()
    entries = []
    def e(tag, typ, count, val): entries.append((tag, typ, count, val))
    hdr = 8
    n_entries = 11
    ifd_size = 2 + n_entries * 12 + 4
    bps_off = hdr + ifd_size
    data_off = bps_off + 6
    e(256, 4, 1, w); e(257, 4, 1, h); e(258, 3, 3, bps_off); e(259, 3, 1, 1)
    e(262, 3, 1, 2); e(273, 4, 1, data_off); e(277, 3, 1, 3); e(278, 4, 1, h)
    e(279, 4, 1, len(data)); e(284, 3, 1, 1); e(339, 3, 1, 1)
    out = bytearray(b'II*\x00' + struct.pack('<I', hdr))
    out += struct.pack('<H', n_entries)
    for tag, typ, count, val in entries:
        if typ == 3 and count == 1:
            out += struct.pack('<HHIHH', tag, typ, count, val, 0)
        else:
            out += struct.pack('<HHII', tag, typ, count, val)
    out += struct.pack('<I', 0)
    out += struct.pack('<HHH', 16, 16, 16)
    out += data
    open(path, 'wb').write(out)


def read_tiff(path):
    b = open(path, 'rb').read()
    bo = '<' if b[:2] == b'II' else '>'
    (off,) = struct.unpack(bo + 'I', b[4:8])
    (n,) = struct.unpack(bo + 'H', b[off:off + 2])
    tags = {}
    sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 7: 1, 16: 8}
    fmt = {1: 'B', 2: 'B', 3: 'H', 4: 'I', 7: 'B', 16: 'Q'}
    for i in range(n):
        p = off + 2 + i * 12
        tag, typ, count = struct.unpack(bo + 'HHI', b[p:p + 8])
        sz = sizes.get(typ, 1) * count
        vp = p + 8 if sz <= 4 else struct.unpack(bo + 'I', b[p + 8:p + 12])[0]
        if typ in fmt:
            vals = struct.unpack(bo + fmt[typ] * count, b[vp:vp + sizes[typ] * count])
        else:
            vals = None
        tags[tag] = vals
    w, h = tags[256][0], tags[257][0]
    bps = tags[258][0]
    spp = tags.get(277, (1,))[0]
    comp = tags.get(259, (1,))[0]
    if comp != 1:
        raise SystemExit(f'{path}: compressed TIFF ({comp}); export with tiffCompression=none')
    if tags.get(284, (1,))[0] != 1:
        raise SystemExit('planar TIFF not supported')
    offs, cnts = tags[273], tags[279]
    raw = b''.join(b[o:o + c] for o, c in zip(offs, cnts))
    dt = np.dtype(bo + ('u2' if bps == 16 else 'u1'))
    a = np.frombuffer(raw, dtype=dt)[: w * h * spp].reshape(h, w, spp)
    return a[..., :3].astype(np.float64) / (65535.0 if bps == 16 else 255.0)

# ---------- grid ----------

def make(args):
    """Write the nodes as patches over several images (OUTDIR/grid_###.tif) + OUTDIR/layout.json."""
    import os
    n, P, cols = args.n, args.patch, args.cols
    per = cols * cols
    idx = np.arange(n ** 3)
    order = idx.copy()
    rgb = np.stack([idx % n, (idx // n) % n, idx // (n * n)], 1) / (n - 1)
    if args.seed is not None:
        np.random.default_rng(args.seed).shuffle(order)
    if args.sort_lum:
        lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
        order = np.argsort(lin @ np.array([0.2126, 0.7152, 0.0722]), kind='stable')
    os.makedirs(args.out, exist_ok=True)
    pos = np.empty(len(order), np.int64); pos[order] = np.arange(len(order))
    nimg = -(-len(order) // per)
    for im in range(nimg):
        img = np.full((cols * P, cols * P, 3), 0.5)
        for slot in range(per):
            g = im * per + slot
            if g >= len(order): break
            y, x = divmod(slot, cols)
            img[y * P:(y + 1) * P, x * P:(x + 1) * P] = rgb[order[g]]
        write_tiff16(os.path.join(args.out, f'grid_{im:03d}.tif'), np.round(img * 65535))
    json.dump({'n': n, 'patch': P, 'cols': cols, 'pos': pos.tolist(), 'images': nimg}, open(os.path.join(args.out, 'layout.json'), 'w'))
    print(f'{args.out}: {nimg} images of {cols*P}px, {n}^3 nodes, patch {P}px')


def read(args):
    """read RENDERDIR (out_###.tif) LAYOUT.json OUT.cube"""
    import os
    L = json.load(open(args.layout))
    n, P, cols = L['n'], L['patch'], L['cols']
    per = cols * cols
    pos = np.array(L['pos'])
    m = P // 4
    table = np.zeros((n ** 3, 3))
    node_of = np.argsort(pos)  # global slot -> node
    for im in range(L['images']):
        img = read_tiff(os.path.join(args.render, f'out_{im:03d}.tif'))
        for slot in range(per):
            g = im * per + slot
            if g >= len(pos): break
            y, x = divmod(slot, cols)
            c = img[y * P + m:(y + 1) * P - m, x * P + m:(x + 1) * P - m]
            table[node_of[g]] = c.reshape(-1, 3).mean(0)
    write_cube(args.out, table, n, args.title, args.style)
    print(f'{args.out}: {n}^3, range {table.min():.4f}..{table.max():.4f}')


def write_cube(path, table, n, title, style):
    lines = [f'TITLE "{title}"']
    if style:
        lines.append(f'#LUMIXPHOTOSTYLE {style}')
    lines += [f'LUT_3D_SIZE {n}', 'DOMAIN_MIN 0.0 0.0 0.0', 'DOMAIN_MAX 1.0 1.0 1.0', '']
    for row in np.clip(table, 0, 1):
        lines.append('%.6f %.6f %.6f' % tuple(row))
    open(path, 'w').write('\n'.join(lines) + '\n')


def load_cube(path):
    n = None; vals = []
    for line in open(path):
        s = line.strip()
        if not s or s.startswith('#') or s.startswith('TITLE') or s.startswith('DOMAIN'):
            continue
        if s.startswith('LUT_3D_SIZE'):
            n = int(s.split()[1]); continue
        vals.append([float(v) for v in s.split()[:3]])
    return n, np.array(vals)


def diff(args):
    na, a = load_cube(args.a); nb, b = load_cube(args.b)
    d = np.abs(a - b).max(1) * 255
    print(f'max channel diff (8-bit units): mean {d.mean():.3f}  p99 {np.percentile(d, 99):.3f}  max {d.max():.3f}')


def apply_lut(table, n, img):
    t = table.reshape(n, n, n, 3)  # [b][g][r]
    x = np.clip(img, 0, 1) * (n - 1)
    i = np.minimum(np.floor(x).astype(int), n - 2)
    f = x - i
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    ir, ig, ib = i[..., 0], i[..., 1], i[..., 2]
    def T(dr, dg, db):
        return t[ib + db, ig + dg, ir + dr]
    c000 = T(0, 0, 0); c111 = T(1, 1, 1)
    out = np.zeros_like(img)
    conds = [
        (r >= g) & (g >= b), (r >= b) & (b > g), (b > r) & (r >= g),
        (g > r) & (r >= b), (g >= b) & (b > r), (b > g) & (g > r),
    ]
    # tetrahedra: (first axis, second axis)
    tets = [((1,0,0),(1,1,0),r,g,b), ((1,0,0),(1,0,1),r,b,g), ((0,0,1),(1,0,1),b,r,g),
            ((0,1,0),(1,1,0),g,r,b), ((0,1,0),(0,1,1),g,b,r), ((0,0,1),(0,1,1),b,g,r)]
    for cond, (a1, a2, f1, f2, f3) in zip(conds, tets):
        c1 = T(*a1); c2 = T(*a2)
        v = c000 + (c1 - c000) * f1[..., None] + (c2 - c1) * f2[..., None] + (c111 - c2) * f3[..., None]
        out = np.where(cond[..., None], v, out)
    return out


def apply_cmd(args):
    n, table = load_cube(args.lut)
    img = read_tiff(args.inp)
    write_tiff16(args.out, np.round(np.clip(apply_lut(table, n, img), 0, 1) * 65535))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    m = sp.add_parser('make'); m.add_argument('out'); m.add_argument('--n', type=int, default=33)
    m.add_argument('--patch', type=int, default=64); m.add_argument('--cols', type=int, default=16)
    m.add_argument('--seed', type=int); m.add_argument('--sort-lum', action='store_true'); m.set_defaults(f=make)
    r = sp.add_parser('read'); r.add_argument('render'); r.add_argument('layout'); r.add_argument('out')
    r.add_argument('--title', default='LightCraft'); r.add_argument('--style', default='STD'); r.set_defaults(f=read)
    d = sp.add_parser('diff'); d.add_argument('a'); d.add_argument('b'); d.set_defaults(f=diff)
    a = sp.add_parser('apply'); a.add_argument('lut'); a.add_argument('inp'); a.add_argument('out'); a.set_defaults(f=apply_cmd)
    args = ap.parse_args(); args.f(args)

if __name__ == '__main__':
    main()
