# Findings

What we learned building this, including the mistakes, so nobody has to repeat them. Camera: DC-S9, firmware 1.5 → 2.1.

## LUT upload

- **Send the whole file in one `LutSendFileData` (0x9924) over USB.** LUMIX Lab uses 61,440-byte chunks only for Wi-Fi.
  Chunking over USB made the camera keep just the last chunk: no header, base Photo Style "none" (65535), and the LUT
  got applied on V-Log, so switching to it looked broken. One transfer → base 0 (Standard), correct look.
- Uploading to an occupied slot replaces it.
- The library list reports the base Photo Style per LUT; check it after every upload (`lumix_lut.py list`).
- Positions 0 (Vlog_709) and 1 (ARRI 709 sample) can't be sorted into or out of. Deleting leaves an empty record (gap);
  close it by moving the following entries up one at a time.
- The camera shows the name you send (up to 255 ASCII bytes; LUMIX Lab truncates to 95). Card imports keep the file
  name including `.cube`.

## USB modes and properties

- USB mode **PC (Tether)** enumerates as 04da:2382, **LUMIX Lab** as 04da:2387. Both are PTP; Panasonic vendor commands
  work although DeviceInfo doesn't list them. LUT commands are used in LUMIX Lab mode.
- Photo Style: `0x02000010` is read-only (writes return 0x201D); write it via **`0x02000011`** ("StyleMode").
  PTP codes: 0 Standard, 1 Vivid, 2 Natural, 3 Monochrome, 4 Scenery, 5 Portrait, 15 L.Monochrome, 17 Cinelike D2,
  18 V-Log, 49 Real Time LUT slot, 19 LUT slot at reduced opacity, 20–22 Custom 1–3.
- Image format `0x020000A2`: 3 = RAW, 4 = RAW+JPEG.
- `0x020001FB` (Lut1RegistrationInformation) accepted writes in tether mode but didn't change the applied LUT there.
- Shooting mode (P/A/S/M), custom mode, the photo/video switch, i.Dynamic and Sleep Mode can't be set over PTP in tether mode.
- Firmware 2.1 exposes ~37 more readable properties than 1.5 (0x02000210–0x0200022A and others).
- macOS `ptpcamerad` re-grabs the camera between calls; claim the interface with retries. If a transfer is interrupted
  the camera's USB stack can hang: replug or power-cycle.
- `gphoto2 --capture-image-and-download` deletes the shot from the card after download.

## Camera behaviour worth knowing

- **Per-slot exposure offset:** with a LUT slot selected, the camera metered about +1⅓ EV brighter than Standard at the
  same compensation setting (another LUT entry had −1⅓). It's stored with the slot, not in the `.cube`. Watch zebras.
- The maker note records the applied LUT: exiftool tags `LUT1Name`, `LUT1Opacity`, `MonochromeGrainEffect`,
  `IntelligentD-Range`. Use them to verify which look a file was shot with.
- Camera Standard JPEG ≈ LightCraft default render (~4/255).

## Making LUTs that match a RAW preset

- Presets are tuned for RAW; applying a preset to JPEG-like colour grids gave a flat, blotchy look ~26/255 off. Fit
  the LUT from RAW pairs instead (default render → preset render): held-out error 1.5–2.3/255 on most presets.
- **Geometry pitfall:** if the default render applies lens correction and the preset render doesn't, the frames don't
  line up and the fit learns noise (16/255 instead of 1.5). Switch lens correction off in both renders.
- **Local tone is not LUT-able:** presets with strong Highlights/Shadows (e.g. −70/+53) or clarity stay 4–5/255 off.
  Balanced sampling doesn't help. Camera i.Dynamic Range (High) does part of that work locally and brought those
  presets from ~5 to ~4/255; fit those LUTs for i.Dynamic High.
- Refining a LUT directly on a single tethered scene overfits (held-out error went up); keep it to a sanity check.
- "Bright" variants: lift midtones in a luminance pre-curve with a soft shoulder (white unchanged) instead of raising
  exposure, so highlights don't clip.
- **Strip absolute white balance** from presets (Kelvin/tint): a LUT can't set a colour temperature, the fit turns it
  into a fixed cast (here cool/magenta). Keep WB as shot so the camera's AWB decides; `settings/nospatial.json` does this.
- Grain, colour noise, sharpness and noise reduction can travel with the LUT as header lines (`#GRAINEFFECT L%d` …).

## Firmware

- Panasonic only offers the newest firmware; update from the SD card (`.bin` on the card root, Setup → Firmware).
  Remove macOS `._` sidecar files from the card so the camera doesn't see a second `.bin`.
- 2.0 added LUMIX Lab wired connection and LUT extras (grain/colour noise for photos, sharpness, NR).
