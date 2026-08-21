#!/bin/sh
# Upstream data the pipeline reads. Not committed -- re-run this to restore.
set -e
mkdir -p vendor
[ -d vendor/apertium-spa-ita ] || \
  git clone --depth 1 https://github.com/apertium/apertium-spa-ita.git vendor/apertium-spa-ita
echo "vendor/ ready"
