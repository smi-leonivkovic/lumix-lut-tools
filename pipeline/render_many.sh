#!/bin/zsh
# render_many.sh SETTINGS OUTDIR SUFFIX SIZE FILE...   -> OUTDIR/<name>SUFFIX.tif, 6 in parallel, skips existing
# (xargs -I can't hold the long command, so each file goes through this script with -n 1)
if [[ $1 == --one ]]; then
  f=$2; o=$OUTDIR/${${f:t}:r}$SUFFIX.tif
  [[ -s $o ]] || ${0:h}/render.sh $f $o --settings $SETTINGS --size $SIZE --library "${LIGHTCRAFT_LIBRARY:-$HOME/Pictures/LightCraft Library}" >/dev/null 2>&1 || echo "fail $f"
  exit 0
fi
export SETTINGS=$1 OUTDIR=$2 SUFFIX=$3 SIZE=$4; shift 4
mkdir -p $OUTDIR
print -rN -- "$@" | xargs -0 -n 1 -P 6 ${0:a} --one
