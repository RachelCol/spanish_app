# How the deck is built

This is the agreed design. **Do not change it without asking first** — it is
the record of decisions made deliberately, several of them after an earlier
approach turned out to be wrong.

## 1 · Spanish frequency list

- Lemmatised to base forms only: singular nouns, infinitive verbs, masculine
  singular adjectives. `costa`, never `costas`.
- May include fixed multiword phrases that always hold together. Not sentences.
- **Each word tagged with its part(s) of speech.** A word may have several —
  noun *and* adjective.
- The part-of-speech inventory comes from **Wiktionary, not Apertium**.
  Apertium is why `hecho` was marked noun-only for weeks despite being a noun
  and an adjective.

## 2 · Italian definitions for each Spanish word

- Find aligned sentence pairs containing the Spanish base form, **exact match**.
- Count the Italian words **exactly** — no stemming, no lemmatising.
  `costa` and `costo` are different words and never merge. Matching the
  Spanish singular keeps the Italian side singular too, so plurals do not
  need handling: measured, `costa` alone gives `costa` 49% with `coste`
  absent, where including `costas` drags `coste` in at 4%.
- Skip capitalised Italian tokens unless the Spanish word is itself a proper
  noun. Otherwise `costa` acquires *Rica* as a meaning.
- Require the Italian token to have real currency in Italian, by Italian
  frequency. This keeps `leader`, `account`, `staff` and `trend`, which
  Italians genuinely say, and drops untranslated English in subtitle files.
- Keep the top translation, plus any scoring **at least 10–15% relative to
  it**. `costo` scores 7% relative to `costa`, so the two stay apart on their
  own.
- **Each Italian word carries its own part-of-speech tag.** Used for mapping
  backwards in step 3; not necessarily shown.
- **The definition is organised by the *Spanish* word's parts of speech** —
  which Italian word translates it as a noun, which as an adjective. At least
  one per Spanish part of speech.
- **If a Spanish part of speech has no attested translation, drop that part of
  speech from the word** and write it to a review list — word, and what was
  dropped — so nothing important disappears unnoticed.

## 3 · The Italian list

- Every Italian word used in any definition, carried across. No new Italian
  words are sought: the point is to reach the most-used Spanish words through
  Italian words already known.
- For each, all the Spanish words that mapped to it. **Nothing is trimmed on
  frequency in this direction** — a Spanish word we set out to learn cannot be
  lost here.
- **Ordered by frequency**, measured from sentence pairs starting from the
  Italian word, each marked with its percentage.
- If a Spanish word *not* on the list translates that Italian word above the
  threshold, **add it** with its percentage, but give it no detail card.
  Tapping it says *"No card for this one — it's outside your deck."*
  Otherwise generating detail cards never terminates.

## 4 · Cards

- Flashcards run **Italian → Spanish**, from the step 3 list.
- Tapping a Spanish answer opens its detail card, from the step 2 list, with
  the Italian definitions **grouped by that Spanish word's parts of speech**.
- **Percentages are shown on both** the flashcard back and the detail card.
- The percentage is of *all* pairs containing the word, including those where
  Italian phrased it differently. A low top score is information: it means the
  sentence is usually restructured. Because the threshold is relative, the
  choice of denominator does not affect which words are included.

## Throughout

Every rebuild reports what moved — cards gained and lost, definitions
rewritten, parts of speech changed, prompts that can no longer be asked:

    python pipeline/changes.py

## Sources

| what | source |
|---|---|
| Spanish and Italian frequency | wordfreq |
| parts of speech, and a second opinion on meaning | English Wiktionary via kaikki.org |
| sentence pairs for the counts | OPUS — OpenSubtitles and Europarl, 32.5M aligned pairs |
| example sentences on cards | Tatoeba, CC BY 2.0 FR |
| conjugation tables | verbecc |

Apertium's bilingual dictionary built the original deck and is being replaced
by the corpus counts above. Its direction markers (`LR`/`RL`) are **not** a
quality signal — tested twice, filtering on them would have removed
`dopo → luego`, `ciao → hola` and `caffè → café`.

## Open decisions

- The threshold: 10% or 15%, to be chosen from the measured distribution.
- Whether one threshold suits function words and nouns alike. Probably not.
