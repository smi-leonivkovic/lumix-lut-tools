# Safety rules

1. **Never** send `camctrl&type=fw_update_mode` or `lens_fw_update_mode`, or any upload whose type is firmware.
   An interrupted or corrupt firmware write can leave the camera unable to boot; only Panasonic service can fix that.
2. Upload commands (`requestsenddata` / `startsenddata` / `senddata` / `endsenddata`) are only used with
   parameters copied from a real, captured LUMIX Lab LUT transfer. No guessing of types or values.
3. Property writes over USB (`0x9403`) only for settings that the camera menu also offers (Photo Style, ISO,
   exposure compensation, ...). Record the old value first and restore it afterwards.
4. Back up before any new kind of write (see [BACKUP.md](BACKUP.md)).
5. `gphoto2 --capture-image-and-download` deletes the file from the card after download. That is fine for test shots,
   but never point it at existing card content.

## Recovery facts

- Camera still boots: reinstall firmware from SD (`.bin` on card root → Setup → Firmware update).
- Camera doesn't boot: Panasonic service. There is no user-side recovery mode.
- Firmware can't be read out of the camera; the backup is the official download.
