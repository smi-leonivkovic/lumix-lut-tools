#!/bin/zsh
# copy_to_card.sh FILE... : wait (up to 30 min) for the camera's SD card (a volume with DCIM/), copy FILEs to its root,
# verify each copy by sha256. Never deletes or overwrites anything else on the card.
for i in {1..900}; do
  card=$(for v in /Volumes/*(N); do [[ -d $v/DCIM ]] && echo $v && break; done)
  [[ -n $card ]] && break
  sleep 2
done
[[ -z $card ]] && { echo "no SD card appeared within 30 min"; exit 1; }
echo "card: $card ($(df -h $card | awk 'NR==2{print $4}') free)"
for f in "$@"; do
  dst=$card/${f:t}
  cp "$f" "$dst" && rm -f "$card/._${f:t}" && sync
  a=$(shasum -a 256 "$f" | cut -d' ' -f1); b=$(shasum -a 256 "$dst" | cut -d' ' -f1)
  [[ $a == $b ]] && echo "ok  ${f:t}  sha256 ${a[1,16]}…" || echo "MISMATCH ${f:t}"
done
ls -la $card
