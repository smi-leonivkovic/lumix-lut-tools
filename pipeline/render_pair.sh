#!/bin/zsh
# render_pair.sh RW2 -> $PAIR_OUT/<name>_def.tif and _pre.tif (768px long edge)
f=$1; b=${${f:t}:r}; d=${${f:h}:t}
for kind set in def $PAIR_DEF pre $PAIR_PRE; do
  o=$PAIR_OUT/${d}_${b}_$kind.tif
  [[ -s $o ]] || $PAIR_T/render.sh $f $o --settings $set --size 768 --library "${LIGHTCRAFT_LIBRARY:-$HOME/Pictures/LightCraft Library}" >/dev/null 2>&1 || echo "fail $f $kind"
done
