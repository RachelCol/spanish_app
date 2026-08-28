"""Add the verbs that surface-form ranking lost, and band verbs by real use.

The lexicon ranked every word by `zipf_frequency` of its own spelling. For a
noun or an adjective that is close enough -- `casa` is written `casa`. For a
verb it is badly wrong, because Spanish writes the infinitive far less often
than it writes the verb: `gustar` scores 4.05 while `gusta` scores 5.48. So
`necesitar`, a top-150 verb, was absent from a list of the 3,000 commonest
Spanish words, along with `gustar`, `faltar`, `encantar` and `soler` -- the
whole backwards-verb class, which is exactly what an Italian speaker can pick
up cheaply because `piacere` behaves the same way.

Aggregating a lemma's forms is the fix and is also a trap. Done across all
parts of speech it puts `unir` at rank 8, because `una` is one of its forms,
and `parir` at 25 from `para`; a whole-lexicon rebuild on that basis came out
1070 words in and 1070 out, and much worse than what it replaced. Two things
make it safe here: only verbs are aggregated, and kaikki's form-of entries are
skipped, since it lists `necesito` as an entry in its own right and letting it
claim its own spelling collapses every conjugation back to the infinitive.

Bands are recomputed for verbs only. No word leaves, so no card and no review
history is lost; only the order in which verbs are introduced changes.
"""
import collections
import csv
import json
import math
import sys

from wordfreq import word_frequency, zipf_frequency

DEPTH = 500                      # cover the commonest 500 Spanish verbs
JUNK = {"estan", "habia", "mayar", "unir", "car", "dir", "sar"}
# `cagar` clears the frequency bar and is excluded by choice, in
# content/excluded.csv, rather than here -- it is not a data error.
BANDS = [("first", 300), ("core", 500), ("common", 700),
         ("useful", 700), ("wider", 800)]


def aggregate(path):
    """verb -> summed frequency of the forms nothing else lays claim to.

    Both filters below are load-bearing. Without the first, `parir` collects
    `para` and `sobrar` collects `sobre`; without the second, `a` and `se`
    arrive as verbs. A form shared with any non-verb, or with a second verb,
    contributes nothing to either -- `faltar` is counted from `faltaba` and
    `faltan` and never from `falta`, which is also a noun.
    """
    verbs, other = collections.defaultdict(set), set()
    for line in open(path, errors="ignore"):
        if '"word"' not in line:
            continue
        e = json.loads(line)
        w = e.get("word", "").lower()
        if not w.isalpha():
            continue
        if any(s.get("form_of") for s in e.get("senses", [])):
            continue
        fs = {(f.get("form") or "").lower() for f in e.get("forms", [])}
        fs = {f for f in fs if f.isalpha() and len(f) > 1} | {w}
        if e.get("pos") == "verb":
            verbs[w] |= fs
        else:
            other |= fs

    claims = collections.Counter(f for fs in verbs.values() for f in fs)
    return {v: sum(word_frequency(f, "es") for f in fs
                   if f not in other and claims[f] == 1)
            for v, fs in verbs.items()}


def main(wikt_es_path):
    freq = aggregate(wikt_es_path)
    json.dump(freq, open("data/verb_frequency.json", "w"), separators=(",", ":"))

    rows = list(csv.DictReader(open("content/lexicon.csv")))
    have = {r["spanish"] for r in rows}
    ranked = [v for v in sorted(freq, key=lambda v: -freq[v]) if freq[v] > 0]
    add = [v for v in ranked[:DEPTH] if v not in have and v not in JUNK]

    def eff_zipf(v):
        """The zipf the verb would have had if written the way it is used."""
        return round(math.log10(freq[v] * 1e9), 2) if freq.get(v) else 0.0

    for v in add:
        rows.append({"rank": "", "spanish": v, "pos": "vblex",
                     "zipf": eff_zipf(v), "band": "",
                     "note": "added after the lexicon was found to rank verbs "
                             "by the frequency of the infinitive spelling "
                             "rather than of the verb"})

    # Verbs sort among themselves by real use; everything else keeps its place.
    verbs = [r for r in rows if "vblex" in r["pos"]]
    for r in verbs:
        if r["spanish"] in freq and freq[r["spanish"]] > 0:
            r["zipf"] = eff_zipf(r["spanish"])
    others = [r for r in rows if "vblex" not in r["pos"]]
    verbs.sort(key=lambda r: -float(r["zipf"] or 0))
    others.sort(key=lambda r: int(r["rank"]) if r["rank"] else 10 ** 6)

    # Interleave so each band keeps its share of verbs and non-verbs.
    out, vi, oi = [], 0, 0
    ratio = len(verbs) / max(len(rows), 1)
    for n in range(len(rows)):
        take_verb = (vi < len(verbs)) and (oi >= len(others) or
                                           (vi + 0.5) / max(n + 1, 1) < ratio)
        if take_verb:
            out.append(verbs[vi]); vi += 1
        else:
            out.append(others[oi]); oi += 1

    edges, at = {}, 0
    for name, size in BANDS:
        for i in range(at, min(at + size, len(out))):
            edges[i] = name
        at += size
    for i, r in enumerate(out):
        r["rank"] = i + 1
        r["band"] = edges.get(i, BANDS[-1][0])

    with open("content/lexicon.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=["rank", "spanish", "pos", "zipf",
                                            "band", "note"])
        wr.writeheader()
        wr.writerows(out)
    print(f"added {len(add)} verbs -> lexicon is now {len(out)} words")
    print(f"  highest-ranked additions: {', '.join(add[:8])}")
    moved = collections.Counter(r["band"] for r in out if "vblex" in r["pos"])
    print(f"  verbs by band: {dict(moved)}")


if __name__ == "__main__":
    main(sys.argv[1])
