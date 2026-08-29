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
# Italian drops the final -e of an infinitive before another word: `dover
# fare`, `aver visto`, `esser certi`. The corpus sees the truncation, which is
# not a word. `tener que` answered `dover` because of this.
TRUNCATED = {"dover": "dovere", "aver": "avere", "esser": "essere",
             "poter": "potere", "voler": "volere", "saper": "sapere",
             "far": "fare", "andar": "andare", "veder": "vedere",
             "voltar": "voltare", "esserci": "esserci"}

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
    # `obstante` occurs only inside `no obstante` -- 100% of its uses, measured
    # -- and had no card at all, so the connector was going untaught.
    "no obstante": "obstante",
    # Found in the overruled review: each of these is why a bare word was
    # credited with the phrase's meaning. The words themselves have real
    # standalone uses, so they keep their own cards and the phrase joins them.
    # These five keep their bare word as a card of its own: `largo`, `vez`,
    # `pesar`, `concreto` and `alrededor` are ordinary Spanish outside the
    # phrase, unlike `siquiera` or `embargo`, which a learner never meets
    # alone. The phrase joins them rather than replacing them.
    "a pesar": None,            "de vez en cuando": None,
    "en concreto": None,        "a lo largo": None,
    "alrededor de": None,
    # Italian `dovere` is `tener que` for a plain obligation and `deber` for a
    # duty or a debt. Without the phrase the prompt could only reach `deber`,
    # which is the heavier of the two and not the everyday one.
    "tener que": None,
}

IT_SKIP = set("""il lo la i gli le un uno una l di a da in con su per tra fra e ed o che se ma
non ci si mi ti vi ne del della dei delle nel nella dal dalla al alla sul sulla
è sono ha ho hanno era erano essere avere fare dire come dove quando cosa
questo questa quello quella qui qua lì là
dell all nell sull dall coll quell un anche solo più molto po cosi coso
commissione parlamento consiglio europea europeo signor presidente onorevole
unione stato stati membro membri paese paesi piu piú più gia già senza
anni anno degli delle dei negli nelle ogni volta cosa modo caso punto
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
        # Fold a truncated infinitive back onto the real word before ranking,
        # so `dover` and `dovere` count as one thing rather than splitting.
        folded = collections.Counter()
        for it, c in tally[phrase].items():
            folded[TRUNCATED.get(it, it)] += c
        rows = [(c / total, it) for it, c in folded.most_common(40)
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
