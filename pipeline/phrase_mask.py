"""Hide fixed phrases from the word counters.

`pesar` occurs 17,224 times in eight million lines and 95% of those are
`a pesar de`. Counting them all against the bare word gave it `nonostante`
at 39.2% and `pesare` at 0.4% -- the card said "despite" for a verb that
means "to weigh". The phrase is a card of its own, so its occurrences belong
to the phrase and not to the word inside it.

Masking rather than skipping the line: `de repente se puso a llover` still
counts `poner` and `llover`, it just stops counting `repente`.
"""
import json
import re


def load(path="data/phrases.json"):
    try:
        phrases = json.load(open(path))
    except FileNotFoundError:
        return None
    if not phrases:
        return None
    # longest first, so `de vez en cuando` is taken before `vez`
    keys = sorted(phrases, key=len, reverse=True)
    return re.compile(r"\b(?:" + "|".join(re.escape(k) for k in keys) + r")\b",
                      re.IGNORECASE)


def masker(path="data/phrases.json"):
    """Returns a function that blanks locked phrases out of a Spanish line."""
    rx = load(path)
    if rx is None:
        return lambda line: line
    return lambda line: rx.sub(" ", line)
