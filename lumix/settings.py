"""Panasonic vendor properties: read, list allowed values, write, with name <-> value mappings verified on a DC-S9."""
import struct

from .ptp import OK, CameraError

GET, SET, LIST = 0x9402, 0x9403, 0x9108

# (read prop, write prop, size). Some properties only accept writes through their "param" twin.
PROPS = {
    'photo_style': (0x02000010, 0x02000011, 2),
    'image_format': (0x020000A2, 0x020000A2, 2),
    'white_balance': (0x02000050, 0x02000051, 2),
    'kelvin': (0x02000052, 0x02000052, 2),
    'wb_adjust_gm': (0x02000054, 0x02000054, 2),
    'iso': (0x02000020, 0x02000021, 4),
    'exposure_comp': (0x02000060, 0x02000061, 2),
    'aperture': (0x02000040, 0x02000041, 2),
    'shutter': (0x02000030, 0x02000031, 4),
    'color_noise': (0x020001F2, 0x020001F2, 2),
    'lut1_on': (0x020001F3, 0x020001F3, 2),
    'lut1_opacity': (0x020001F9, 0x020001F9, 2),
}

PHOTO_STYLES = {'standard': 0, 'vivid': 1, 'natural': 2, 'monochrome': 3, 'scenery': 4, 'portrait': 5,
                'l_monochrome': 15, 'cinelike_d2': 17, 'vlog': 18, 'custom1': 20, 'custom2': 21, 'custom3': 22,
                'real_time_lut': 49}
WB_MODES = {'auto': 0x0002, 'daylight': 0x0004, 'fluorescent': 0x0005, 'tungsten': 0x0006, 'flash': 0x0007,
            'cloudy': 0x8008, 'white_set': 0x8009, 'shade': 0x800F, 'kelvin': 0x8010, 'kelvin2': 0x8011,
            'kelvin3': 0x8012, 'kelvin4': 0x8013, 'auto_cool': 0x8014, 'auto_warm': 0x8015}
IMAGE_FORMATS = {'raw': 3, 'raw+jpeg': 4}
ISO_AUTO = 0xFFFFFFFF


def _name(table, value):
    return next((k for k, v in table.items() if v == value), value)


def ev_encode(ev):
    """EV in stops -> Panasonic 1/3-stop code (negative values have bit 15 set)."""
    thirds = round(ev * 3)
    return (0x8000 | -thirds) if thirds < 0 else thirds


def ev_decode(code):
    return round(-(code & 0x7FFF) / 3 if code & 0x8000 else code / 3, 2)


def get(cam, prop):
    rc, _, d = cam.tx(GET, [prop])
    if rc != OK or len(d) < 8:
        return None
    size = struct.unpack('<I', d[4:8])[0]
    if size in (2, 4):
        return struct.unpack('<H' if size == 2 else '<I', d[8:8 + size])[0]
    return d[8:8 + size].hex()


def allowed(cam, prop, size):
    rc, _, d = cam.tx(LIST, [prop, 0, 0])
    if rc != OK or len(d) < 32:
        return []
    o = struct.unpack('<I', d[4:8])[0] * 4 + 8
    fmt = '<I' if size == 4 else '<H'
    n = struct.unpack('<I', d[o + size:o + size + 4])[0]
    b = o + size + 4
    return [struct.unpack(fmt, d[b + i * size:b + (i + 1) * size])[0] for i in range(n) if b + (i + 1) * size <= len(d)]


def put(cam, prop, value, size):
    payload = struct.pack('<II', prop, size) + (struct.pack('<H', value) if size == 2 else struct.pack('<I', value))
    rc, _, _ = cam.tx(SET, [prop], payload)
    return rc


def read(cam, key):
    rp, _, _ = PROPS[key]
    return get(cam, rp)


def write(cam, key, value):
    """Write a setting, verify by reading back. Returns (old, new)."""
    rp, wp, size = PROPS[key]
    old = get(cam, rp)
    rc = put(cam, wp, value, size)
    if rc != OK and wp != rp:
        rc = put(cam, rp, value, size)
    new = get(cam, rp)
    if rc != OK or new != value:
        raise CameraError(f'{key}: camera did not accept {value} (rc 0x{rc:04x}, reads {new})')
    return old, new


def status(cam):
    r = {k: read(cam, k) for k in PROPS}
    return {
        'photo_style': _name(PHOTO_STYLES, r['photo_style']),
        'image_format': _name(IMAGE_FORMATS, r['image_format']),
        'white_balance': _name(WB_MODES, r['white_balance']),
        'kelvin': r['kelvin'],
        'wb_adjust_gm': r['wb_adjust_gm'],
        'iso': 'auto' if r['iso'] == ISO_AUTO else r['iso'],
        'exposure_comp_ev': ev_decode(r['exposure_comp']) if r['exposure_comp'] is not None else None,
        'aperture_f': r['aperture'] / 10 if r['aperture'] else None,
        'color_noise': bool(r['color_noise']) if r['color_noise'] is not None else None,
        'lut1_on': bool(r['lut1_on']) if r['lut1_on'] is not None else None,
        'lut1_opacity': r['lut1_opacity'],
    }
