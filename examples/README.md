# Example LUTs

| File | What |
|---|---|
| `luts/identity_std.cube` | No change. Upload test: the camera image must look exactly like Standard. |
| `luts/demo_warm_std.cube` | Simple demo look: gentle S-curve, lifted blacks, warm highlights. |
| `luts/demo_warm_grain_std.cube` | Same plus `#GRAINEFFECT/#COLORNOISE/#SHARPNESS/#NOISEREDUCTION` header lines. `#GRAINEFFECT` verified on a DC-S9 (visible grain, maker note `MonochromeGrainEffect` set); the other three tags are unverified. |

```sh
python3 control/lumix_lut.py push examples/luts/identity_std.cube 30 "Identity test"
python3 control/lumix_lut.py selftest   # check it shows base STD
```
