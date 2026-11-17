#!/usr/bin/env python3
"""Reorder the camera's LUT Library to a wanted name order (USB mode LUMIX Lab).

  lut_reorder.py ORDER.txt [--dry-run]

ORDER.txt: one LUT name per line, in the wanted order starting at position 1 (position 0, Vlog_709, is fixed).
Names not listed keep their relative order after the listed ones. Uses SortLUTFile(from, to) and re-reads the
library after every move, so it works whether the camera moves or swaps.
"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lumix_lut as LL


def read(p):
    rc, d = LL.lut_info(p)
    assert rc == 0x2001, hex(rc)
    out = []
    for i in range((len(d) - 9) // 272):  # all records; deleted LUTs leave empty-name gaps
        o = 9 + i * 272
        rid = struct.unpack('<H', d[o:o + 2])[0]
        out.append((rid, d[o + 2:o + 258].split(b'\0')[0].decode('ascii', 'replace')))
    names = [name for _, name in sorted(out)]
    while names and not names[-1]:
        names.pop()
    return names


def main():
    want = [l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()]
    dry = '--dry-run' in sys.argv
    p = LL.PTP()
    try:
        cur = read(p)
        missing = [w for w in want if w not in cur]
        if missing:
            sys.exit(f'not in camera: {missing}')
        print('before:', cur)
        start = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--start=")), 1))
        for pos, name in enumerate(want, start=start):
            cur = read(p)
            i = cur.index(name)
            if i == pos:
                continue
            print(f'move "{name}" {i} -> {pos}')
            if dry:
                cur.insert(pos, cur.pop(i)); continue
            rc, _, _ = p.tx(LL.SET_PARAM, [LL.SORT], struct.pack('<IIHH', LL.SORT, 4, i, pos))
            if rc != 0x2001:
                sys.exit(f'sort rc=0x{rc:04x}')
        final = read(p)
        print('after:')
        for k, n in enumerate(final):
            print(f'  {k:2d} {n}')
    finally:
        p.close()


if __name__ == '__main__':
    main()
