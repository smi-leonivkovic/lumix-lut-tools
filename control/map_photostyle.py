#!/usr/bin/env python3
"""Map PTP Photo Style codes (0x02000010) to names: set each allowed code, shoot, read the maker note.

  map_photostyle.py OUTDIR

Restores the original Photo Style at the end. Uses gphoto2 for capture (it deletes the test shots from the card).
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lumixctl as L

PS = 0x02000010   # read
PSW = 0x02000011  # write (0x02000010 rejects writes with 0x201D)
SUB = list(range(0x02000011, 0x02000020))
TAGS = ['PhotoStyle', 'LUT1Name', 'LUT1Opacity', 'MonochromeGrainEffect', 'ContrastMode', 'Contrast', 'Saturation', 'Sharpness', 'NoiseReduction', 'HighlightShadow',
        'MonochromeFilterEffect', 'FilterEffect', 'ColorEffect', 'Panasonic_0x0087']


def ptp(fn):
    p = L.PTP()
    try:
        return fn(p)
    finally:
        p.close()


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    orig, allowed = ptp(lambda p: L.parse_list(p.list(PS)[1], 2))
    print('original', orig, 'allowed', allowed, flush=True)
    res = []
    try:
        for code in allowed:
            rc = ptp(lambda p: p.set(PSW, code, 2))
            sub = ptp(lambda p: {f'0x{q:08x}': p.get(q)[2] for q in [PS] + SUB})
            subprocess.run(['killall', '-9', 'ptpcamerad'], capture_output=True)
            base = os.path.join(out, f'ps{code:02d}')
            r = subprocess.run(['gphoto2', '--capture-image-and-download', '--filename', base + '.%C', '--force-overwrite'],
                               capture_output=True, text=True)
            jpg = base + '.JPG'
            tags = {}
            if os.path.exists(jpg):
                e = subprocess.run(['exiftool', '-j', '-n', '-u'] + [f'-Panasonic:{t}' for t in TAGS] + [jpg],
                                   capture_output=True, text=True)
                tags = json.loads(e.stdout)[0]
                tags.pop('SourceFile', None)
                os.remove(base + '.RW2') if os.path.exists(base + '.RW2') else None
            row = {'code': code, 'set_rc': f'0x{rc:04x}', 'props': sub, 'exif': tags, 'shot_ok': r.returncode == 0}
            print(json.dumps(row), flush=True)
            res.append(row)
    finally:
        rc = ptp(lambda p: p.set(PSW, orig, 2))
        print(f'restored Photo Style {orig}: rc=0x{rc:04x}', flush=True)
        json.dump(res, open(os.path.join(out, 'photostyle_map.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
