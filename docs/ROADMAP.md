# Roadmap

1. LumixOS: run-test with a camera; camera-style HUD (top: Photo Style/LUT, format, WB; bottom: mode, aperture, EV,
   ISO, shutter, remaining shots, battery), each value expanding its options on hover; grid, level line.
2. Server `hud` data: battery (std 0x1015 prop 0x5001), remaining shots (GetParamInfo 0x9414 0x12000010 → 0x12000011),
   mode (0x02000080), histogram/level from the live view header sections (0x17000003, 0x17000005).
3. Photo Style fine-tune props (0x02000012–0x0200001C), LUT 2 (0x020001F8/FA/FC).
4. Gallery download over PTP (0x9911–0x9917) so captures stay on the card.
5. Wi-Fi (cam.cgi / LUMIX Lab's Wi-Fi stream has focus frames).

Known limits: active LUT selection, P/A/S/M, custom modes, i.Dynamic and USB focus-frame position are not available.
