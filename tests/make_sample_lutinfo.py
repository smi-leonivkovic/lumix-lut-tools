#!/usr/bin/env python3
"""Write made-up GetLutInfo replies (41 records) for testing parsers without a camera:
tests/sample_lutinfo.bin (272-byte records, LUMIX Lab mode) and tests/sample_lutinfo_tether.bin (262-byte, PC Tether)."""
import os, struct
names = [('Vlog_709', 40, 1), ('ARRI 709', 65535, 2), ('My Look', 0, 3), ('', 0, 3), ('Natural Look', 2, 3), ('VLog Look', 65535, 3)]
for rec, fname in ((272, 'sample_lutinfo.bin'), (262, 'sample_lutinfo_tether.bin')):
  recs = b''
  for i in range(41):
    name, style, typ = names[i] if i < len(names) else ('', 0, 3)
    r = struct.pack('<H', i) + name.encode().ljust(256, b'\0') + struct.pack('<7H', style, typ, 0, 0, 0, 0, 1 if name else 0)
    recs += r[:rec]
  body = bytes([sum(1 for n, _, _ in names if n)]) + recs
  data = struct.pack('<II', 0x53000011, len(body)) + body
  open(os.path.join(os.path.dirname(__file__), fname), 'wb').write(data)
