#!/bin/zsh
# capture_lumixlab.sh [OUTDIR]
# Record everything the iPhone sends/receives while LUMIX Lab transfers one LUT to the camera.
# iPhone on USB (unlocked, "Trust this computer"). Uses Xcode's rvictl: the phone's traffic appears on the Mac as rvi0.
# Run with sudo (tcpdump needs it):  sudo control/capture_lumixlab.sh
# Stop with Ctrl-C after the LUT shows up on the camera.
UDID=${UDID:?set UDID to your iPhone id (xcrun devicectl list devices)}
OUT=${1:-${0:a:h:h}/data/capture}
mkdir -p $OUT
f=$OUT/lumixlab_$(date +%Y%m%d_%H%M%S).pcap
rvictl -s $UDID || { echo "rvictl failed: is the iPhone plugged in, unlocked and trusted?"; exit 1; }
trap 'rvictl -x $UDID >/dev/null; echo; echo "saved $f"; ls -la $f' EXIT INT
echo "Recording to $f"
echo "Now on the iPhone: LUMIX Lab -> connect to the S9 -> send one LUT (e.g. LC_A1-Snappy). Ctrl-C when done."
# full packets, all traffic (camera is 192.168.54.1 on its own AP; BLE is not visible here)
tcpdump -i rvi0 -s 0 -w $f
