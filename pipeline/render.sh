#!/bin/zsh
# render.sh IN OUT [extra lightcraft-cli render args…]
in=$1; out=$2; shift 2
exec "${LIGHTCRAFT_CLI:-lightcraft-cli}" render "$in" -o "$out" \
  --opt bitDepth=16 --opt tiffCompression=none --opt colorSpace=srgb --opt sharpen=none --opt metadata=none "$@"
