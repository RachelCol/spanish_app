"""Fixed phrases whose parts do not stand alone.

`embargo` on its own is a seizure; it is `sin embargo` that means `tuttavia`,
and 98% of the word's uses are inside that phrase. Aligning the bare word
credits it with the phrase's meaning, which is how `embargo -> tuttavia` and
`menudo -> spesso` got onto cards.

These are counted as units. The list is hand-picked from a corpus measurement
of which words sit inside a fixed phrase most of the time, keeping only those
whose bare form a learner would not meet on its own -- `través`, `siquiera`,
`repente` have no independent life, while `acuerdo` and `propósito` do and keep
their own cards.

    python pipeline/build_phrases.py <corpus-dir>
"""
import collections
import json
import os
import re
import sys
import unicodedata

TOKEN = re.compile(r"[A-Za-zÁÉÍÓÚÜÑÀÈÌÒÙáéíóúüñàèìòùç]+")

# phrase -> the bare word it replaces on the lexicon
LOCKED = {
    "sin embargo": "embargo",
    "a través": "través",
    "de repente": "repente",
    "ni siquiera": "siquiera",
    "a menudo": "menudo",
    "por supuesto": "supuesto",
    "al revés": "revés",
    "a bordo": "bordo",
    "en absoluto": "absoluto",
    "de inmediato": "inmediato",
    # Found in the overruled review: each of these is why a bare word was
    # credited with the phrase's meaning. The words themselves have real
    # standalone uses, so they keep their own cards and the phrase joins them.
    "a pesar": "pesar",         "de vez en cuando": "vez",
    "en concreto": "concreto",  "a lo largo": "largo",
    "alrededor de": "alrededor",
}

IT_SKIP = set("""il lo la i gli le un uno una l di a da in con su per tra fra e ed o che se ma
non ci si mi ti vi ne del della dei delle nel nella dal dalla al alla sul sulla
è sono ha ho hanno era erano essere avere fare dire come dove quando cosa
questo questa quello quella qui qua lì là
dell all nell sull dall coll quell un anche solo più molto po cosi coso
pero perche quando dopo prima ora poi già ancora sempre mai""".split())


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def main(corpus_dir, cap=4000):
    from wordfreq import zipf_frequency
    keys = {norm(p): p for p in LOCKED}
    seen = collections.Counter()
    tally = collections.defaultdict(collections.Counter)

    files = [(os.path.join(corpus_dir, f), os.path.join(corpus_dir, f[:-3] + ".it"))
             for f in sorted(os.listdir(corpus_dir)) if f.endswith(".es")]
    for es_path, it_path in files:
        sys.stderr.write(f"  {os.path.basename(es_path)}\n")
        with open(es_path, errors="ignore") as fe, open(it_path, errors="ignore") as fi:
            for es_line, it_line in zip(fe, fi):
                low = " " + norm(es_line) + " "
                hits = [p for k, p in keys.items() if f" {k} " in low
                        and seen[p] < cap]
                if not hits:
                    continue
                its = {norm(t) for t in TOKEN.findall(it_line)} - IT_SKIP
                for p in hits:
                    seen[p] += 1
                    tally[p].update(its)

    out = {}
    for phrase, total in seen.items():
        if total < 30:
            continue
        rows = [(c / total, it) for it, c in tally[phrase].most_common(40)
                if zipf_frequency(it, "it") >= 2.5]
        rows.sort(reverse=True)
        if not rows:
            continue
        top = rows[0][0]
        keep = [(it, round(100 * f, 1)) for f, it in rows if f >= top * 0.35][:3]
        out[phrase] = {"pairs": total, "replaces": LOCKED[phrase],
                       "it": [{"it": it, "pct": p} for it, p in keep]}
    json.dump(out, open("data/phrases.json", "w"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"\n{len(out)} phrases -> data/phrases.json")
    for p, v in sorted(out.items()):
        print(f"  {p:16s} ({v['pairs']:5d} pairs)  "
              + ", ".join(f"{i['it']} {i['pct']}%" for i in v["it"]))


if __name__ == "__main__":
    main(sys.argv[1])
