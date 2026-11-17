#!/bin/zsh
f=$1; b=${${f:t}:r}
$CAM_T/render.sh $f $CAM_OUT/${b}_lc.tif --settings $CAM_SET --library "${LIGHTCRAFT_LIBRARY:-$HOME/Pictures/LightCraft Library}" >/dev/null 2>&1 || echo "fail $f"
