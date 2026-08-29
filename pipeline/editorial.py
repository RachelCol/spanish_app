"""Hand-made decisions the corpus cannot reach, kept as data rather than code.

Four files under content/, each carrying a note column that records what was
done and the evidence for it. None of them show on a card.

  included.csv  words the lexicon's own rules keep out but that belong in it.
  see_also.csv  a phrase to mention under a word whose other use lives in it.
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

# Which parts of speech are taught in a section rather than on a card. Kept
# here because it was copied into three pipeline scripts and they drifted:
# build_deck2 still sectioned prepositions after the other two had stopped, so
# `de`, `en`, `por` and eleven more had definitions and no card.
SECTIONED = {"det", "ij", "prn", "cnj"}

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


def see_also():
    """spanish -> the phrase its other use lives in, shown under the card.

    Some words are a card in one part of speech and a preposition only inside
    a fixed phrase: `dado` is a noun and `dado que` is the conjunction, `junto`
    is an adjective and `junto a` is the preposition. Teaching the phrase as
    its own card would be wrong -- you meet these as phrases, not as words --
    but leaving the use unmentioned loses it.
    """
    return {r["spanish"]: r for r in _rows("see_also.csv")}


def excluded():
    """Spanish words to skip entirely -> reason."""
    return {r["spanish"]: r["reason"] for r in _rows("excluded.csv")}


def reverts():
    """(spanish, pos) -> (italian to drop, italian to put in its place).

    One revert per reading: a second row for the same word and part of speech
    replaces the first rather than adding to it. Two rows for `hasta` as a
    preposition looked like they would drop two words and instead undid each
    other, letting `pure` back onto the card. To change several senses of one
    reading, state it outright in overrides.csv.
    """
    out = {}
    for r in _rows("reverts.csv"):
        key = (r["spanish"], r["pos"])
        if key in out:
            raise SystemExit(
                f"reverts.csv has two rows for {key}; only one would apply. "
                f"Use overrides.csv to state that reading outright.")
        out[key] = (r["drop"], r["keep"])
    return out


def overrides():
    """(spanish, pos) -> ordered list of Italian senses, replacing all others."""
    return {(r["spanish"], r["pos"]): r["italian"].split("|")
            for r in _rows("overrides.csv")}
