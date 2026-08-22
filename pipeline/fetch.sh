#!/bin/sh
# Upstream data the pipeline reads. Not committed -- re-run this to restore.
set -e
mkdir -p vendor
[ -d vendor/apertium-spa-ita ] || \
  git clone --depth 1 https://github.com/apertium/apertium-spa-ita.git vendor/apertium-spa-ita
echo "vendor/ ready"

# Tatoeba: Spanish and Italian sentences plus the links between them.
mkdir -p vendor/tatoeba
base="https://downloads.tatoeba.org/exports/per_language"
for f in "spa/spa_sentences" "ita/ita_sentences" "spa/spa-ita_links"; do
  out="vendor/tatoeba/$(basename $f).tsv"
  [ -f "$out" ] || { curl -s "$base/$f.tsv.bz2" | bunzip2 > "$out"; echo "fetched $out"; }
done
