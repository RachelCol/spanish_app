"""How often each definition pair actually co-occurs, counted exactly.

matrix.json keeps each Spanish word's thirty commonest Italian neighbours, and
those are `e`, `di`, `che` and the rest -- so a real translation can fall off
the end and read as 0%. This counts only the pairs that made it into a
definition, which is a few thousand rather than everything, and so can be
exact.

The number is of all sentence pairs containing the Spanish word, including
those where Italian said it another way. A low figure means the sentence is
usually restructured, which is worth seeing on a card.
"""
import collections
import json
import os
import re
import sys

from phrase_mask import masker
import unicodedata

TOKEN = re.compile(r"[A-Za-zÁÉÍÓÚÜÑÀÈÌÒÙáéíóúüñàèìòùç]+")

from lookup import build as build_lookup, strip


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def main(corpus_dir):
    defs = json.load(open("data/definitions.json"))
    wanted = collections.defaultdict(set)          # spanish -> {italian}
    for es, entry in defs.items():
        for items in entry["by_pos"].values():
            for i in items:
                wanted[es].add(i["it"])
    look = build_lookup(list(wanted))
    lookup = wanted
    seen = collections.Counter()
    hit = collections.defaultdict(collections.Counter)

    mask = masker()
    files = [(os.path.join(corpus_dir, f), os.path.join(corpus_dir, f[:-3] + ".it"))
             for f in sorted(os.listdir(corpus_dir)) if f.endswith(".es")]
    for es_path, it_path in files:
        sys.stderr.write(f"  {os.path.basename(es_path)}\n")
        n = 0
        with open(es_path, errors="ignore") as fe, open(it_path, errors="ignore") as fi:
            for es_line, it_line in zip(fe, fi):
                n += 1
                if n % 5_000_000 == 0:
                    sys.stderr.write(f"    {n:,}\n")
                hits = {w for t in TOKEN.findall(mask(es_line))
                        if (w := look.get(t.lower()) or look.get(strip(t)))}
                if not hits:
                    continue
                its = set()
                for t in TOKEN.findall(it_line):
                    its.add(t.lower())
                    its.add(strip(t))
                for w in hits:
                    seen[w] += 1
                    # Count the accent-free form as the accented one: subtitle
                    # text writes `citta` and `città` interchangeably, and
                    # splitting them left `società` reading 0%.
                    for cand in lookup[w]:
                        if cand in its or strip(cand) in its:
                            hit[w][cand] += 1
        sys.stderr.write(f"    {n:,}\n")

    out = {}
    for w, total in seen.items():
        if total < 20:
            continue
        out[w] = {it: round(100 * c / total, 1) for it, c in hit[w].items()}
    json.dump({"pairs": dict(seen), "share": out}, open("data/shares.json", "w"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"\n{len(out)} Spanish words counted exactly -> data/shares.json")


if __name__ == "__main__":
    main(sys.argv[1])
