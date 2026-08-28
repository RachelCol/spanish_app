"""An independent verdict on each overruled row, through English.

The overruled list asks whether the corpus was right to displace the
dictionary. Neither side of that argument is a witness: the corpus is the
accused and the dictionary is the party it overruled. English Wiktionary is
the third opinion -- it defines Spanish and Italian words in English, so a
shared content word between `manera` and `modo` is evidence they mean the
same thing, arrived at without either source.

The rows fall into two questions, not one, and they need different answers:

  `corpus beats dictionary`  -- a real head-to-head. Revert or keep.
  `dictionary offered nothing` -- no candidate existed to revert *to*. The
      question is keep or *drop the reading*, and answering `revert` on one
      of these does nothing. This is where `nadie -> vero` lives.
"""
import csv
import json
import re
import sys
from collections import defaultdict

sys.path.insert(0, "pipeline")
from build_crosscheck import STOP

WORD = re.compile(r"[a-z]+")
POS = {"n": "noun", "adj": "adj", "adv": "adv", "vblex": "verb"}


def glosses(path, wanted):
    """word -> pos -> set of content words from its English definitions."""
    out = defaultdict(lambda: defaultdict(set))
    for line in open(path, errors="ignore"):
        if '"word"' not in line:
            continue
        e = json.loads(line)
        w = e.get("word", "").lower()
        if w not in wanted:
            continue
        for s in e.get("senses", []):
            for g in s.get("glosses", []) or []:
                out[w][e.get("pos", "")] |= {t for t in WORD.findall(g.lower())
                                             if t not in STOP and len(t) > 2}
    return out


def main(wikt_dir):
    rows = list(csv.DictReader(open("review_overruled.csv")))
    es_want = {r["spanish"] for r in rows}
    it_want = {r["corpus"] for r in rows} | {r["dictionary"] for r in rows if r["dictionary"]}

    es_g = glosses(f"{wikt_dir}/es-en.jsonl", es_want)
    it_g = glosses(f"{wikt_dir}/it-en.jsonl", it_want)

    def overlap(es, pos, it):
        """Shared English content words, preferring the row's part of speech
        on the Spanish side and allowing any on the Italian side -- Italian
        renders a Spanish noun with a noun nearly always, and the exceptions
        are the interesting rows, not errors to suppress."""
        want = POS.get(pos)
        left = es_g.get(es, {})
        left = left.get(want, set()) or set().union(*left.values()) if left else set()
        right = it_g.get(it, {})
        right = set().union(*right.values()) if right else set()
        return left & right

    out = []
    for r in rows:
        c = overlap(r["spanish"], r["pos"], r["corpus"])
        d = overlap(r["spanish"], r["pos"], r["dictionary"]) if r["dictionary"] else set()
        known = r["spanish"] in es_g and r["corpus"] in it_g
        if not known:
            v = "unknown"
        elif c and not d:
            v = "corpus"          # keep what the corpus chose
        elif d and not c:
            v = "dictionary"      # revert
        elif c and d:
            v = "both"
        else:
            v = "neither"         # nothing supports either: read this one
        r["verdict"] = v
        r["shared"] = " ".join(sorted(c)[:4])
        r["shared_dict"] = " ".join(sorted(d)[:4])
        out.append(r)

    with open("data/overruled_judged.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(out)
    from collections import Counter
    for kind in ("dictionary offered nothing", "corpus beats"):
        sub = [r for r in out if r["note"].startswith(kind)]
        print(f"\n{kind}  ({len(sub)} rows)")
        for v, n in Counter(r["verdict"] for r in sub).most_common():
            print(f"    {v:12s} {n:4d}")


if __name__ == "__main__":
    main(sys.argv[1])
