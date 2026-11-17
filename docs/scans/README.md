# Property scans (DC-S9)

Read-only dumps of every Panasonic property answering GetProperty (0x9402), made with `control/lumixctl.py scan`.
Format: `property  [name]  size=N value=V`. Values are camera state at the time (photo mode, aperture priority,
Photo Style = LUT slot), useful to diff against your own camera after changing one setting.

| File | Firmware | USB mode |
|---|---|---|
| props_fw1.5_tether.txt | 1.5 | PC (Tether) |
| props_fw2.1_tether.txt, props_fw2.1_tether_b.txt | 2.1 | PC (Tether), two moments |
| devinfo_fw2.1_lumixlab_mode.txt | 2.1 | LUMIX Lab (`control/devinfo.py`) |

Diff the two firmware scans to see the ~37 properties 2.1 added.
