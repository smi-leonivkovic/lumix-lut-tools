# How a preset becomes a LUT

## Camera side

- S9 Real Time LUT: `.cube`, up to 33 points, header `#LUMIXPHOTOSTYLE STD` so the LUT sits on Standard
  (allows ISO 100; a V-Log base forces a high base ISO). Up to 39 LUTs in the LUT Library.

## Why not just apply the preset to JPEG colours

LightCraft presets are tuned for RAW. Applying a preset to a JPEG-like grid gave a flat, blotchy look about
26/255 away from the same preset on the RAW. So the LUT maps **camera Standard JPEG → preset on RAW**:

    final = F ∘ G
    G: camera Standard JPEG  → LightCraft default render   (from RAW+JPEG pairs of real scenes)
    F: LightCraft default    → LightCraft preset render    (from many RW2s rendered both ways)

## F (preset)

- 120 S9 RW2s (every 22nd file from the card), rendered at 768 px with `render_pair.sh`:
  default settings vs preset + `settings/nospatial.json` (sharpen, NR, clarity, dehaze, texture, grain,
  vignette, lens corrections off; a LUT can't do spatial effects).
- `fit_lut.py`: regularised least squares on the 33³ grid, trilinear weights + λ·second differences +
  μ·(L − prior), solved with scipy `splu`. λ picked on a holdout. Held-out error ≈ 1.9/255.

## Grid extraction (for pure per-pixel presets)

`lutgrid.py make/read`: 33³ colours in 64 px patches, 16×16 per 1024 px image, 141 images.
Shadows/Highlights in LightCraft are local (guided filter, σ = 1.5 % of long edge, eps 0.35), so patches must be
**luminance-sorted**; then grid renders match flat fields to 0.00.

## G (camera)

Fit from RAW+JPEG pairs of real scenes shot in **Standard**, no monitor charts (a screen's gamut and flicker make a poor
reference). `control/tether_pairs.py` shoots the scene in front of the camera over an exposure sweep (optionally white
balance too), Standard and the LUT slot back to back, restoring settings afterwards. `pipeline/align_pairs.py` aligns
camera JPEG and LightCraft default render, `pipeline/fit_g.py` fits G with hold-out by white balance or exposure (`--key`).

On an S9, camera Standard and LightCraft's default render were only ~4/255 apart, so G is a small correction.
i.Dynamic Range changes the JPEG locally; fit G with the i.Dynamic setting you will shoot with.

## Rendering

```
lightcraft-cli render IN -o OUT --settings JSON --size N --library DIR \
  --opt bitDepth=16 --opt tiffCompression=none --opt colorSpace=srgb --opt sharpen=none --opt metadata=none
```
`pipeline/render.sh` wraps this (zsh doesn't word-split `$OPTS`).
