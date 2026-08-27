"""Count how a Spanish word is actually translated, across millions of pairs.

Which Italian words belong on a Spanish card has been a judgement call, made by
Apertium's ordering and then by me. This replaces it with a count: take every
aligned sentence pair where the Spanish word appears, and tally what the
Italian side contains.

    costa -> costa 46%  riva 3%  costo 2%   (of all pairs containing `costa`)

The denominator is every pair containing the Spanish word, including those
where Italian said it another way entirely -- so the numbers run low, and a
low top score is itself information: it means the sentence is usually
restructured. Inclusion is decided on the ratio between senses rather than the
raw figure, which makes the denominator cancel out.

Matching is by stem, not exact form, so `hablar` sees `habla` and `hablando`.
That over-matches slightly (`hablador`) and is fine for counting; the parts of
speech come later, from a tagged sample rather than from all 32 million lines.

    python pipeline/build_matrix.py <corpus-dir> [--cap N]
"""
import collections
import json
import os
import re
import sys
import unicodedata

TOKEN = re.compile(r"[a-záéíóúüñàèìòùçA-ZÁÉÍÓÚÜÑÀÈÌÒÙ]+")

# Counting these tells us nothing -- they appear beside everything.
IT_SKIP = set("""
il lo la i gli le un uno una l di a da in con su per tra fra e ed o od che se ma
non ci si mi ti vi ne io tu lui lei noi voi loro questo questa quello quella
essere avere fare dire come dove quando più meno molto poco tutto altro
del della dei delle nel nella dal dalla al alla sul sulla è sono ha ho hanno
era erano sia siamo siete stato stata cosa qui qua lì là ora poi già ancora
anche solo sempre mai nulla niente bene male grande piccolo buono
""".split())


def stem(w):
    return w[:max(4, len(w) - 2)]


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def build(corpus_dir, cap=4000):
    deck = json.load(open("data/deck.json"))
    cards = [c["es"] for c in deck]

    # stem -> the card words that stem reaches
    by_stem = collections.defaultdict(set)
    for w in cards:
        by_stem[stem(norm(w))].add(w)
    stems = set(by_stem)
    maxstem = max(len(s) for s in stems)

    seen = collections.Counter()                       # pairs counted per card
    tally = collections.defaultdict(collections.Counter)   # card -> italian -> n

    pairs = [(os.path.join(corpus_dir, f), os.path.join(corpus_dir, f[:-3] + ".it"))
             for f in sorted(os.listdir(corpus_dir)) if f.endswith(".es")]

    for es_path, it_path in pairs:
        name = os.path.basename(es_path)
        sys.stderr.write(f"  {name} ...\n")
        n = 0
        with open(es_path, errors="ignore") as fe, open(it_path, errors="ignore") as fi:
            for es_line, it_line in zip(fe, fi):
                n += 1
                if n % 2_000_000 == 0:
                    sys.stderr.write(f"    {n:,} lines\n")
                es_toks = TOKEN.findall(es_line)
                if not es_toks or len(es_toks) > 40:
                    continue
                hits = set()
                for t in es_toks:
                    t = norm(t)
                    for k in range(4, min(len(t), maxstem) + 1):
                        for w in by_stem.get(t[:k], ()):
                            if seen[w] < cap:
                                hits.add(w)
                if not hits:
                    continue
                it_toks = {norm(t) for t in TOKEN.findall(it_line)}
                it_toks -= IT_SKIP
                if not it_toks:
                    continue
                for w in hits:
                    seen[w] += 1
                    tally[w].update(it_toks)
        sys.stderr.write(f"    {n:,} lines\n")

    out = {}
    for w in cards:
        total = seen.get(w, 0)
        if not total:
            continue
        top = tally[w].most_common(25)
        out[w] = {"pairs": total,
                  "it": [[it, round(100 * c / total, 1)] for it, c in top if c >= 3]}
    return out


if __name__ == "__main__":
    d = sys.argv[1]
    cap = 4000
    if "--cap" in sys.argv:
        cap = int(sys.argv[sys.argv.index("--cap") + 1])
    m = build(d, cap)
    json.dump(m, open("data/matrix.json", "w"), ensure_ascii=False, separators=(",", ":"))
    covered = sum(1 for v in m.values() if v["pairs"] >= 50)
    print(f"\n{len(m)} Spanish words counted -> data/matrix.json")
    print(f"  with at least 50 example pairs: {covered}")
