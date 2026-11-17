#!/usr/bin/env python3
"""Read-only: open a PTP session with the LUMIX in any USB mode and print the full DeviceInfo
(operations, events, properties, capture/playback formats) plus storage IDs.

  devinfo.py [PID hex, default: first Panasonic device]
"""
import struct, subprocess, sys, time
import usb.core, usb.util, usb.backend.libusb1

OPS = {0x1001: 'GetDeviceInfo', 0x1002: 'OpenSession', 0x1003: 'CloseSession', 0x1004: 'GetStorageIDs',
       0x1005: 'GetStorageInfo', 0x1006: 'GetNumObjects', 0x1007: 'GetObjectHandles', 0x1008: 'GetObjectInfo',
       0x1009: 'GetObject', 0x100A: 'GetThumb', 0x100B: 'DeleteObject', 0x100C: 'SendObjectInfo',
       0x100D: 'SendObject', 0x100E: 'InitiateCapture', 0x100F: 'FormatStore', 0x1014: 'GetDevicePropDesc',
       0x1015: 'GetDevicePropValue', 0x1016: 'SetDevicePropValue', 0x101B: 'GetPartialObject',
       0x9801: 'MTP GetObjectPropsSupported', 0x9802: 'MTP GetObjectPropDesc', 0x9803: 'MTP GetObjectPropValue',
       0x9804: 'MTP SetObjectPropValue', 0x9805: 'MTP GetObjPropList', 0x9808: 'MTP SendObjPropList'}


def main():
    subprocess.run(['killall', '-9', 'ptpcamerad'], capture_output=True)
    be = usb.backend.libusb1.get_backend(find_library=lambda x: '/opt/homebrew/lib/libusb-1.0.dylib')
    kw = {'idVendor': 0x04DA, 'backend': be}
    if len(sys.argv) > 1:
        kw['idProduct'] = int(sys.argv[1], 16)
    dev = usb.core.find(**kw)
    if dev is None:
        sys.exit('no Panasonic USB device')
    print(f'device 04da:{dev.idProduct:04x}')
    try:
        dev.set_configuration()
    except usb.core.USBError:
        pass
    intf = dev.get_active_configuration()[(0, 0)]
    for i in range(8):
        try:
            usb.util.claim_interface(dev, 0); break
        except usb.core.USBError:
            subprocess.run(['killall', '-9', 'ptpcamerad'], capture_output=True); time.sleep(0.4)
    ep = lambda d: usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == d and usb.util.endpoint_type(e.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK)
    out, inp = ep(usb.util.ENDPOINT_OUT), ep(usb.util.ENDPOINT_IN)
    tid = [0]

    def tx(code, params):
        tid[0] += 1
        out.write(struct.pack('<IHHI', 12 + 4 * len(params), 1, code, tid[0]) + b''.join(struct.pack('<I', p) for p in params), timeout=5000)
        data = b''
        while True:
            buf = bytes(inp.read(1 << 20, timeout=10000))
            ln = struct.unpack('<I', buf[:4])[0]
            while len(buf) < ln:
                buf += bytes(inp.read(1 << 20, timeout=10000))
            typ, rc = struct.unpack('<HH', buf[4:8])
            if typ == 2:
                data += buf[12:ln]
            elif typ == 3:
                return rc, data

    rc, d = tx(0x1001, [])  # GetDeviceInfo works without a session
    o = 0
    std, vext = struct.unpack('<HI', d[o:o + 6]); o += 6
    vver = struct.unpack('<H', d[o:o + 2])[0]; o += 2

    def pstr():
        nonlocal o
        n = d[o]; o += 1
        s = d[o:o + 2 * n].decode('utf-16-le', 'replace').rstrip('\0'); o += 2 * n
        return s

    def arr():
        nonlocal o
        n = struct.unpack('<I', d[o:o + 4])[0]; o += 4
        v = list(struct.unpack(f'<{n}H', d[o:o + 2 * n])); o += 2 * n
        return v

    print(f'PTP std {std}, vendor ext 0x{vext:x} v{vver}, ext desc "{pstr()}"')
    mode = struct.unpack('<H', d[o:o + 2])[0]; o += 2
    ops, evs, props, capf, playf = arr(), arr(), arr(), arr(), arr()
    print('manufacturer:', pstr(), '| model:', pstr(), '| version:', pstr())
    print(f'functional mode {mode}')
    print('operations:'); [print(f'  0x{x:04x} {OPS.get(x, "")}') for x in ops]
    print('events:', ' '.join(f'0x{x:04x}' for x in evs))
    print('properties:', ' '.join(f'0x{x:04x}' for x in props))
    print('capture formats:', ' '.join(f'0x{x:04x}' for x in capf))
    print('playback formats:', ' '.join(f'0x{x:04x}' for x in playf))
    rc, _ = tx(0x1002, [1])
    print(f'OpenSession rc=0x{rc:04x}')
    if rc in (0x2001, 0x201E):
        rc, s = tx(0x1004, [])
        n = struct.unpack('<I', s[:4])[0] if len(s) >= 4 else 0
        ids = struct.unpack(f'<{n}I', s[4:4 + 4 * n]) if n else ()
        print(f'GetStorageIDs rc=0x{rc:04x}:', ' '.join(f'0x{i:08x}' for i in ids))
        tx(0x1003, [])
    usb.util.dispose_resources(dev)


if __name__ == '__main__':
    main()
