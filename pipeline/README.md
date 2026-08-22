# pipeline

Generates the deck data in `../data/`. Python only — the app itself has no
build step and just reads the JSON.

## Setup

```sh
python3 -m venv .venv
.venv/bin/pip install wordfreq
./pipeline/fetch.sh
```

## Order

1. `frequency.py` — Spanish frequency spine from wordfreq, banded into tiers,
   with the top-200 closed-class layer cut. Writes `data/frequency_es.json`.
2. `build_pairs.py` -- joins the spine to the Apertium senses and writes
   `data/paired.json`.
3. `build_sentences.py` -- example sentences from Tatoeba, matched to deck
   words by lemma and scored so short sentences built from common words win.
   Needs `spacy` and the `es_core_news_md` model. Writes `data/sentences.json`.
4. `pairs.py` — Spanish→Italian lemma pairs from Apertium. Membership in this
   dictionary doubles as the citation-form test, which is how the spine gets
   filtered to lemmas without a lemmatizer.

## Two things that are not obvious

**Cross-language frequency only means something after pairing.** Comparing the
Zipf of `mayoría` against the Italian string `mayoría` measures orthographic
coincidence, not difficulty. It has to be compared against `maggioranza`.

**Frequency mismatch is a correctness signal.** A pair whose Italian side is
much rarer than its Spanish side is usually a bad translation — Apertium is MT
data and carries domain-skewed senses (`madre` → `staminale`, from *célula
madre*). Flagging `zipf_es - zipf_it >= 1.2` catches ~3% of pairs at close to
100% precision. It does not catch wrong-but-common pairs, so it filters the
obvious garbage rather than proving anything.
