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
import sys

from wordfreq import top_n_list, zipf_frequency

sys.path.insert(0, "pipeline")
from build_wordlist import read_wiktionary, POS_MAP, singular_of  # noqa: E402

SIZE = 3000
OUT = "content/lexicon.csv"

# Frequency bands, cut so each is a sensible chunk of 3,000 rather than by
# absolute Zipf, which put 22 words in one band and 1,700 in another.
BANDS = [(0, 300, "first"), (300, 800, "core"), (800, 1500, "common"),
         (1500, 2200, "useful"), (2200, 3000, "wider")]


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
    rows, rank = [], 0
    for w in top_n_list("es", 20000):
        if len(rows) >= SIZE:
            break
        if not w.isalpha() or len(w) < 2:
            continue
        pos = {p for p in own.get(w, ()) if p != "name"}
        if not pos:
            continue
        # a plural whose singular is already listed is not a base form
        have = {r["spanish"] for r in rows}
        if any(s in have for s in singular_of(w)):
            continue
        rows.append({"rank": rank, "spanish": w, "pos": " ".join(sorted(pos)),
                     "zipf": round(zipf_frequency(w, "es"), 2),
                     "band": band_for(rank), "note": ""})
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
