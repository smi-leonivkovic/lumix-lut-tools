#!/usr/bin/env python3
"""Write tests/sample_lutinfo.bin: a made-up GetLutInfo reply (41 records) for testing parsers without a camera."""
import os, struct
names = [('Vlog_709', 40, 1), ('ARRI 709', 65535, 2), ('My Look', 0, 3), ('', 0, 3), ('Natural Look', 2, 3), ('VLog Look', 65535, 3)]
recs = b''
for i in range(41):
    name, style, typ = names[i] if i < len(names) else ('', 0, 3)
    recs += struct.pack('<H', i) + name.encode().ljust(256, b'\0') + struct.pack('<7H', style, typ, 0, 0, 0, 0, 1 if name else 0)
body = bytes([sum(1 for n, _, _ in names if n)]) + recs
data = struct.pack('<II', 0x53000011, len(body)) + body
open(os.path.join(os.path.dirname(__file__), 'sample_lutinfo.bin'), 'wb').write(data)
