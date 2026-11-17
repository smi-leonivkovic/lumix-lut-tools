#!/bin/zsh
# build_lut.sh GRIDDIR SETTINGS.json OUT.cube TITLE  -> renders every grid image with SETTINGS, reads the LUT
set -e
grid=$1; settings=$2; out=$3; title=$4
T=${0:A:h}; rd=$(mktemp -d "${out:h}/render.XXXX")
export LUT_RD=$rd LUT_SETTINGS=$settings LUT_T=$T
ls $grid/grid_*.tif | xargs -n 1 -P 6 $T/render_one.sh
n_in=$(ls $grid/grid_*.tif | wc -l); n_out=$(ls $rd/out_*.tif | wc -l)
[[ $n_in -eq $n_out ]] || { echo "only $n_out of $n_in renders succeeded"; exit 1; }
python3 -I $T/lutgrid.py read $rd $grid/layout.json $out --title "$title"
rm -rf $rd
