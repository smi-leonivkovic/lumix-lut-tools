"""Live view for Panasonic LUMIX over USB (as in libgphoto2): 0x9412 start/stop, 0x9706 frame = header + JPEG."""
import struct
import time

from .ptp import OK, CameraError

LIVEVIEW, LIVEVIEW_IMAGE = 0x9412, 0x9706
START, STOP = 0x0D000010, 0x0D000011
REC_RELEASE, REC_AFAE = 0x9404, 0x9405
RELEASE_PHOTO = 0x03000011
AF_ONESHOT = 0x03000024


SIZES = {(640, 480): 0x20, (960, 720): 0xFA, (1280, 960): 0x1C2}  # third field as the camera lists it
PARAMS_CURRENT, PARAMS_ALL = 0x0D800011, 0x0D800012
GET_PARAM, SET_PARAM = 0x9414, 0x9415


def sizes(cam):
    """Live view formats the camera offers: [(width, height, fps)]."""
    rc, _, d = cam.tx(GET_PARAM, [PARAMS_ALL])
    n = struct.unpack('<H', d[8:10])[0]
    return [(w, h, fps) for h, w, _x, fps in (struct.unpack('<HHHH', d[12 + 8 * i:20 + 8 * i]) for i in range(n))]


def set_size(cam, width, height):
    x = SIZES.get((width, height), 0x1C2)
    rc, _, _ = cam.tx(SET_PARAM, [PARAMS_CURRENT], struct.pack('<IIHHHH', PARAMS_CURRENT, 8, height, width, x, 30))
    if rc != OK:
        raise CameraError(f'Live view size refused: 0x{rc:04x}')


def start(cam):
    rc, _, _ = cam.tx(LIVEVIEW, [START])
    if rc != OK:
        raise CameraError(f'Live view start refused: 0x{rc:04x}')
    time.sleep(0.1)


def stop(cam):
    try:
        cam.tx(LIVEVIEW, [STOP])
    except Exception:
        pass


def frame(cam, tries=25):
    """One live view frame -> (jpeg bytes, header bytes). Retries while the camera reports busy (0x2019)."""
    for _ in range(tries):
        rc, _, d = cam.tx(LIVEVIEW_IMAGE, [], timeout=5000)
        if rc == 0x2019:
            time.sleep(0.04)
            continue
        if rc != OK:
            raise CameraError(f'Live view frame refused: 0x{rc:04x}')
        soi = d.find(b'\xff\xd8')
        if soi < 0:
            raise CameraError('Live view data contains no JPEG')
        return d[soi:], d[:soi]
    raise CameraError('Camera stayed busy')


def autofocus(cam):
    rc, _, _ = cam.tx(REC_AFAE, [AF_ONESHOT])
    return rc


MF_DRIVE, MF_PARAM = 0x9416, 0x03010011
MF_STEPS = {'stop': 0, 'far_fast': 1, 'far_slow': 2, 'near_slow': 3, 'near_fast': 4}


def mf_drive(cam, step):
    """Drive the focus motor (as libgphoto2 'manualfocusdrive'): keeps moving until 'stop'. Needs focus mode MF,
    otherwise the camera answers 0x201D."""
    rc, _, _ = cam.tx(MF_DRIVE, [MF_PARAM], struct.pack('<IIH', MF_PARAM, 2, MF_STEPS[step]), timeout=5000)
    return rc


def shutter(cam):
    """Take a picture to the card (not downloaded)."""
    rc, _, _ = cam.tx(REC_RELEASE, [RELEASE_PHOTO])
    return rc


def parse_header(h):
    """Live view header sections ([u32 code][u32 size][data], codes 0x1700000x) -> dict.
    histogram: 64 luminance bins (0x17000003); level: (a, b) signed raw values of LevelInfo (0x17000005),
    presumably roll/pitch in 0.1 deg (unverified); rotation (0x17000004)."""
    out, o = {}, 0
    while o + 8 <= len(h):
        code, size = struct.unpack('<II', h[o:o + 8])
        if code & 0xFFFFFF00 != 0x17000000:
            break
        d = h[o + 8:o + 8 + size]
        o += 8 + size
        if code == 0x17000003 and len(d) >= 80:
            out['histogram'] = list(d[16:80])
        elif code == 0x17000004 and len(d) >= 6:
            out['rotation'] = struct.unpack('<H', d[4:6])[0]
        elif code == 0x17000005 and len(d) >= 8:
            out['level'] = struct.unpack('<hh', d[4:8])
    return out
