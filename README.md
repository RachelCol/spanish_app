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

## The lab build

`lab/` is a second, independently installable copy of the app, for changes too
disruptive to make in the one you use daily. Rebuild it from main with:

    python pipeline/make_lab.py

Three things deliberately diverge, and nothing else:

| | main | lab |
|---|---|---|
| IndexedDB | `spanish_app` | `spanish_app_lab` |
| cache | `spanish-app-vN` | `spanish-lab-vN` |
| manifest id | *(none)* | `spanish-from-italian-lab` |

They share an origin, so without the first of those the two copies would share
your progress and a schema change in the lab would migrate your real data.

To carry your progress across, Export from one and Import into the other --
the file format is the same.

`stable-v56` tags the app as it stood before the Italian-first experiments.
