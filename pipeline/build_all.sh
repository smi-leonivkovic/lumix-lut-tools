#!/bin/zsh
# build_all.sh LIST.tsv  (preset_id<TAB>name per line) -> luts/LC_<name>.cube for each, log in data/build_all.log
R=${0:a:h:h}
while IFS=$'\t' read -r id name; do
  echo "== $name"; $R/pipeline/build_look.sh $id $name 2>&1 | grep -E 'held-out|wrote'
done < $1
