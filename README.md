# spanish_app

A Spanish course for someone who already speaks Italian.

Built for one learner: a native English speaker at **C1 Italian**, learning
**Latin American Spanish**. Every design decision follows from that.

## Why this exists

General Spanish courses assume you're starting from English. From Italian,
most of the vocabulary and roughly all of the grammatical machinery — gender,
clitics, the subjunctive, the tense system — already transfers. Marching
through `la casa = house` wastes the ~85% you get for free and never gets to
the part that actually trips you up.

This app inverts that. It teaches:

1. **Transfer rules** — the systematic Italian→Spanish mappings, so one rule
   unlocks hundreds of words
2. **False friends** — the dangerous minority where Italian actively misleads
3. **Real divergences** — `ser`/`estar`, the auxiliary collapse, preterite vs
   perfect, no geminates

And deliberately skips everything that carries over intact.

## Sections

**Flashcards** — the vocabulary deck, spaced repetition, example sentences and
conjugation tables.

**Grammar** — *Comparisons*, eighteen lessons on what Italian gets wrong about
Spanish, ordered by how much trouble each causes. *Basics*, a plain outline of
how Spanish works, in English, including the preposition mapping.

**Drills** — *Verbs*, typed conjugation drills over the fifty commonest verbs.
*Prepositions* and *Articles*, gap-fill against real Tatoeba sentence pairs.

## Status

Early. See [docs/spec.md](docs/spec.md) for the design.

## Data

Vocabulary pairs come from [Apertium](https://github.com/apertium/apertium-spa-ita),
frequency from [wordfreq](https://pypi.org/project/wordfreq/), and example
sentences from [Tatoeba](https://tatoeba.org) under CC BY 2.0 FR.

## Stack

Static site — Svelte + Vite, PWA for offline phone use, deployed to GitHub
Pages. No backend and no API key: the curriculum is authored content committed
to the repo, so the app costs nothing to run and works on a plane.

A Claude-backed grader for free-form production is a deliberate later option;
the content layer is shaped so it can slot in without a rewrite.

## Two builds

`/` is the app. `classic/` is a frozen copy of how it worked before the
Italian-first refactor, kept so the old behaviour stays referenceable.

| | app | classic |
|---|---|---|
| direction | Italian → Spanish only | both, scheduled separately |
| deck driven by | `data/prompts.json` | `data/collisions.json` |
| IndexedDB | `spanish_app_v2` | `spanish_app` |
| cache | `spanish-app-vN` | `spanish-classic-v1` |

They share an origin, so the database names must differ or the two would share
progress. `classic/` keeps the original name because that is where the
existing history lives; the app starts fresh alongside it.

`stable-v56` tags the code as it stood before the refactor.

## Experimenting

`python pipeline/make_lab.py --recreate` copies the app into `lab/` as a third,
independently installable build to try disruptive changes in. A plain run only
rebuilds generated data and leaves `lab/` app code alone.

## Reviewing the pairings yourself

    python pipeline/export_review.py

writes `review.csv` -- every pairing in the deck, ordered by frequency band,
with the cross-check's verdict beside it and two empty columns.

Open it in Google Sheets (File > Import > Upload). Fill in:

| column | what it does |
|---|---|
| `call` | `drop` removes that Italian sense from that Spanish card. Anything else leaves it alone. |
| `note` | free text; read, never applied automatically |

Then File > Download > Comma-separated values, save it as `content/review.csv`,
and re-run the pipeline. Your calls are applied on every build from then on,
and `export_review.py` carries them forward into the next export so nothing is
retyped.

`review.csv` in the project root is a generated scratch file and is ignored by
git; `content/review.csv` is the reviewed one and is committed.

Corrections are deliberately not applied from the sheet. Removing a sense can
only cost a card; asserting one can teach a wrong word, which is how
`dovere -> tener` shipped. Put those in `note` and they get checked first.
