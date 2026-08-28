"""The lexicon: the 3,000 Spanish words this course teaches. Built once.

Membership has been recomputed on every run so far, from wordfreq's ranking,
Wiktionary's judgement about base forms, and -- worst of all -- whether a
definition happened to be found. Change any rule and the deck's contents move,
which is why words kept falling out and coming back.

So this writes content/lexicon.csv once and is not meant to run again. The file
is committed and edited by hand thereafter. Definitions may change freely; what
words the course covers does not. A word that cannot be defined stays on the
list as a visible gap rather than vanishing.

    python pipeline/build_lexicon.py <kaikki-es.jsonl>     # once
"""
import csv
import os
import re
import sys

from wordfreq import top_n_list, zipf_frequency

sys.path.insert(0, "pipeline")
from build_wordlist import read_wiktionary, POS_MAP, singular_of  # noqa: E402

# A conjugated form earns a place only on a real noun or adjective reading.
# Wiktionary gives many of them a marginal interjection -- `puede` is listed as
# "it's possible", `va` as "okay", `sé` as "yes", `he` as a Hebrew letter --
# and accepting those put 181 verb forms in a list meant to hold `tener`, not
# `tengo`. `era`, `trabajo` and `cuenta` stay: those are genuine nouns.
SUBSTANTIAL = {"n", "adj", "vblex"}

# Articles are not worth drilling: an Italian speaker does not need a card to
# learn that `el` is `il`. Dropped as a class rather than one at a time.
ARTICLES = {"el", "la", "los", "las", "un", "una", "unos", "unas", "lo"}

# Names of letters and notes. Wiktionary lists `de` as "the name of the Latin
# script letter D", `te` as T, `la` as the sixth note of the scale -- readings
# that keep a function word alive as a noun and belong nowhere near a deck.
LETTERISH = re.compile(
    r"^(the name of the|name of the).*(letter|character)|"
    r"letter [א-ת]|"
    r"\((?:first|second|third|fourth|fifth|sixth|seventh) note of the scale\)",
    re.I)

# Nouns that coincide with a verb form stay -- `casa`, `agua`, `mano`, `paso`,
# `pasa` the raisin. What goes is a past participle riding in on an adjective
# reading, since `llegado` and `creado` add nothing beside `llegar` and
# `crear`. Judged by whether the word's only reading is an adjective that
# Wiktionary calls a participle of a verb already on the list.
PARTICIPLE_ONLY = True

# Inflected forms that survive on a marginal noun reading, and are not worth a
# card beside the base they inflect: `son` a musical style beside `ser`, `haya`
# a beech tree beside `haber`, `nueva` as "news" beside `nuevo`. Judged by hand
# because no rule separates them from `falta` and `pasa`, which are ordinary
# nouns that merely look like inflections. Add to this list as more turn up.
BY_HAND_OUT = {
    "son", "haya", "nueva", "buena", "primera", "segunda", "poca",
    "deja",    # a textile remnant, per Wiktionary, beside `dejar`
    "pasa",    # a raisin, but the corpus sees only the verb: it defined as `che`
    "queda",   # a curfew, likewise: defined as `la, chiusa`
    "trata",   # trade, likewise
    "van",     # the vehicle, beside `ir`
    "he",      # a Hebrew letter, beside `haber`
}

SIZE = 3000
OUT = "content/lexicon.csv"

# Frequency bands, cut so each is a sensible chunk of 3,000 rather than by
# absolute Zipf, which put 22 words in one band and 1,700 in another.
BANDS = [(0, 300, "first"), (300, 800, "core"), (800, 1500, "common"),
         (1500, 2200, "useful"), (2200, 3000, "wider")]


def letter_names(path, lang="es"):
    """word -> the parts of speech whose only reading is a letter or note."""
    import collections
    import json
    lettery = collections.defaultdict(set)
    other = collections.defaultdict(set)
    for line in open(path, errors="ignore"):
        if '"word"' not in line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("lang_code") != lang:
            continue
        pos = POS_MAP.get(r.get("pos"))
        if not pos:
            continue
        for s in r.get("senses") or []:
            g = (s.get("glosses") or [""])[0]
            if not g or s.get("form_of"):
                continue
            (lettery if LETTERISH.search(g) else other)[r["word"]].add(pos)
    return {w: v - other.get(w, set()) for w, v in lettery.items()}


def feminine_forms(path, lang="es"):
    """Words whose ADJECTIVE reading is the feminine of something.

    Adjectives are wanted in the masculine singular, so `nueva` and `buena` go.
    But this must remove the adjective reading, not the word: `falta` is the
    feminine of `falto` and also the noun "lack", `pasa` the feminine of `paso`
    and also a raisin. Dropping the word loses a noun that has every right to
    be here."""
    import json
    out = set()
    for line in open(path, errors="ignore"):
        if '"word"' not in line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("lang_code") != lang or POS_MAP.get(r.get("pos")) != "adj":
            continue
        for s in r.get("senses") or []:
            tags = s.get("tags") or []
            if "feminine" in tags and ("form-of" in tags or s.get("form_of")):
                out.add(r["word"])
    return out


def participles(path, lang="es"):
    """word -> the verbs it is a past participle of."""
    import collections
    import json
    out = collections.defaultdict(set)
    for line in open(path, errors="ignore"):
        if '"word"' not in line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("lang_code") != lang:
            continue
        for s in r.get("senses") or []:
            tags = s.get("tags") or []
            if "participle" in tags or "past" in tags:
                for fo in (s.get("form_of") or []):
                    if isinstance(fo, dict) and fo.get("word"):
                        out[r["word"]].add(fo["word"])
    return out


def bases_of(path, lang="es"):
    """word -> the words it is an inflection of, for the note column."""
    import collections
    import json
    out = collections.defaultdict(set)
    for line in open(path, errors="ignore"):
        if '"word"' not in line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("lang_code") != lang:
            continue
        for s in r.get("senses") or []:
            for fo in (s.get("form_of") or []):
                if isinstance(fo, dict) and fo.get("word"):
                    out[r["word"]].add(fo["word"])
    return out


def band_for(rank):
    for lo, hi, name in BANDS:
        if lo <= rank < hi:
            return name
    return "wider"


def main(wikt_path):
    if os.path.exists(OUT):
        raise SystemExit(f"{OUT} already exists. It is written once on purpose; "
                         f"edit it by hand or delete it deliberately.")
    own, inflected = read_wiktionary(wikt_path)
    inflected_bases = bases_of(wikt_path)
    feminines = feminine_forms(wikt_path)
    parts = participles(wikt_path)
    letters = letter_names(wikt_path)
    rows, rank = [], 0
    for w in top_n_list("es", 20000):
        if len(rows) >= SIZE:
            break
        if not w.isalpha() or len(w) < 2:
            continue
        if w in ARTICLES:
            continue
        pos = {p for p in own.get(w, ()) if p != "name"}
        pos = pos - letters.get(w, set())      # `de` the letter, `la` the note
        if not pos:
            continue
        if inflected.get(w) and not (pos & SUBSTANTIAL):
            continue
        if w in feminines:
            pos = pos - {"adj"}
            if not pos:
                continue
        if w in BY_HAND_OUT:
            continue
        if pos == {"adj"} and parts.get(w):
            continue
        # a plural whose singular is already listed is not a base form
        have = {r["spanish"] for r in rows}
        if any(s in have for s in singular_of(w)):
            continue
        # A word that is also a conjugated form of something is kept only on a
        # noun or adjective reading, but whether that reading is worth a card
        # is a judgement: `trabajo` and `paso` plainly are, `haya` the beech
        # tree and `pasa` the raisin are not. Flagged rather than guessed at --
        # this file is meant to be edited by hand.
        # Flag only where the base is commoner than the word itself. Spanish
        # noun/verb homography is pervasive -- `casa` is also a form of
        # `casar`, `agua` of `aguar` -- and flagging all of it drowns the real
        # cases. `son` against `ser`, `he` against `haber`, `van` against `ir`:
        # there the noun reading is the marginal one.
        note = ""
        z = zipf_frequency(w, "es")
        commoner = [b for b in sorted(inflected_bases.get(w, ()))
                    if zipf_frequency(b, "es") > z + 0.3]
        if commoner:
            note = "check: commoner as a form of " + ", ".join(commoner[:2])
        rows.append({"rank": rank, "spanish": w, "pos": " ".join(sorted(pos)),
                     "zipf": round(zipf_frequency(w, "es"), 2),
                     "band": band_for(rank), "note": note})
        rank += 1

    os.makedirs("content", exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=["rank", "spanish", "pos", "zipf",
                                            "band", "note"])
        wr.writeheader()
        wr.writerows(rows)
    print(f"{len(rows)} words -> {OUT}   (written once; committed thereafter)")
    import collections
    for lo, hi, name in BANDS:
        n = sum(1 for r in rows if r["band"] == name)
        z = [r["zipf"] for r in rows if r["band"] == name]
        print(f"  {name:8s} {n:5d}   Zipf {min(z):.2f}–{max(z):.2f}")
    print()
    byp = collections.Counter(p for r in rows for p in r["pos"].split())
    print("  parts of speech:", dict(byp.most_common()))


if __name__ == "__main__":
    main(sys.argv[1])
