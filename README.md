# lumix-lut-tools

Manage the **Real Time LUT Library of a Panasonic LUMIX S9 from a computer over USB**, without the LUMIX Lab app or an
SD card, plus a pipeline for turning photo-editor presets into camera LUTs that look like the preset on the RAW.

Tested on a DC-S9 with firmware 2.1 on macOS (Apple Silicon). Other LUMIX bodies that support LUMIX Lab's wired
connection probably speak the same protocol, but are untested.

## What works

| Task | Tool |
|---|---|
| Read-only check of camera and library | `control/lumix_lut.py selftest` |
| List the LUT Library (names, base Photo Style, type) | `control/lumix_lut.py list` |
| Upload a `.cube` into a slot (new or replace) | `control/lumix_lut.py push FILE.cube SLOT "Name"` |
| Rename / reorder | `control/lumix_lut.py rename SLOT "Name"`, `control/lut_reorder.py order.txt --start=2` |
| Read device info in any USB mode | `control/devinfo.py` |
| Tethered shooting, Photo Style / format / WB / EV over USB | `control/lumixctl.py`, `control/tether_pairs.py` |
| Add grain (no colour noise) to any LUT | `pipeline/add_grain.py my.cube my_grain.cube 50` |
| Preset → 33-point camera LUT, evaluation sheets | `pipeline/` (needs LightCraft, see below) |

## lumix-mcp (MCP server)

Lets an AI assistant (Claude Code, Claude Desktop, any MCP client) drive the camera: list/upload/rename/move/delete LUTs,
write grain into LUTs, set Photo Style, white balance, ISO, exposure, aperture, image format, LUT opacity, take pictures
and report what the camera applied (LUT, grain, WB).

```sh
python3 -m venv .venv && .venv/bin/pip install -e .     # needs libusb (brew install libusb); capture needs gphoto2 + exiftool
claude mcp add lumix-mcp -- "$PWD/.venv/bin/lumix-mcp"   # Claude Code; other clients: command = .venv/bin/lumix-mcp (stdio)
```

| Tool | |
|---|---|
| `camera_status`, `selftest`, `list_luts` | read only |
| `upload_lut` (grain/colour noise optional), `rename_lut`, `move_lut`, `delete_lut` | LUT Library; delete/replace need `confirm=true` |
| `write_lut_file` | camera-ready `.cube` with header tags, no camera needed |
| `set_photo_style`, `set_white_balance`, `set_exposure`, `set_image_format`, `set_lut_options` | verified by read-back |
| `restore_settings` | undo every setting change made through the server |
| `capture` | shoot + download, returns files and the applied LUT/grain/WB/ISO |

Not possible over USB (as far as tested): choosing the active LUT, P/A/S/M, custom modes, i.Dynamic. Firmware
operations are blocked in the transport. Tests: `python tests/test_offline.py`, with a camera `python tests/live_mcp_test.py [--write]`.

## Quick start (LUT upload)

1. Camera: **Setup → USB Mode → PC (Tether)** (or LUMIX Lab), connect by USB.
2. `pip install -r requirements.txt` (pyusb) and `brew install libusb`.
3. ```sh
   python3 control/lumix_lut.py list
   python3 control/lumix_lut.py push my_look.cube 20 "My Look"
   ```
   The `.cube` needs `#LUMIXPHOTOSTYLE STD` (or another base) on line 2 and at most 33 points.
   Optional header lines: `#GRAINEFFECT L50`, `#COLORNOISE L1`, `#SHARPNESS L60`, `#NOISEREDUCTION L40` (L0–L100).

On macOS the system camera service `ptpcamerad` grabs the camera; the tools kill it before connecting.

## Docs

- [docs/PROTOCOL.md](docs/PROTOCOL.md): PTP vendor commands, LUT Library protocol, property codes, `.cube` tags
- [docs/FINDINGS.md](docs/FINDINGS.md): what we learned the hard way (pitfalls, camera behaviour, measurements)
- [docs/METHOD.md](docs/METHOD.md): how the preset → LUT pipeline works and why
- [docs/CODES.md](docs/CODES.md): all command/parameter code tables
- [docs/SAFETY.md](docs/SAFETY.md): what these tools never do
- [docs/DEVNOTES.md](docs/DEVNOTES.md): how it was built, including dead ends
- [docs/REPRODUCE.md](docs/REPRODUCE.md): verify the protocol against a newer LUMIX Lab yourself
- [docs/FIRMWARE.md](docs/FIRMWARE.md): official firmware link and checksums
- [docs/TESTED.md](docs/TESTED.md): tested cameras (add yours)
- [docs/scans/](docs/scans/): raw property dumps, firmware 1.5 and 2.1
- [examples/](examples/): demo LUTs, start with `identity_std.cube`

Offline test: `python3 tests/test_parse.py`.

## Safety

The tools never use the firmware channel (PTP 0x9606/0x9607) and refuse to. LUT operations only touch the LUT Library.
Still: this is unofficial, use at your own risk, and keep your own copies of every LUT.

## Pipeline requirements

The `pipeline/` scripts render RAWs with LightCraft's command-line renderer (`lightcraft-cli`). Set `LIGHTCRAFT_CLI` and
`LIGHTCRAFT_LIBRARY` if they aren't on the default paths. Python: numpy, scipy, pillow. exiftool for maker notes.

## How the protocol was found

From the PTP command tables and request builders in Panasonic's LUMIX Lab Android app (3.1.0), for interoperability,
then verified against a camera. No Panasonic code, assets or firmware are included in this repository.

## Licence

MIT, see [LICENSE](LICENSE). Not affiliated with Panasonic. LUMIX is a trademark of Panasonic Holdings Corporation.

## Credits

- [libgphoto2](https://github.com/gphoto/libgphoto2): Panasonic PTP property codes and tethering basics
- [sapoepsilon/lumix-remote](https://github.com/sapoepsilon/lumix-remote): Wi-Fi `cam.cgi` notes
- [t0saki/lumix-lut-converter](https://github.com/t0saki/lumix-lut-converter): LUMIX `.cube` format and V-Log/Standard base behaviour
