#!/bin/zsh
# build_look.sh PRESET_ID NAME [RW2LIST]
#   1. export the LightCraft preset, switch spatial effects off  -> settings/NAME.lcpreset, NAME_nospatial.json
#   2. render the training RAWs with defaults (shared) and with the preset (768 px)
#   3. fit F (default -> preset) -> luts/work/NAME_F.cube
# Final camera LUT = F ∘ G, composed by compose_look.py.
set -e
R=${0:a:h:h}; id=$1; name=$2; list=${3:-$R/data/fset_rw2.txt}
CLI=${LIGHTCRAFT_CLI:-lightcraft-cli}
$CLI run --library "${LIGHTCRAFT_LIBRARY:-$HOME/Pictures/LightCraft Library}" preset.export path=$R/settings/$name.lcpreset "ids=[\"$id\"]" >/dev/null
python3 -I $R/pipeline/preset_settings.py $R/settings/$name.lcpreset $R/settings/nospatial.json $R/settings/${name}_nospatial.json
files=( ${(f)"$(<$list)"} )
$R/pipeline/render_many.sh $R/settings/default_nospatial.json $R/data/fset/def _def 768 $files
$R/pipeline/render_many.sh $R/settings/${name}_nospatial.json $R/data/fset/$name _pre 768 $files
P=$R/data/fset/pairs_$name; rm -rf $P; mkdir -p $P
for d in $R/data/fset/def/*_def.tif; do
  b=${${d:t}%_def.tif}; [[ -s $R/data/fset/$name/${b}_pre.tif ]] || continue
  ln -s $d "$P/${b}_def.tif"; ln -s $R/data/fset/$name/${b}_pre.tif "$P/${b}_pre.tif"
done
mkdir -p $R/luts/work
python3 -I $R/pipeline/fit_lut.py $P $R/settings/identity33.cube $R/luts/work/${name}_F.cube --title "$name F"
# 4. compose with the camera correction G -> final camera LUT
python3 -I - "$R" "$name" <<'PY'
import sys; R, name = sys.argv[1:3]; sys.path.insert(0, f'{R}/pipeline')
import numpy as np, lutgrid as L
nF, F = L.load_cube(f'{R}/luts/work/{name}_F.cube'); nG, G = L.load_cube(f'{R}/luts/work/G_tether1.cube')
L.write_cube(f'{R}/luts/LC_{name}.cube', np.clip(L.apply_lut(F, nF, G[None])[0], 0, 1), nG, f'LC {name}', 'STD')
print(f'wrote luts/LC_{name}.cube')
PY
