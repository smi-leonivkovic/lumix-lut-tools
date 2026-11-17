"""Minimal PTP-over-USB transport for Panasonic LUMIX cameras (macOS/Linux, libusb via pyusb).

One connection per operation: `with Camera() as cam: cam.tx(...)`. A process-wide lock keeps calls from overlapping.
Firmware-channel operations are refused here, whatever the caller asks.
"""
import ctypes.util
import os
import struct
import subprocess
import sys
import threading
import time
import warnings

import usb.backend.libusb1
import usb.core
import usb.util

VID = 0x04DA
KNOWN_PRODUCTS = {0x2382: 'PC (Tether)', 0x2387: 'LUMIX Lab'}
FORBIDDEN_OPS = {0x9606, 0x9607}  # LumixSendDataInfo / LumixSendData: firmware update channel
STD_PROP_OPS = {0x1014, 0x1015, 0x1016}  # standard Get/SetDevicePropDesc/Value
STD_PROPS_OK = {0x5001}  # the only standard property a DC-S9 lists; others (e.g. 0x500E) hang its USB stack
OK = 0x2001
LOCK = threading.RLock()


try:  # surface our messages to MCP clients verbatim
    from mcp.server.mcpserver.exceptions import ToolError as _Base
except Exception:  # package used without the MCP SDK
    _Base = RuntimeError


class CameraError(_Base):
    pass


def _backend():
    for path in (os.environ.get('LIBUSB_PATH'), '/opt/homebrew/lib/libusb-1.0.dylib', '/usr/local/lib/libusb-1.0.dylib',
                 ctypes.util.find_library('usb-1.0')):
        if path and (os.path.exists(path) or not path.startswith('/')):
            be = usb.backend.libusb1.get_backend(find_library=lambda _x, p=path: p)
            if be:
                return be
    return usb.backend.libusb1.get_backend()


def _free_from_macos():
    if sys.platform == 'darwin':
        subprocess.run(['killall', '-9', 'ptpcamerad'], capture_output=True)


class Camera:
    def __init__(self):
        self.dev = None

    def __enter__(self):
        LOCK.acquire()
        try:
            self.open()
        except Exception:
            LOCK.release()
            raise
        return self

    def __exit__(self, *exc):
        try:
            self.close()
        finally:
            LOCK.release()

    def open(self):
        _free_from_macos()
        self.dev = usb.core.find(idVendor=VID, backend=_backend())
        if self.dev is None:
            raise CameraError('No LUMIX camera on USB. Switch it on, set USB mode to PC (Tether), plug it in.')
        try:
            self.dev.set_configuration()
        except usb.core.USBError:
            pass
        intf = self.dev.get_active_configuration()[(0, 0)]
        for attempt in range(8):
            try:
                usb.util.claim_interface(self.dev, intf.bInterfaceNumber)
                break
            except usb.core.USBError:
                if attempt == 7:
                    raise CameraError('Could not claim the camera (another program has it?). Replug and retry.')
                _free_from_macos()
                time.sleep(0.4)
        bulk = lambda d: usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == d
                                                  and usb.util.endpoint_type(e.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK)
        self.out, self.inp = bulk(usb.util.ENDPOINT_OUT), bulk(usb.util.ENDPOINT_IN)
        self.tid = 0
        rc, _, _ = self.tx(0x1002, [1])  # OpenSession
        if rc not in (OK, 0x201E):
            raise CameraError(f'OpenSession failed: 0x{rc:04x}')

    @property
    def usb_mode(self):
        return KNOWN_PRODUCTS.get(self.dev.idProduct, f'unknown (0x{self.dev.idProduct:04x})')

    def tx(self, code, params, data=None, timeout=30000):
        """One PTP transaction -> (response code, response params, data in)."""
        if code in FORBIDDEN_OPS:
            raise CameraError(f'Operation 0x{code:04x} is the firmware channel and is blocked.')
        if code in STD_PROP_OPS and (not params or params[0] not in STD_PROPS_OK):
            warnings.warn('Standard PTP property 0x%04x is not listed by the camera; on a DC-S9 this request hung the '
                          'USB connection until replug.' % (params[0] if params else 0), RuntimeWarning, stacklevel=2)
        self.tid += 1
        self.out.write(struct.pack('<IHHI', 12 + 4 * len(params), 1, code, self.tid)
                       + b''.join(struct.pack('<I', p) for p in params), timeout=5000)
        if data is not None:
            self.out.write(struct.pack('<IHHI', 12 + len(data), 2, code, self.tid) + data, timeout=timeout)
        got = b''
        while True:
            buf = bytes(self.inp.read(1 << 20, timeout=timeout))
            length = struct.unpack('<I', buf[:4])[0]
            while len(buf) < length:
                buf += bytes(self.inp.read(1 << 20, timeout=timeout))
            typ, rc = struct.unpack('<HH', buf[4:8])
            if typ == 2:
                got += buf[12:length]
            elif typ == 3:
                n = (length - 12) // 4
                return rc, list(struct.unpack(f'<{n}I', buf[12:12 + 4 * n])), got

    def close(self):
        if self.dev is None:
            return
        try:
            self.tx(0x1003, [])  # CloseSession
        except Exception:
            pass
        usb.util.dispose_resources(self.dev)
        self.dev = None

    def device_info(self):
        rc, _, d = self.tx(0x1001, [])
        if rc != OK:
            raise CameraError(f'GetDeviceInfo failed 0x{rc:04x}')
        o = 8
        def pstr():
            nonlocal o
            n = d[o]; o += 1
            s = d[o:o + 2 * n].decode('utf-16-le', 'replace').rstrip('\0'); o += 2 * n
            return s
        def arr():
            nonlocal o
            n = struct.unpack('<I', d[o:o + 4])[0]; o += 4 + 2 * n
        pstr(); o += 2
        for _ in range(5):
            arr()
        return {'manufacturer': pstr(), 'model': pstr(), 'firmware': pstr(), 'serial': pstr()}
