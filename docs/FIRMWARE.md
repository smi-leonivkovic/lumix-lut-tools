# Firmware notes (DC-S9)

Official downloads only: <https://av.jpn.support.panasonic.com/support/global/cs/dsc/download/ff/dl/s9.html>
(Panasonic offers only the newest version). Never install firmware from anywhere else, and these tools never send it.

| File | Size (bytes) | SHA-256 |
|---|---|---|
| `S9___V21.zip` (Ver. 2.1, Oct 2026) | 152,907,156 | `6187173be784c32bdb55258b80a01822d61606ad8e64ed12c831dc6275051052` |
| `S9___V21.bin` (inside the zip) | 172,915,712 | `598585177df951c760583f05ee36c742a79eb3ace598b6a88a1f2149b2b9f294` |

Install: `.bin` on the card root → Setup → Firmware Version, full battery. On macOS delete the `._S9___V21.bin`
AppleDouble file Finder may create on the card. Updating via the LUMIX Lab app was suspended by Panasonic for 2.0.
Changes relevant here: 2.0 added LUMIX Lab wired connection and LUT extras (grain/colour noise for photos, sharpness, NR).
