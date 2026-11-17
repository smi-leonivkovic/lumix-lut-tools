# pana_style.py JPG... -> PhotoStyle (Panasonic makernote tag 0x0089), ISO
import sys, struct
STY = {1:'Auto',2:'Standard/Custom',3:'Vivid',4:'Natural',5:'Monochrome',6:'Scenery',7:'Portrait',8:'Cinelike D',9:'Cinelike V',
       10:'L.Monochrome',11:'Like709',12:'L.Classic Neo',13:'Flat',14:'V-Log',15:'Real Time LUT',16:'Leica Monochrome',17:'L.Monochrome D',
       18:'L.Monochrome S',19:'709Like',20:'Standard'}
for p in sys.argv[1:]:
    b = open(p, 'rb').read(200000)
    i = b.find(b'Panasonic\x00\x00\x00')
    if i < 0: print(p, 'no makernote'); continue
    t = b.find(b'Exif\x00\x00') + 6; bo = '<' if b[t:t+2] == b'II' else '>'
    o = i + 12; (n,) = struct.unpack(bo+'H', b[o:o+2]); vals = {}
    for k in range(n):
        tag, typ, cnt = struct.unpack(bo+'HHI', b[o+2+12*k:o+10+12*k]); v = b[o+10+12*k:o+14+12*k]
        vals[tag] = struct.unpack(bo+'H', v[:2])[0] if typ == 3 else struct.unpack(bo+'I', v)[0]
    s = vals.get(0x89)
    print(p.split('/')[-1], 'PhotoStyle', s, STY.get(s, '?'))
