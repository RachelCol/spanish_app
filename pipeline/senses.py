"""Turn the corpus counts into a definition list, in two stages.

First a filter, then the ratio.

The filter asks whether a word stands out at all. `e` appears beside 48% of
every Spanish word in the deck, so seeing it beside `costa` says nothing;
`cugino` appears beside almost nothing except `primo`. Dividing a word's rate
here by its rate everywhere separates the two, and no hand-written stoplist is
needed -- the corpus says which words are ubiquitous.

Only then does the ratio apply: keep the top surviving translation, and any
other within the chosen percentage of it.
"""
import collections
import json

LIFT = 8.0        # how far above its own baseline a word must stand


def baselines(matrix):
    """How often each Italian word turns up beside a Spanish word, on average."""
    tot = collections.defaultdict(float)
    for e in matrix.values():
        for it, pct in e["it"]:
            tot[it] += pct
    n = max(1, len(matrix))
    return {w: s / n for w, s in tot.items()}


def candidates(matrix, base, es):
    """Italian words that stand out beside `es`, commonest first."""
    e = matrix.get(es)
    if not e:
        return []
    out = []
    for it, pct in e["it"]:
        b = max(base.get(it, 0.01), 0.01)
        if pct / b >= LIFT:
            out.append((pct, it))
    return sorted(out, reverse=True)


def definition(matrix, base, es, relative=15.0):
    """The top translation plus everything within `relative`% of it."""
    cand = candidates(matrix, base, es)
    if not cand:
        return []
    top = cand[0][0]
    return [(it, pct) for pct, it in cand if 100 * pct / top >= relative]
