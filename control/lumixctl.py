#!/usr/bin/env python3
"""Minimal PTP-over-USB client for Panasonic LUMIX (tested target: DC-S9) — vendor property access.

  lumixctl.py info                       device info + supported vendor operations
  lumixctl.py get   PROP [PROP…]         current value (PROP hex, e.g. 0x02000010)
  lumixctl.py list  PROP [PROP…]         current value + allowed values (0x9108)
  lumixctl.py set   PROP VALUE [--size 2|4]
  lumixctl.py scan  [FROM TO STEP]       list every readable property in a range (read only)
  lumixctl.py capture                    take a picture (to the camera's capture target)

Protocol from libgphoto2 (camlibs/ptp2): 0x9402 GetProperty, 0x9108 ListProperty, 0x9403 SetProperty with
data [propcode u32][valuesize u16][2 pad][value]. macOS' ptpcamerad grabs cameras; it is killed before use.
"""
import struct, subprocess, sys, time
import usb.core, usb.util, usb.backend.libusb1

VID, PID = 0x04DA, 0x2382
NAMES = {
    0x02000010: 'PhotoStyle', 0x02000020: 'ISO', 0x02000030: 'ShutterSpeed', 0x02000040: 'Aperture',
    0x02000050: 'WhiteBalance', 0x02000060: 'Exposure', 0x02000070: 'AFArea', 0x02000080: 'CameraMode',
    0x02000081: 'DriveMode', 0x02000082: 'ModePos', 0x02000083: 'CreativeMode', 0x02000084: 'iAMode',
    0x020000A2: 'ImageFormat', 0x020000B0: 'MeteringInfo', 0x020000E0: 'RecDispConfig',
}


class PTP:
    def __init__(self):
        subprocess.run(['killall', '-9', 'ptpcamerad'], capture_output=True)
        be = usb.backend.libusb1.get_backend(find_library=lambda x: '/opt/homebrew/lib/libusb-1.0.dylib')
        self.dev = usb.core.find(idVendor=VID, idProduct=PID, backend=be)
        if self.dev is None:
            sys.exit('LUMIX not found on USB (is it on and in PC (Tether) mode?)')
        try:
            self.dev.set_configuration()
        except usb.core.USBError:
            pass
        intf = self.dev.get_active_configuration()[(0, 0)]
        for attempt in range(8):  # macOS respawns ptpcamerad, which can grab the camera between calls
            try:
                usb.util.claim_interface(self.dev, intf.bInterfaceNumber)
                break
            except usb.core.USBError:
                if attempt == 7:
                    raise
                subprocess.run(['killall', '-9', 'ptpcamerad'], capture_output=True)
                time.sleep(0.4)
        ep = lambda d, t: usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == d and usb.util.endpoint_type(e.bmAttributes) == t)
        self.out = ep(usb.util.ENDPOINT_OUT, usb.util.ENDPOINT_TYPE_BULK)
        self.inp = ep(usb.util.ENDPOINT_IN, usb.util.ENDPOINT_TYPE_BULK)
        self.tid = 0
        code, _, _ = self.tx(0x1002, [1])  # OpenSession
        if code not in (0x2001, 0x201E):  # OK / SessionAlreadyOpen
            sys.exit(f'OpenSession failed: 0x{code:04x}')

    def close(self):
        try:
            self.tx(0x1003, [])
        except Exception:
            pass
        usb.util.dispose_resources(self.dev)

    def _send(self, typ, code, payload):
        self.out.write(struct.pack('<IHHI', 12 + len(payload), typ, code, self.tid) + payload, timeout=5000)

    def _read(self):
        buf = bytes(self.inp.read(1 << 20, timeout=15000))
        length = struct.unpack('<I', buf[:4])[0]
        while len(buf) < length:
            buf += bytes(self.inp.read(1 << 20, timeout=15000))
        typ, code, _ = struct.unpack('<HHI', buf[4:12])
        return typ, code, buf[12:length]

    def tx(self, code, params, data_out=None):
        """One PTP transaction -> (response code, response params, data-in bytes)."""
        self.tid += 1
        self._send(1, code, b''.join(struct.pack('<I', p) for p in params))
        if data_out is not None:
            self._send(2, code, data_out)
        data = b''
        while True:
            typ, rc, body = self._read()
            if typ == 2:
                data += body
            elif typ == 3:
                return rc, list(struct.unpack(f'<{len(body)//4}I', body[:len(body)//4*4])), data

    def get(self, prop):
        rc, _, d = self.tx(0x9402, [prop])
        if rc != 0x2001 or len(d) < 8:
            return rc, None, None
        size = struct.unpack('<I', d[4:8])[0]
        val = struct.unpack('<I' if size == 4 else '<H', d[8:8 + size])[0] if size in (2, 4) else d[8:8 + size].hex()
        return rc, size, val

    def list(self, prop):
        rc, _, d = self.tx(0x9108, [prop, 0, 0])
        return rc, d

    def set(self, prop, value, size):
        payload = struct.pack('<IH', prop, size) + b'\0\0' + (struct.pack('<I', value) if size == 4 else struct.pack('<H', value))
        rc, _, _ = self.tx(0x9403, [prop], payload)
        return rc


def parse_list(d, size):
    """Decode a 0x9108 reply like libgphoto2's ptp_panasonic_getdevicepropertydesc."""
    if len(d) < 32:
        return None, []
    hl = struct.unpack('<I', d[4:8])[0]
    o = hl * 4 + 8
    fmt = '<I' if size == 4 else '<H'
    cur = struct.unpack(fmt, d[o:o + size])[0]
    n = struct.unpack('<I', d[o + size:o + size + 4])[0]
    base = o + size + 4
    vals = [struct.unpack(fmt, d[base + i * size: base + (i + 1) * size])[0] for i in range(n) if base + (i + 1) * size <= len(d)]
    return cur, vals


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    p = PTP()
    try:
        if cmd == 'info':
            rc, _, d = p.tx(0x1001, [])
            def arr16(off):
                n = struct.unpack('<I', d[off:off + 4])[0]
                return list(struct.unpack(f'<{n}H', d[off + 4: off + 4 + 2 * n])), off + 4 + 2 * n
            off = 8
            sl = d[off]; off += 1 + 2 * sl  # vendor extension desc string
            off += 2  # functional mode
            ops, off = arr16(off)
            print('vendor ops:', ' '.join(f'0x{o:04x}' for o in ops if o >= 0x9000))
        elif cmd in ('get', 'list'):
            for a in args:
                prop = int(a, 16)
                rc, size, val = p.get(prop)
                line = f'0x{prop:08x} {NAMES.get(prop, ""):14s} rc=0x{rc:04x} size={size} value={val}'
                if cmd == 'list' and size in (2, 4):
                    lrc, d = p.list(prop)
                    cur, vals = parse_list(d, size)
                    line += f' | allowed ({len(vals)}): {vals}'
                print(line)
        elif cmd == 'set':
            prop = int(args[0], 16); val = int(args[1], 0)
            size = int(args[3]) if len(args) > 3 and args[2] == '--size' else (p.get(prop)[1] or 4)
            rc = p.set(prop, val, size)
            print(f'set 0x{prop:08x} = {val} (size {size}): rc=0x{rc:04x}', '(OK)' if rc == 0x2001 else '')
            print('now:', p.get(prop)[2])
        elif cmd == 'scan':
            lo, hi, step = (int(x, 16) for x in (args + ['0x02000000', '0x02000200', '0x1'])[len(args):len(args) + 3]) if len(args) == 0 else (int(args[0], 16), int(args[1], 16), int(args[2], 16))
            for prop in range(lo, hi, step):
                rc, size, val = p.get(prop)
                if rc == 0x2001:
                    print(f'0x{prop:08x} {NAMES.get(prop, ""):14s} size={size} value={val}')
        elif cmd == 'capture':
            rc, _, _ = p.tx(0x9404, [0x3000011])
            print(f'capture rc=0x{rc:04x}')
        else:
            sys.exit(__doc__)
    finally:
        p.close()


if __name__ == '__main__':
    main()
