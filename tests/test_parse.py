#!/usr/bin/env python3
"""Offline test of the GetLutInfo parser: python3 tests/test_parse.py (needs pyusb importable, no camera)."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
subprocess.run([sys.executable, os.path.join(here, 'make_sample_lutinfo.py')], check=True)
sys.path.insert(0, os.path.join(here, '..', 'control'))
import lumix_lut as LL
for f, rec in (('sample_lutinfo.bin', 272), ('sample_lutinfo_tether.bin', 262)):
    e = LL.parse_lutinfo(open(os.path.join(here, f), 'rb').read())
    assert [x['name'] for x in e] == ['Vlog_709', 'ARRI 709', 'My Look', 'Natural Look', 'VLog Look'], e
    assert e[3]['pos'] == 4 and e[3]['style'] == 2 and e[0]['type'] == 1 and e[0]['record_size'] == rec
    print(f'ok: {f}: {len(e)} entries, {rec}-byte records, empty slot skipped')
