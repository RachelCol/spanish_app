"""What relative score do translations we already trust actually get?

The threshold is meant to separate real senses from coincidences. Rather than
pick a number and hope, measure it against pairs whose status is already known:

  known good -- the core and common pairings read by hand, which we believe
  known bad  -- the pairings removed during the audit as wrong

A relative score is a translation's share divided by the share of the top
translation for that Spanish word. `costo` at 3.4% against `costa` at 49% is
7% relative.
"""
import json
import sys
from collections import defaultdict


def relative(matrix, es, it):
    e = matrix.get(es)
    if not e or not e["it"]:
        return None
    top = e["it"][0][1]
    if not top:
        return None
    for w, pct in e["it"]:
        if w == it.lower():
            return 100 * pct / top
    return 0.0


def main():
    matrix = json.load(open("data/matrix.json"))
    deck = json.load(open("data/deck.json"))
    sys.path.insert(0, "pipeline")
    from pairs import DROP_SENSES

    tiers = {c["es"]: c["tier"] for c in deck}
    good = [(c["es"], s) for c in deck if c["tier"] in ("core", "common")
            for s in c["senses"] if " " not in s]
    bad = [(es, it) for es, it in DROP_SENSES if " " not in it]

    def scores(pairs):
        out, missing = [], 0
        for es, it in pairs:
            r = relative(matrix, es, it)
            if r is None:
                missing += 1
            else:
                out.append((r, es, it))
        return sorted(out), missing

    g, g_missing = scores(good)
    b, b_missing = scores(bad)

    def band(rows, edges=(0, 1, 5, 10, 15, 20, 30, 50, 101)):
        counts = []
        for lo, hi in zip(edges, edges[1:]):
            counts.append((lo, hi, sum(1 for r, _, _ in rows if lo <= r < hi)))
        return counts

    print(f"KNOWN GOOD -- {len(g)} hand-read core/common pairings "
          f"({g_missing} not in the corpus)")
    for lo, hi, n in band(g):
        bar = "#" * min(60, n * 60 // max(1, len(g)))
        print(f"   {lo:3d}-{hi:3d}%  {n:5d}  {bar}")
    print(f"\n   at a 10% cut this keeps {sum(1 for r,_,_ in g if r >= 10)} of {len(g)}"
          f"  ({100*sum(1 for r,_,_ in g if r >= 10)//max(1,len(g))}%)")
    print(f"   at a 15% cut this keeps {sum(1 for r,_,_ in g if r >= 15)} of {len(g)}"
          f"  ({100*sum(1 for r,_,_ in g if r >= 15)//max(1,len(g))}%)")

    print(f"\nKNOWN BAD -- {len(b)} pairings removed in the audit "
          f"({b_missing} not in the corpus)")
    for r, es, it in b:
        print(f"   {r:6.1f}%   {es} -> {it}")

    print("\nGOOD pairings that would be lost at 10%:")
    for r, es, it in g:
        if r < 10:
            print(f"   {r:6.1f}%   {es} -> {it}   [{tiers.get(es)}]")


if __name__ == "__main__":
    main()
