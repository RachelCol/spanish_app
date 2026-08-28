"""Step 2: count how each Spanish word is actually translated.

For every Spanish base form, take aligned sentence pairs whose Spanish side
contains that exact word, and tally what the Italian side contains -- exactly,
no stemming and no lemmatising, so `costa` and `costo` never merge. Matching
the Spanish base form keeps the Italian side in the same number, so plurals
need no special handling.

Two filters on the Italian side:

  capitalised tokens are skipped unless the Spanish word is itself a proper
  noun, or `costa` acquires *Rica* as a meaning;

  the token must have real currency in Italian, by Italian frequency. This
  keeps `leader`, `account`, `staff` and `trend`, which Italians say, and drops
  untranslated English sitting in subtitle files.

Percentages are of all pairs containing the Spanish word, including those where
Italian phrased it differently -- so a low top score means the sentence is
usually restructured, which is worth knowing.

    python pipeline/build_matrix.py <corpus-dir> [--cap N]
"""
import collections
import json
import os
import re
import sys
import unicodedata

from wordfreq import zipf_frequency

TOKEN = re.compile(r"[A-Za-zÁÉÍÓÚÜÑÀÈÌÒÙáéíóúüñàèìòùç]+")
MIN_IT_ZIPF = 2.5      # `leader` clears this; untranslated English does not
KEEP_TOP = 30


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def build(corpus_dir, cap=3000):
    words = json.load(open("data/wordlist.json"))
    wanted = {norm(w["es"]): w["es"] for w in words}

    seen = collections.Counter()
    tally = collections.defaultdict(collections.Counter)

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
                hits = set()
                for t in TOKEN.findall(es_line):
                    w = wanted.get(norm(t))
                    if w is not None and seen[w] < cap:
                        hits.add(w)
                if not hits:
                    continue
                # Capitalisation is read before lowercasing: a token that is
                # capitalised mid-sentence is a name, not a translation.
                it_toks = TOKEN.findall(it_line)
                keep = set()
                for i, t in enumerate(it_toks):
                    if i > 0 and t[:1].isupper():
                        continue
                    keep.add(norm(t))
                if not keep:
                    continue
                for w in hits:
                    seen[w] += 1
                    tally[w].update(keep)
        sys.stderr.write(f"    {n:,}\n")

    out = {}
    for w in wanted.values():
        total = seen.get(w, 0)
        if total < 20:
            continue
        rows = []
        for it, c in tally[w].most_common(120):
            if c < 3 or it == norm(w) and False:
                continue
            if zipf_frequency(it, "it") < MIN_IT_ZIPF:
                continue
            rows.append([it, round(100 * c / total, 2)])
            if len(rows) >= KEEP_TOP:
                break
        out[w] = {"pairs": total, "it": rows}
    return out


if __name__ == "__main__":
    d = sys.argv[1]
    cap = 3000
    if "--cap" in sys.argv:
        cap = int(sys.argv[sys.argv.index("--cap") + 1])
    m = build(d, cap)
    json.dump(m, open("data/matrix.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"\n{len(m)} Spanish words counted -> data/matrix.json")
    for floor in (50, 200, 1000):
        print(f"  with at least {floor:4d} pairs: "
              f"{sum(1 for v in m.values() if v['pairs'] >= floor)}")
