#!/usr/bin/env python3
"""Offline tests for the lumix package and lumix-mcp (no camera): python tests/test_offline.py"""
import asyncio, os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, '..'))
from lumix import luts, settings

# EV codes as the camera reports them
assert settings.ev_encode(-2 / 3) == 0x8002 and settings.ev_decode(0x8002) == -0.67
assert settings.ev_encode(1) == 3 and settings.ev_decode(3) == 1.0
# .cube header writer
src = open(os.path.join(here, '..', 'examples', 'luts', 'identity_std.cube')).read()
out = luts.cube_with_tags(src, grain=50, color_noise=0, title='T').split('\n')
assert out[:5] == ['TITLE "T"', '#LUMIXPHOTOSTYLE STD', '#GRAINEFFECT L50', '#COLORNOISE L0', 'LUT_3D_SIZE 33'], out[:5]
assert len([l for l in out if l and l[0].isdigit()]) == 33 ** 3
# library parser, both record sizes
subprocess.run([sys.executable, os.path.join(here, 'make_sample_lutinfo.py')], check=True)
for f in ('sample_lutinfo.bin', 'sample_lutinfo_tether.bin'):
    e = luts.parse_lutinfo(open(os.path.join(here, f), 'rb').read())
    assert [x['name'] for x in e] == ['Vlog_709', 'ARRI 709', 'My Look', 'Natural Look', 'VLog Look']
    assert e[4]['on_vlog_default'] and not e[2]['on_vlog_default']
# MCP server exposes its tools
from lumix.mcp_server import server
names = {t.name for t in asyncio.run(server.list_tools())}
assert {'camera_status', 'list_luts', 'upload_lut', 'delete_lut', 'capture', 'restore_settings'} <= names, names
print(f'ok: offline tests passed, {len(names)} MCP tools')
