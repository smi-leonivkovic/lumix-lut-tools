# Development notes

How this came together, in order, including the dead ends. Conclusions are in [FINDINGS.md](FINDINGS.md).

1. **Goal:** photo-editor presets as in-camera looks on a LUMIX S9 (Real Time LUT, 33-point `.cube`, Standard base).
2. **Grid extraction.** Render a 33³ colour grid through the editor and read the LUT back. Exact for per-pixel tools,
   but the editor's Highlights/Shadows are local (guided filter), so patches had to be sorted by luminance.
3. **Wrong domain.** Grid LUTs applied the preset to JPEG-like colours: flat and blotchy, ~26/255 from the preset on
   the RAW. Switched to fitting from RAW pairs (default render → preset render), regularised least squares on the grid.
4. **Camera correction.** First attempt used old RAW+JPEG pairs: invalid, they were shot with a LUT and grain applied
   (the maker note's `LUT1Name` told us). Monitor charts were dropped (gamut, flicker). Tethered real-scene pairs worked;
   camera Standard turned out ~4/255 from the editor's default render.
5. **USB control.** gphoto2 + Panasonic vendor ops from libgphoto2. Photo Style refused writes on its own property;
   the "param" twin 0x02000011 worked. Mapped all Photo Style codes by shooting each and reading the maker note.
6. **Tether hiccups.** macOS `ptpcamerad` grabbing the camera; an interrupted transfer hung the camera's USB stack
   (replug fixed it); a capture in a video custom mode recorded a clip instead of a photo.
7. **Firmware 1.5 → 2.1** from the SD card. 2.0 added LUMIX Lab wired connection and LUT extras.
8. **Lens-correction bug.** Default render with lens correction, preset render without → misaligned training pairs,
   16/255 error. Same geometry in both → 1.5/255.
9. **Local tone.** Presets with strong Highlights/Shadows stayed ~5/255 off. Camera i.Dynamic Range (High) took over
   part of that work; refitting for it helped a little more. A direct refine on one scene overfitted and was rejected.
10. **Getting LUTs in without the app.** Wi-Fi capture via the iPhone was the plan, then the Android emulator. The
    Play Store refused the app (requires USB host). Downloaded the real Play build, but the more useful step was reading
    its code: dedicated LUT commands (0x9921–0x9924), separate from the firmware channel.
11. **First upload broke the looks.** Sent 60 KB chunks; the camera kept only the last one → no header, base style
    none, LUT on V-Log. The app sends the whole file in one transfer over USB. Fixed, re-uploaded in place.
12. **Library housekeeping.** Reorder (positions 0–1 locked), rename, delete (leaves gaps; close them by sorting).
13. **Too cool.** Several presets set an absolute white balance (5256 K). A LUT can't set Kelvin; the fit turned it into
    a cool/magenta cast. Rebuilt with WB as shot and set the camera to a fixed 5300 K instead.
14. **Variants.** "Bright" (luminance pre-curve with a soft shoulder) and "Soft" (70% blend with identity) looks.
