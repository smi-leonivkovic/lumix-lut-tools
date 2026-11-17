#!/bin/zsh
f=$1; b=${f:t}
$LUT_T/render.sh $f $LUT_RD/${b/grid_/out_} --settings $LUT_SETTINGS >/dev/null 2>&1 || echo "render failed: $f"
