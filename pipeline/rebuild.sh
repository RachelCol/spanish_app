#!/bin/sh
# Rebuild the deck from the corpus, in the one order that is correct.
#
# Two dependencies are easy to get wrong and both have cost us a shipped deck:
#
#   build_shares reads data/definitions.json to decide what to count, and
#   build_definitions reads data/shares.json for the percentages it prints.
#   That is a cycle, so definitions is built twice: once to name the pairs
#   worth counting, and again on the counts. Skipping the second pass leaves
#   every percentage stale; skipping the first leaves new pairs uncounted and
#   showing 0%, which is how `mas -> piu` came to claim a measured zero when
#   it is 52.5%.
#
#   build_sentences_paired reads data/deck.json, so examples come last. An
#   example is only kept when the Italian half contains one of the card's
#   senses, and the senses are not final until the deck is.
#
# Usage:  sh pipeline/rebuild.sh <corpus-dir> <wikt-it2es.json> <wikt-dir>
#
# <wikt-dir> holds kaikki's it-en.jsonl and es-en.jsonl, used only for the
# cross-check, which reads meaning through English and changes no card.
set -e
CORPUS="$1"
WIKT="$2"
WDIR="$3"
PY="${PY:-.venv/bin/python}"
export PYTHONPATH=pipeline

step() { printf '\n=== %s\n' "$1"; }

step "wordlist superset of the lexicon"
$PY pipeline/sync_wordlist.py

step "alignment over lemma|POS tokens"
$PY pipeline/align_tagged.py "$CORPUS"

step "co-occurrence matrix"
$PY pipeline/build_matrix.py "$CORPUS"

step "fixed phrases counted as units"
$PY pipeline/build_phrases.py "$CORPUS"

step "definitions, first pass -- names the pairs worth counting"
$PY pipeline/build_definitions.py "$WIKT"

step "exact share of each pair, over the whole corpus"
$PY pipeline/build_shares.py "$CORPUS"

step "definitions, second pass -- now on real counts"
$PY pipeline/build_definitions.py "$WIKT"

step "the Italian list"
$PY pipeline/build_italian.py

step "the deck"
$PY pipeline/build_deck2.py

step "example sentences"
$PY pipeline/build_sentences_paired.py

step "cross-check against English Wiktionary"
[ -n "$WDIR" ] && $PY pipeline/build_crosscheck.py \
    "$WDIR/it-en.jsonl" "$WDIR/es-en.jsonl" || true

step "what moved"
$PY pipeline/changes.py || true
