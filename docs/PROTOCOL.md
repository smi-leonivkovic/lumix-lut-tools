# Camera protocols

## USB (PTP, mode "PC (Tether)")

- USB id 04DA:2382. gphoto2 2.5.32 reports it as "DC-GH5" in auto-detect; the summary says DC-S9.
- macOS `ptpcamerad` grabs the camera: `killall -9 ptpcamerad` right before each gphoto2/pyusb call.
- In tether mode the card is not exposed as storage (`--storage-info` empty), and the camera says "No File Upload".
- Panasonic vendor ops (libgphoto2 camlibs/ptp2):
  - `0x9402` GetProperty [prop] → data `[prop u32][size u32][value]`
  - `0x9108` ListProperty [prop,0,0] → current + allowed values
  - `0x9403` SetProperty [prop], data `[prop u32][size u16][2 pad][value]`
  - `0x9404` InitiateCapture [0x3000011]
- DeviceInfo lists vendor ops 0x9102 0x9103 0x9104 only, but 0x9402/0x9108 answer OK anyway.

### Properties seen (17 Nov 2026)

| Prop | Name | Size | Value then | Allowed |
|---|---|---|---|---|
| 0x02000010 | PhotoStyle | 2 | 40 | 0 1 2 44 18 4 5 3 15 17 45 50 41 42 14 40 49 16 19 20 21 22 |
| 0x02000020 | ISO | 4 | 0xFFFFFFFF (auto) | auto, 3 special, 640…51200 (min 640 → Log-type base, or video mode) |
| 0x020000A2 | ImageFormat | 2 | 3 | (list empty) |
| 0x02000060 | Exposure comp. | 2 | 5 | 0x8009…0x8001 (negative), 0…6 |
| 0x02000050 | WhiteBalance | 2 | 2 | 15 values |

That reading was taken in a **video** custom mode (a capture produced a `.MOV`), so it is not the photo setup.
Photo Style codes still need mapping: set a code, shoot, read the JPEG maker note (exiftool `PhotoStyle`).

## Wi-Fi (cam.cgi, from sapoepsilon/lumix-remote docs)

- Camera AP 192.168.54.1, SSDP discovery, plain HTTP `cam.cgi?mode=…`.
- `accctrl&type=req_acc`, `getinfo&type=capability|allmenu|curmenu|camsetting`, `setsetting/getsetting&type=photostyle|…`.
- Upload channel: `requestsenddata`, `startsenddata`, `senddata` (multipart, UA "LUMIX Sync"), `endsenddata`,
  `abortsenddata`, `getprogress`. Documented for firmware; LUT parameters unknown → must be captured from LUMIX Lab.

## BLE

LUMIX Lab pairing: challenge 0x7A → 0x72/0x74; app name "LUMIX LUT Creators APP 1.2.1" written at 0x70.

### What can be set over USB (checked 17 Nov 2026)

| Setting | Over USB? | How |
|---|---|---|
| Photo Style | **read-only** | `0x02000010` writes return 0x201D; try Wi-Fi cam.cgi |
| Image format (RAW+JPEG) | yes | `0x020000A2`, allowed 0 1 4 5 3, current 3 (codes to map) |
| P/A/S/M | yes | gphoto2 `expmode` (prop 0x06000011) |
| ISO, WB, exposure comp., shutter, aperture, AF mode | yes | gphoto2 config / lumixctl |
| Photo ↔ video | **no** | physical photo/video switch on the S9 |
| Custom mode C1/C2/C3 | **no** | no property for it; camera menu |
| i.Dynamic, Sleep Mode | **no** | menu only, no PTP property |
| USB mode PC (Tether) | n/a | must already be set for USB control to work |

Other reads: CameraMode 0x02000080 = 1 (allowed 0 1 9 4 3), ModePos 0x02000082 = 9, CreativeMode 0x02000083 = 22.

## LUT Library protocol (from LUMIX Lab 3.1.0 for Android, decompiled 17 Nov 2026)

Source: `com.panasonic.jp.lumixlab` 3.1.0 (versionCode 22), Play-signed. Op table `p183q6/A.java`, builders `A6/r.java`.
Works over PTP in USB mode "LUMIX Lab" (04da:2387); Lab also has a Wi-Fi path with the same payloads.
Data phases for Panasonic ops are `[code u32][payload size u32][payload]`.

| Op | Name | Params | Data out |
|---|---|---|---|
| 0x9414 | GetParamInfo | 0x53000011 GetLutInfo | – (returns library list) |
| 0x9415 | SetParamInfo | 0x53000013 RenameLUTFile | `[0x53000013][258][u16 slot][256 B ASCII name, NUL-padded]` |
| 0x9415 | SetParamInfo | 0x53000015 SortLUTFile | `[0x53000015][4][u16 from][u16 to]` (0–40) |
| 0x9415 | SetParamInfo | 0x53000014 DeleteLUTFile | `[0x53000014][2][u16 slot]` |
| 0x9921 | LutGetFileData | 0x53000012 GetLUTFile | slot byte; reads a LUT back |
| 0x9922 | LutStartFileData | slot | 256 B ASCII name, NUL-padded |
| 0x9924 | LutSendFileData | file length | **whole file in ONE transfer over USB** (≤ 9 MB). 61440 B chunks are only Lab's Wi-Fi fallback; chunking over USB leaves the camera with just the last chunk (no header → base style none → LUT applied on V-Log, looks broken). Uploading to an occupied slot replaces it. |
| 0x9923 | LutCancelFileData | – | – |
| 0x9403 | SetRecInfo | 0x020001FB Lut1RegistrationInformation | `[code][2][u16 slot]` |
| 0x9403 | SetRecInfo | 0x020001F3 Lut1 (values 0, 1, 65534, 65535) / 0x020001F8 Lut2 | |

Valid slots: 0–40 and 65535. The app uploads into a slot taken from the camera's GetLutInfo list.
Event 0xC219 LumixLutFileChangeInfo. Also present: 0x9419 CtrlMyPhotoStyle, 0x9421/9422/9423 Export/Import/Save config file.
Firmware channel 0x9606/0x9607 is separate and never needed for LUTs.

Rec props (p183q6/t, s): 0x02000011 StyleMode (= Photo Style write), 0x02000013 Sharpness, 0x02000014 NoiseReduction,
0x0200001F PhotoStyle, 0x020001F2 ColorNoise.

**.cube extras** (written by native `convertToCube` in libllc.so), header lines:
`#LUMIXPHOTOSTYLE %s`, `#GRAINEFFECT L%d`, `#COLORNOISE L%d`, `#SHARPNESS L%d`, `#NOISEREDUCTION L%d` (L0–L100).
Panasonic's bundled LUTs use `#LUMIXPHOTOSTYLE STD|NAT|CNEV2`.

### GetLutInfo reply (parser `p205s6/L.java`)

`[0x53000011 u32][size u32][u8 count]` then records of 272 bytes (camera always returns 41, deleted ones have an empty name):
`[u16 id 0–40][256 B name, NUL-padded][u16 photo style (PTP Photo Style code: 0 STD, 2 NAT, 5 portrait-type, 40 V-Log; 65535 none)]
[u16 type 1 built-in / 2 Panasonic sample / 3 user][u16 grain][u16 colour noise][u16 sharpness][u16 noise reduction][u16 visibility]`.

Positions 0 (Vlog_709) and 1 (ARRI 709 sample) cannot be sorted into or out of. SortLUTFile moves one entry. DeleteLUTFile
leaves a gap (empty record); close it by sorting the following entries up.
