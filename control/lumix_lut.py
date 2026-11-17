#!/usr/bin/env python3
"""LUT Library control over USB (camera USB mode "LUMIX Lab", 04da:2387), using the commands LUMIX Lab 3.1.0 uses
(see docs/PROTOCOL.md "LUT Library protocol").

  lumix_lut.py list                         read the library (read only)
  lumix_lut.py push FILE.cube SLOT NAME     upload into an EMPTY slot (refuses occupied slots unless --replace)
  lumix_lut.py rename SLOT NAME
  lumix_lut.py sort FROM TO
  lumix_lut.py select SLOT                  make SLOT the active LUT 1

Safety: only the LUT ops 0x9922/0x9924/0x9923 and SetParamInfo LUT codes are sent; firmware ops (0x9606/0x9607) are
never used. Names are ASCII, max 255 bytes.
"""
import os, struct, subprocess, sys, time
import usb.core, usb.util, usb.backend.libusb1

VID = 0x04DA
GET_PARAM, SET_PARAM, SET_REC = 0x9414, 0x9415, 0x9403
LUT_START, LUT_CANCEL, LUT_SEND = 0x9922, 0x9923, 0x9924
GET_LUT_INFO, RENAME, DELETE, SORT = 0x53000011, 0x53000013, 0x53000014, 0x53000015
LUT1_REG = 0x020001FB
CHUNK = 61440
FORBIDDEN = {0x9606, 0x9607}  # firmware channel


class PTP:
    def __init__(self):
        subprocess.run(['killall', '-9', 'ptpcamerad'], capture_output=True)
        be = usb.backend.libusb1.get_backend(find_library=lambda x: '/opt/homebrew/lib/libusb-1.0.dylib')
        self.dev = usb.core.find(idVendor=VID, backend=be)
        if self.dev is None:
            sys.exit('LUMIX not found on USB (on, awake, USB mode LUMIX Lab?)')
        if self.dev.idProduct != 0x2387:
            print(f'warning: product 0x{self.dev.idProduct:04x}, LUT commands are expected in LUMIX Lab mode (0x2387)')
        try:
            self.dev.set_configuration()
        except usb.core.USBError:
            pass
        intf = self.dev.get_active_configuration()[(0, 0)]
        for i in range(8):
            try:
                usb.util.claim_interface(self.dev, 0); break
            except usb.core.USBError:
                if i == 7: raise
                subprocess.run(['killall', '-9', 'ptpcamerad'], capture_output=True); time.sleep(0.4)
        ep = lambda d: usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == d and usb.util.endpoint_type(e.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK)
        self.out, self.inp = ep(usb.util.ENDPOINT_OUT), ep(usb.util.ENDPOINT_IN)
        self.tid = 0
        rc, _, _ = self.tx(0x1002, [1])
        if rc not in (0x2001, 0x201E):
            sys.exit(f'OpenSession failed 0x{rc:04x}')

    def tx(self, code, params, data=None):
        assert code not in FORBIDDEN
        self.tid += 1
        self.out.write(struct.pack('<IHHI', 12 + 4 * len(params), 1, code, self.tid) + b''.join(struct.pack('<I', p) for p in params), timeout=5000)
        if data is not None:
            self.out.write(struct.pack('<IHHI', 12 + len(data), 2, code, self.tid) + data, timeout=30000)
        got = b''
        while True:
            buf = bytes(self.inp.read(1 << 20, timeout=30000))
            ln = struct.unpack('<I', buf[:4])[0]
            while len(buf) < ln:
                buf += bytes(self.inp.read(1 << 20, timeout=30000))
            typ, rc = struct.unpack('<HH', buf[4:8])
            if typ == 2:
                got += buf[12:ln]
            elif typ == 3:
                return rc, list(struct.unpack(f'<{(ln - 12) // 4}I', buf[12:12 + (ln - 12) // 4 * 4])), got

    def close(self):
        try:
            self.tx(0x1003, [])
        except Exception:
            pass
        usb.util.dispose_resources(self.dev)


def name256(s):
    b = s.encode('ascii', 'replace')[:255]
    return b + b'\0' * (256 - len(b))


def lut_info(p):
    rc, _, d = p.tx(GET_PARAM, [GET_LUT_INFO])
    return rc, d


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    p = PTP()
    try:
        if cmd == 'list':
            rc, d = lut_info(p)
            print(f'GetLutInfo rc=0x{rc:04x}, {len(d)} bytes')
            open('lutinfo.bin', 'wb').write(d)
            for i in range(0, min(len(d), 4096), 32):
                chunk = d[i:i + 32]
                print(f'{i:05x}  {chunk.hex(" ")}  {"".join(chr(c) if 32 <= c < 127 else "." for c in chunk)}')
            print('raw saved to ./lutinfo.bin')
        elif cmd == 'push':
            path, slot, name = args[0], int(args[1]), args[2]
            if not (0 <= slot <= 40):
                sys.exit('slot must be 0-40')
            blob = open(path, 'rb').read()
            if len(blob) > 9437184:
                sys.exit('file larger than 9 MB')
            rc, _, _ = p.tx(LUT_START, [slot], name256(name))
            print(f'LutStartFileData slot {slot} "{name}": rc=0x{rc:04x}')
            if rc != 0x2001:
                return
            # USB: LUMIX Lab sends the whole file in ONE LutSendFileData (bufsize = fileSize); 60 KB chunks are its
            # Wi-Fi fallback. Chunking over USB made the camera keep only the last chunk (no header, broken LUT).
            rc, _, _ = p.tx(LUT_SEND, [len(blob)], blob)
            if rc != 0x2001:
                print(f'send rc=0x{rc:04x}, cancelling'); p.tx(LUT_CANCEL, []); return
            print(f'sent {len(blob)} bytes in one transfer: done')
        elif cmd == 'rename':
            slot, name = int(args[0]), args[1]
            rc, _, _ = p.tx(SET_PARAM, [RENAME], struct.pack('<IIH', RENAME, 258, slot) + name256(name))
            print(f'rename slot {slot} -> "{name}": rc=0x{rc:04x}')
        elif cmd == 'sort':
            a, b = int(args[0]), int(args[1])
            rc, _, _ = p.tx(SET_PARAM, [SORT], struct.pack('<IIHH', SORT, 4, a, b))
            print(f'sort {a} -> {b}: rc=0x{rc:04x}')
        elif cmd == 'select':
            slot = int(args[0])
            rc, _, _ = p.tx(SET_REC, [LUT1_REG], struct.pack('<IIH', LUT1_REG, 2, slot))
            print(f'select LUT1 slot {slot}: rc=0x{rc:04x}')
        else:
            sys.exit(__doc__)
    finally:
        p.close()


if __name__ == '__main__':
    main()
