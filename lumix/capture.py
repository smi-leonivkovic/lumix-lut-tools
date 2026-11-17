"""Take a picture with gphoto2 and read what the camera applied from the maker note (exiftool)."""
import json
import os
import shutil
import subprocess
import sys
import time

from .ptp import LOCK, CameraError

GRAIN = {0: 'off', 1: 'low', 2: 'standard', 3: 'high', 4: 'low+colour noise', 5: 'standard+colour noise', 6: 'high+colour noise'}
TAGS = ['LUT1Name', 'LUT1Opacity', 'MonochromeGrainEffect', 'PhotoStyle', 'WhiteBalance', 'ColorTempKelvin', 'ISO',
        'ExposureTime', 'FNumber', 'ExposureCompensation', 'IntelligentD-Range', 'ImageQuality', 'ImageSize']


def capture(outdir, basename=None):
    for tool in ('gphoto2', 'exiftool'):
        if not shutil.which(tool):
            raise CameraError(f'{tool} is required for capture (brew install {tool}).')
    os.makedirs(outdir, exist_ok=True)
    base = os.path.join(outdir, basename or time.strftime('lumix_%Y%m%d_%H%M%S'))
    with LOCK:
        if sys.platform == 'darwin':
            subprocess.run(['killall', '-9', 'ptpcamerad'], capture_output=True)
        r = subprocess.run(['gphoto2', '--capture-image-and-download', '--filename', base + '.%C', '--force-overwrite'],
                           capture_output=True, text=True, timeout=120)
    files = [base + ext for ext in ('.JPG', '.RW2', '.MOV', '.MP4') if os.path.exists(base + ext)]
    if not files:
        raise CameraError('Capture failed: ' + (r.stderr or r.stdout)[-300:])
    info = {'files': files}
    jpg = next((f for f in files if f.endswith('.JPG')), None)
    if jpg:
        e = subprocess.run(['exiftool', '-j', '-n'] + [f'-{t}' for t in TAGS] + [jpg], capture_output=True, text=True)
        tags = json.loads(e.stdout)[0]
        tags.pop('SourceFile', None)
        if 'MonochromeGrainEffect' in tags:
            tags['grain'] = GRAIN.get(tags['MonochromeGrainEffect'], tags['MonochromeGrainEffect'])
        info['applied'] = tags
    elif any(f.endswith(('.MOV', '.MP4')) for f in files):
        info['note'] = 'The camera recorded video: it is in a video mode or the photo/video switch is on video.'
    return info
