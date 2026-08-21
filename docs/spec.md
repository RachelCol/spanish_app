# spanish_app — design

## The learner

Native English, **C1 Italian**, target **Latin American Spanish**.

This is a course for an audience of one, which is a luxury: no need to
accommodate learners who lack the Italian, and no need to hedge on variety.

## Principle: teach the delta, not the language

Italian and Spanish share roughly 82% lexical similarity and near-identical
grammatical architecture. The course covers only where that breaks down.

**Assumed known, never taught:** gendered nouns and adjective agreement, the
subjunctive as a concept, clitic pronouns as a concept, the preterite/imperfect
aspect distinction, reflexives, ~ser/estar as a concept~ (see below — the
concept transfers, the boundary does not).

**Taught:** everything below.

---

## Module 1 — Transfer rules

Productive orthographic and morphological mappings. Each rule is presented
once, then drilled by generating unseen words that follow it. The learner
should end up able to *derive* vocabulary rather than recall it.

| Italian | Spanish | Rule |
|---|---|---|
| conversazione, nazione | conversación, nación | `-zione` → `-ción` |
| città, libertà | ciudad, libertad | `-tà` → `-dad` |
| chiave, fiamma, piano, pioggia | llave, llama, llano, lluvia | `chi-/fi-/pi-` → `ll-` |
| macellaio, fornaio | carnicero, panadero | `-aio` → `-ero` |
| difficile, possibile | difícil, posible | `-ile` → `-il`/`-ible` |
| studiare, parlare | estudiar, hablar | `-are` → `-ar`, infinitive `-e` drops |
| scuola, scrivere, spagnolo | escuela, escribir, español | `s-` + cons. → `es-` |
| dubbio, doppio | duda, doble | degemination |

Rules carry **confidence** and **exceptions**; the drill surfaces exceptions
only after the rule is solid.

## Module 2 — False friends

The highest-stakes content, because Italian gives *confident* wrong answers.
Ordered by damage potential, not frequency.

| Word | Means in Spanish | Italian says | Severity |
|---|---|---|---|
| burro | donkey | butter | high |
| salir | to leave/go out | salire = to go up | high |
| guardar | to keep/put away | guardare = to look at | high |
| esposa | wife | sposa = bride | medium |
| embarazada | pregnant | imbarazzata = embarrassed | high |
| largo | long | largo = wide | medium |
| aceite | oil | aceto = vinegar | high |
| topo | mole | topo = mouse | low |
| rato | a while | ratto = rat | medium |
| gamba | prawn | gamba = leg | medium |
| prender | to arrest/switch on | prendere = to take | medium |
| subir | to go up | (the `salire` pair, inverted) | high |

Drilled in **context sentences**, never as bare pairs — the trap only fires in
context, so the practice has to.

## Module 3 — Real divergences

Where the systems genuinely differ. Each needs explanation, not just drilling.

**`ser`/`estar` vs `essere`/`stare`.** The concept transfers; the boundary does
not. Italian uses *essere* for states Spanish assigns to *estar*:
`sono stanco` → `estoy cansado`, `sono a casa` → `estoy en casa`.
This is the single most persistent Italian-speaker error.

**The auxiliary collapse.** Spanish has only `haber`. No essere/avere split, no
past-participle agreement with the auxiliary. Strictly a simplification, but
Italian speakers produce `soy ido` for months.

**Preterite vs perfect.** Latin American Spanish uses the preterite where
Italian uses the passato prossimo: `ho mangiato ieri` → `comí ayer`, not
`he comido ayer`. Frequency-critical — it's wrong in nearly every past-tense
sentence until it clicks.

**No geminates.** Spanish has no phonemic doubling. Italian speakers reliably
over-double, and the spelling reinforces it (`dubbio` → `duda`).

**Gender flips.** Cognates that changed gender: `il sangue`/`la sangre`,
`il latte`/`la leche`, `il fiore`/`la flor`.

**Gaps with no Spanish equivalent.** Italian `ne` and `ci` — the risk is
importing them, producing calques that have no target form.

---

## Product shape

**Drill types**
- *Rule application* — given an Italian word, derive the Spanish
- *Trap detection* — a sentence that is plausible-but-Italian; find the error
- *Production* — translate Italian → Spanish, self-graded against a reference
- *Recognition* — Spanish → meaning, for the non-transferring vocabulary

**Scheduling.** Spaced repetition over items, but the *unit* is the rule where
one exists, not the word — the point is generative competence.

**Explicitly not included.** Speaking and listening. Both matter, neither is
served well by a static app; better handled with real audio and real people.

## Data model sketch

Content is authored data, not code — JSON in the repo, versioned, so it can be
regenerated or hand-edited without touching the app.

```
rules:      { id, from_pattern, to_pattern, gloss, examples[], exceptions[], confidence }
falsefriends: { id, es, es_meaning, it, it_meaning, severity, context_sentences[] }
divergences: { id, title, explanation_md, contrasts[], drills[] }
progress:   { item_id, ease, interval, due, lapses }   // localStorage
```

Progress lives in `localStorage` — one learner, one device class, no accounts,
no backend.

## Deliberate later option: AI grading

Free-form production can't be graded well by string comparison. The seam for
that is the *production* drill type: today it self-grades against a reference,
later it can POST to an Apps Script endpoint holding a Claude API key in Script
Properties, returning a structured critique focused on Italian interference.

Nothing else in the design needs to change for that, which is why the drill
types are separated in the first place.
