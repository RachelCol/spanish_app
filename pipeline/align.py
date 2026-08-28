"""Learn which Italian word translates which Spanish word.

Counting words that share a sentence cannot tell a translation from a
neighbour: `anche` sits beside `tiempo` because the sentence also contained
`también`, and `discussione` sits beside `cerrado` because the phrase was
`discussione chiusa`. Alignment fixes this by making the words compete. Across
millions of pairs, `también` explains `anche` far better than `tiempo` does,
so `tiempo` stops being credited for it.

IBM Model 1, trained with EM. The model is deliberately simple -- it ignores
word order entirely and only asks which target word each source word explains
-- which is all that is needed to produce a translation table, and it is what
`fast_align` and the rest are refinements of.

Competition is the whole mechanism, so the Spanish vocabulary must include the
words that ought to win. Restricting it to the deck would leave `anche` with
nothing but `tiempo` to attach to. It covers the deck plus the commonest few
thousand Spanish words besides.

    python pipeline/align.py <corpus-dir> [--pairs N] [--iters N]
"""
import collections
import json
import math
import os
import re
import sys
import unicodedata

from wordfreq import top_n_list

TOKEN = re.compile(r"[A-Za-zÁÉÍÓÚÜÑÀÈÌÒÙáéíóúüñàèìòùç]+")
MAX_LEN = 20           # long sentences align poorly and cost the most
PRUNE = 1e-3           # drop translation probabilities below this between rounds


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def vocabularies(extra_es=6000, it_n=40000):
    deck = {norm(w["es"]) for w in json.load(open("data/wordlist.json"))}
    es = deck | {norm(w) for w in top_n_list("es", extra_es)}
    it = {norm(w) for w in top_n_list("it", it_n)}
    return deck, es, it


def read_pairs(corpus_dir, es_vocab, it_vocab, limit):
    """Sentence pairs as word tuples, taken evenly from each corpus.

    Split evenly rather than in filename order: Europarl is institutional and
    OpenSubtitles is dialogue, and reading them in sequence would fill the
    quota with parliament before reaching a single conversation.
    """
    pairs = []
    files = [(os.path.join(corpus_dir, f), os.path.join(corpus_dir, f[:-3] + ".it"))
             for f in sorted(os.listdir(corpus_dir)) if f.endswith(".es")]
    share = limit // max(1, len(files))
    for es_path, it_path in files:
        sys.stderr.write(f"  reading {os.path.basename(es_path)} (up to {share:,})\n")
        here = 0
        with open(es_path, errors="ignore") as fe, open(it_path, errors="ignore") as fi:
            for es_line, it_line in zip(fe, fi):
                if here >= share or len(pairs) >= limit:
                    break
                e = [norm(t) for t in TOKEN.findall(es_line)]
                if not (1 < len(e) <= MAX_LEN):
                    continue
                f = [norm(t) for t in TOKEN.findall(it_line)]
                if not (1 < len(f) <= MAX_LEN):
                    continue
                e = tuple(sorted({w for w in e if w in es_vocab}))
                f = tuple(sorted({w for w in f if w in it_vocab}))
                if e and f:
                    pairs.append((e, f))
                    here += 1
                    if here % 250_000 == 0:
                        sys.stderr.write(f"    {here:,}\n")
    return pairs


def train(pairs, iters=5):
    """IBM Model 1: t[f][e] is P(italian f | spanish e)."""
    # uniform start, over co-occurring pairs only
    t = collections.defaultdict(dict)
    for e_s, f_s in pairs:
        for f in f_s:
            row = t[f]
            for e in e_s:
                row[e] = 1.0
    for f, row in t.items():
        n = len(row)
        for e in row:
            row[e] = 1.0 / n

    for it_no in range(iters):
        sys.stderr.write(f"  iteration {it_no + 1} ...\n")
        count = collections.defaultdict(lambda: collections.defaultdict(float))
        total = collections.defaultdict(float)
        for k, (e_s, f_s) in enumerate(pairs):
            if k and k % 500_000 == 0:
                sys.stderr.write(f"    {k:,}\n")
            for f in f_s:
                row = t[f]
                z = 0.0
                for e in e_s:
                    z += row.get(e, 0.0)
                if z <= 0:
                    continue
                cf = count[f]
                for e in e_s:
                    p = row.get(e, 0.0)
                    if p <= 0:
                        continue
                    c = p / z
                    cf[e] += c
                    total[e] += c
        new = collections.defaultdict(dict)
        kept = 0
        for f, row in count.items():
            out = new[f]
            for e, c in row.items():
                v = c / total[e] if total[e] else 0.0
                if v >= PRUNE:
                    out[e] = v
                    kept += 1
        t = new
        sys.stderr.write(f"  iteration {it_no + 1}: {kept:,} live pairs\n")
    return t


def main():
    corpus = sys.argv[1]
    limit = 3_000_000
    iters = 5
    if "--pairs" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--pairs") + 1])
    if "--iters" in sys.argv:
        iters = int(sys.argv[sys.argv.index("--iters") + 1])

    deck, es_vocab, it_vocab = vocabularies()
    sys.stderr.write(f"vocabulary: {len(es_vocab):,} Spanish, {len(it_vocab):,} Italian\n")
    pairs = read_pairs(corpus, es_vocab, it_vocab, limit)
    sys.stderr.write(f"{len(pairs):,} sentence pairs\n")
    t = train(pairs, iters)

    # invert to spanish -> [(italian, probability)], deck words only
    out = collections.defaultdict(list)
    for f, row in t.items():
        for e, p in row.items():
            if e in deck and p >= 0.01:
                out[e].append((round(p, 4), f))
    result = {e: [[f, p] for p, f in sorted(v, reverse=True)[:20]]
              for e, v in out.items()}
    json.dump(result, open("data/aligned.json", "w"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"\n{len(result)} Spanish words aligned -> data/aligned.json")
    for w in ("costa", "tiempo", "mejor", "primo", "auto", "carta", "hecho"):
        r = result.get(w, [])[:5]
        print(f"  {w:10s} " + "  ".join(f"{f} {p:.2f}" for f, p in r))


if __name__ == "__main__":
    main()
