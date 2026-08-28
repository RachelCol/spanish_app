"""Matching Spanish words in corpus text without merging distinct ones.

Stripping accents to be forgiving of corpus spelling merges 34 pairs the
language keeps apart -- `que`/`qué`, `el`/`él`, `más`/`mas`, `si`/`sí`, and
`año`/`ano`, which is how the word for "year" came to have no corpus data at
all. So the exact form is always matched, and the accent-free form is matched
too only where nothing else claims it.
"""
import collections
import unicodedata


def strip(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def build(words):
    """token -> the word it means, for exact and unambiguous loose forms."""
    look = {}
    for w in words:
        look[w.lower()] = w
    bare = collections.defaultdict(set)
    for w in words:
        bare[strip(w)].add(w)
    for b, owners in bare.items():
        if len(owners) == 1 and b not in look:
            look[b] = next(iter(owners))
    return look
