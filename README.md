# puente

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

## Status

Early. See [docs/spec.md](docs/spec.md) for the design.

## Stack

Static site — Svelte + Vite, PWA for offline phone use, deployed to GitHub
Pages. No backend and no API key: the curriculum is authored content committed
to the repo, so the app costs nothing to run and works on a plane.

A Claude-backed grader for free-form production is a deliberate later option;
the content layer is shaped so it can slot in without a rewrite.
