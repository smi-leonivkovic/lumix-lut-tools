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

## Reading LUTs back (backup)

- **LutGetFileData 0x9921 works**: the command block carries `[0x53000012 u32][slot u8]` (5 bytes, not a u32 param;
  sending it as a data phase gets no answer). Reply: `[0x53000012][size][file length u32][.cube text]`. The camera
  stores the header tags it received (`#GRAINEFFECT`, `#COLORNOISE`) and writes 7-decimal floats, `TITLE ""`.
  `lumix.luts.backup()` / MCP `backup_luts` save the whole library.

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
- **Don't use standard PTP property ops (0x1014/0x1015/0x1016) for properties the camera doesn't list** (DeviceInfo
  lists only 0x5001 battery): GetDevicePropValue 0x500E (ExposureProgramMode) gets **no answer**. The camera doesn't
  freeze; the pending transaction blocks the link. **Recovery without replug:** the PTP-over-USB class *Device Reset
  Request* (bmRequestType 0x21, bRequest 0x66) restores it (verified). `lumix/ptp.py` does this automatically on a
  timeout (cancel request → device reset request → clear halts → USB port reset) and warns before such requests.
- **P/A/S/M can't be set over USB.** libgphoto2's `expmode` (0x06000011) is the movie exposure mode; LUMIX Lab has no
  photo exposure-mode setter either. 0x9918 LumixControlCameraMode switches shooting (1) vs gallery/LUT management (2).
- macOS `ptpcamerad` re-grabs the camera between calls; claim the interface with retries. If a transfer is interrupted
  the link can stop answering: the device reset request (0x66) recovers it, replug as a last resort.
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
- **Grain works via the `.cube` header** (verified, DC-S9 2.1): header `TITLE "…"`, `#LUMIXPHOTOSTYLE STD`,
  `#GRAINEFFECT L60`, `LUT_3D_SIZE 33`, data (no DOMAIN lines), uploaded over USB in one transfer. Shots then record
  maker note `MonochromeGrainEffect = 5` (was Off) and show visible grain at 100%. L20 was too faint to notice.
  The library list (GetLutInfo) reports 0 in the grain/noise/sharpness fields regardless, so check a shot, not the list.
  **`#COLORNOISE L0` verified too:** with it the camera's own colour-noise setting (0x020001F2) switched to off when
  the LUT was uploaded/active, and shots record `MonochromeGrainEffect` 3 (High grain, no colour noise) instead of 6.
  The camera loads these tags into its settings. Without the tag, High grain inherits the camera's colour-noise
  setting (colour speckles on B&W looks). `#SHARPNESS`, `#NOISEREDUCTION`: same syntax, not verified yet.
- Grain strengths: L1–33 Low, L34–66 Standard, L67–100 High; no size control. L20 was hard to see, L50–60 clear,
  L85 strong. Maker note `MonochromeGrainEffect`: 1/2/3 = Low/Standard/High, 4/5/6 = the same with colour noise.
- More Rec properties found by testing (tether mode): 0x020001F2 colour noise on/off, 0x020001F3 LUT 1 on/off,
  0x020001F9 LUT opacity (10–100).
- **Active LUT selection is not exposed over PTP** (as far as tested; also tried: select style 0x02000223 + My Photo
  Style edit session + 0x020001FB, on style 49 and on MY PHOTO STYLE 1 — accepted, ignored): switching the LUT on the camera changes none of
  the single properties nor the 0x020001F0/0x02000220/0x02000010 blocks; writing 0x020001FB (alone or inside the
  My Photo Style edit session 0x9419 StartEdit/EndEdit) is accepted but ignored. Next step would be recording LUMIX Lab.
- LUT upload/rename/sort/delete also work in **PC (Tether)** USB mode (04da:2382); no need to switch to LUMIX Lab mode.
  In tether mode GetLutInfo records are **262 bytes** (id, name, style, type) instead of 272 (no grain/noise/visibility
  fields); the parser detects it from the size field.
- `pipeline/add_grain.py IN OUT LEVEL` writes a camera LUT with grain (colour noise off by default). Standard (L50) is a
  good default for colour looks; High (L85) for heavy B&W.
- A `.cube` without a base tag is applied on V-Log. That's right for V-Log LUTs (ARRI 709_Legacy, S5II Legacy packs)
  and wrong for Standard ones; `lumix_lut.py selftest` lists which LUTs sit on that default.

## Firmware

- Panasonic only offers the newest firmware; update from the SD card (`.bin` on the card root, Setup → Firmware).
  Remove macOS `._` sidecar files from the card so the camera doesn't see a second `.bin`.
- 2.0 added LUMIX Lab wired connection and LUT extras (grain/colour noise for photos, sharpness, NR).
