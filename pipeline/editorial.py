"""Hand-made decisions the corpus cannot reach, kept as data rather than code.

Four files under content/, each carrying a note column that records what was
done and the evidence for it. None of them show on a card.

  included.csv  words the lexicon's own rules keep out but that belong in it.
  excluded.csv  words in the frozen lexicon that should not become cards.
                The list stays frozen -- these are skipped at build time, so
                nothing is recomputed and nothing churns.
  reverts.csv   rows from the overruled review where the corpus displaced the
                dictionary and was wrong, almost always because it caught a
                fragment of a fixed phrase (`casa` from `casa editrice`).
  overrides.csv the sense list for a word, set outright. For the auxiliaries,
                where co-occurrence measures grammar rather than meaning.
  phrases.json  built, not hand-made, but applied here alongside the rest.
"""
import csv
import os

C = os.path.join(os.path.dirname(__file__), "..", "content")


def _rows(name):
    path = os.path.join(C, name)
    if not os.path.exists(path):
        return []
    return list(csv.DictReader(open(path)))


def included():
    """Words to put in the lexicon that its own rules would keep out.

    One word long, and the file says why it is one word long."""
    return _rows("included.csv")


def excluded():
    """Spanish words to skip entirely -> reason."""
    return {r["spanish"]: r["reason"] for r in _rows("excluded.csv")}


def reverts():
    """(spanish, pos) -> (italian to drop, italian to put in its place)."""
    return {(r["spanish"], r["pos"]): (r["drop"], r["keep"])
            for r in _rows("reverts.csv")}


def overrides():
    """(spanish, pos) -> ordered list of Italian senses, replacing all others."""
    return {(r["spanish"], r["pos"]): r["italian"].split("|")
            for r in _rows("overrides.csv")}
