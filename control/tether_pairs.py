#!/usr/bin/env python3
"""Shoot the scene in front of the camera as Standard and through the camera's LUT slot, RAW+JPEG each,
over a sweep of white balance and exposure. No chart or monitor needed: variety comes from the WB/EV sweep.

  tether_pairs.py OUTDIR [--wb Automatic,Daylight,Tungsten,Cloudy,Shadow] [--ev -1.666667,-0.666667,0.333333,1.333333]
                         [--styles 0,49]

Files: OUTDIR/w{wb}_e{ev}_s{style}.JPG/.RW2 and shots.json. Restores Photo Style, WB and EV at the end.
Photo Style is written through 0x02000011 (0x02000010 is read-only).
"""
import argparse, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lumixctl as L

PS_R, PS_W = 0x02000010, 0x02000011


def ptp(fn):
    p = L.PTP()
    try:
        return fn(p)
    finally:
        p.close()


def gp(*a):
    subprocess.run(['killall', '-9', 'ptpcamerad'], capture_output=True)
    return subprocess.run(['gphoto2', *a], capture_output=True, text=True)


def cur(name):
    out = gp('--get-config', name).stdout
    return next(l.split(': ', 1)[1] for l in out.splitlines() if l.startswith('Current:'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--wb', default='Automatic,Daylight,Tungsten,Cloudy,Shadow')
    ap.add_argument('--ev', default='-1.666667,-0.666667,0.333333,1.333333')
    ap.add_argument('--styles', default='0,49')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    orig_ps = ptp(lambda p: p.get(PS_R)[2])
    orig_wb, orig_ev = cur('whitebalance'), cur('exposurecompensation')
    print(f'original: style {orig_ps}, wb {orig_wb}, ev {orig_ev}', flush=True)
    shots = []
    try:
        for wb in a.wb.split(','):
            gp('--set-config-value', f'whitebalance={wb}')
            for ev in a.ev.split(','):
                gp('--set-config-value', f'exposurecompensation={ev}')
                for st in (int(s) for s in a.styles.split(',')):
                    ptp(lambda p: p.set(PS_W, st, 2))
                    name = f'w{wb}_e{float(ev):+.1f}_s{st:02d}'
                    r = gp('--capture-image-and-download', '--filename', os.path.join(a.out, name + '.%C'), '--force-overwrite')
                    ok = r.returncode == 0
                    print(name, 'ok' if ok else 'FAILED ' + (r.stderr or r.stdout)[-200:], flush=True)
                    shots.append({'name': name, 'wb': wb, 'ev': float(ev), 'style': st, 'ok': ok})
                    if not ok and 'No camera found' in r.stderr + r.stdout:
                        return
    finally:
        ptp(lambda p: p.set(PS_W, orig_ps, 2))
        gp('--set-config-value', f'whitebalance={orig_wb}')
        gp('--set-config-value', f'exposurecompensation={orig_ev}')
        print('restored:', ptp(lambda p: p.get(PS_R)[2]), cur('whitebalance'), cur('exposurecompensation'), flush=True)
        json.dump(shots, open(os.path.join(a.out, 'shots.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
