#!/usr/bin/env python3
"""Test every USB control we rely on, in PC (Tether) mode, restoring each setting afterwards.

  capability_test.py OUTDIR

For each setting: read, write a different allowed value, read back, (optionally shoot and check the maker note),
restore, read back. Prints a PASS/FAIL table and writes OUTDIR/report.json.
"""
import json, os, struct, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lumix_lut as LL

GET, SET, LIST = 0x9402, 0x9403, 0x9108


def get(p, prop):
    rc, _, d = p.tx(GET, [prop])
    if rc != 0x2001 or len(d) < 8:
        return None
    size = struct.unpack('<I', d[4:8])[0]
    return struct.unpack('<H' if size == 2 else '<I', d[8:8 + size])[0] if size in (2, 4) else d[8:8 + size].hex()


def allowed(p, prop, size):
    rc, _, d = p.tx(LIST, [prop, 0, 0])
    if rc != 0x2001 or len(d) < 32:
        return []
    hl = struct.unpack('<I', d[4:8])[0]; o = hl * 4 + 8
    fmt = '<I' if size == 4 else '<H'
    n = struct.unpack('<I', d[o + size:o + size + 4])[0]; b = o + size + 4
    return [struct.unpack(fmt, d[b + i * size:b + (i + 1) * size])[0] for i in range(n) if b + (i + 1) * size <= len(d)]


def put(p, prop, val, size=2):
    data = struct.pack('<II', prop, size) + (struct.pack('<H', val) if size == 2 else struct.pack('<I', val))
    rc, _, _ = p.tx(SET, [prop], data)
    return rc


def shoot(path):
    subprocess.run(['killall', '-9', 'ptpcamerad'], capture_output=True)
    r = subprocess.run(['gphoto2', '--capture-image-and-download', '--filename', path + '.%C', '--force-overwrite'], capture_output=True, text=True)
    if not os.path.exists(path + '.JPG'):
        return {}
    e = subprocess.run(['exiftool', '-j', '-n', '-LUT1Name', '-PhotoStyle', '-WhiteBalance', '-ColorTempKelvin', '-ISO',
                        '-ExposureCompensation', '-ImageQuality', '-MonochromeGrainEffect', path + '.JPG'], capture_output=True, text=True)
    return json.loads(e.stdout)[0]


# (label, read prop, write prop, size, test value or None = pick another allowed one)
TESTS = [
    ('Photo Style', 0x02000010, 0x02000011, 2, 0),          # Standard
    ('Image format', 0x020000A2, 0x020000A2, 2, 3),         # RAW only
    ('White balance mode', 0x02000050, 0x02000051, 2, 0x8015),  # AWB warm
    ('Kelvin', 0x02000052, 0x02000052, 2, 5600),
    ('ISO', 0x02000020, 0x02000021, 4, 800),
    ('Exposure comp.', 0x02000060, 0x02000061, 2, 3),        # +1 EV
    ('Aperture', 0x02000040, 0x02000041, 2, 56),             # F5.6
]


def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    p = LL.PTP()
    report = []
    try:
        for label, rp, wp, size, val in TESTS:
            orig = get(p, rp)
            if val is None or val == orig:
                al = [v for v in allowed(p, rp, size) if v != orig]
                val = al[0] if al else None
            r = {'setting': label, 'read': hex(rp), 'write': hex(wp), 'orig': orig, 'test': val}
            rc = put(p, wp, val, size)
            r['write_rc'] = hex(rc); r['after'] = get(p, rp)
            if rc != 0x2001 and wp != rp:  # try the plain property too
                rc2 = put(p, rp, val, size); r['plain_rc'] = hex(rc2); r['after'] = get(p, rp)
            r['changed'] = r['after'] == val
            rc3 = put(p, wp, orig, size)
            if rc3 != 0x2001 and wp != rp:
                rc3 = put(p, rp, orig, size)
            r['restored'] = get(p, rp) == orig
            report.append(r)
            print(f"{label:20s} {'PASS' if r['changed'] and r['restored'] else 'FAIL'}  {orig} -> {val} -> {r['after']} -> restored {r['restored']}  rc {r['write_rc']}", flush=True)
        # capture + maker note
        p.close(); time.sleep(0.5)
        tags = shoot(os.path.join(out, 'capture'))
        report.append({'setting': 'Capture + download', 'tags': tags, 'changed': bool(tags), 'restored': True})
        print(f"{'Capture + download':20s} {'PASS' if tags else 'FAIL'}  {tags}", flush=True)
        p = LL.PTP()
        rc, d = LL.lut_info(p)
        n = len(LL.parse_lutinfo(d))
        report.append({'setting': 'LUT library read', 'changed': rc == 0x2001, 'restored': True, 'entries': n})
        print(f"{'LUT library read':20s} {'PASS' if rc == 0x2001 else 'FAIL'}  {n} entries", flush=True)
    finally:
        p.close()
        json.dump(report, open(os.path.join(out, 'report.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
