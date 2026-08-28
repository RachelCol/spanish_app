"""Alignment over lemmas and parts of speech rather than raw words.

Aligning surface forms conflates readings. Spanish `cuenta` is a noun in "la
cuenta, por favor" and a verb in "cuenta conmigo", and counting the string
mixes their translations; the same on the Italian side is why `meglio` and
`migliore` both attach to `mejor` with nothing to separate the adverb from the
adjective. Tagging both sides first, and aligning `word|POS` tokens, makes the
distinction the model's rather than something inferred afterwards from
Wiktionary.

Lemmatising as part of the same pass has a second benefit: the corpus is
matched on `lasciare` however the sentence spelt it, so conjugated forms stop
leaking in and stop needing to be filtered out later.

Short lines are dropped. A one- or two-word subtitle gives alignment nothing to
disambiguate against, and short lines are also where subtitle files are least
reliably paired.

Writes data/aligned_pos.json:  spanish|POS -> [[italian|POS, probability], ...]

    python pipeline/align_tagged.py <corpus-dir> [--pairs N] [--iters N]
"""
import collections
import json
import os
import sys

import spacy

MIN_TOKENS = 4         # below this a line carries no alignment signal
MAX_TOKENS = 20
PRUNE = 1e-3

UPOS = {"NOUN": "n", "VERB": "vblex", "AUX": "vblex", "ADJ": "adj",
        "ADV": "adv", "ADP": "pr", "PRON": "prn", "DET": "det",
        "CCONJ": "cnj", "SCONJ": "cnj", "INTJ": "ij", "NUM": "num"}


def tagged(nlp, lines):
    """Each line as a set of `lemma|pos` tokens."""
    out = []
    for doc in nlp.pipe(lines, batch_size=512):
        toks = {f"{t.lemma_.lower()}|{UPOS[t.pos_]}"
                for t in doc if t.is_alpha and t.pos_ in UPOS}
        out.append(toks)
    return out


def read_raw(corpus_dir, limit):
    """Balanced sentence pairs, before tagging."""
    es_lines, it_lines = [], []
    files = [(os.path.join(corpus_dir, f), os.path.join(corpus_dir, f[:-3] + ".it"))
             for f in sorted(os.listdir(corpus_dir)) if f.endswith(".es")]
    share = limit // max(1, len(files))
    for es_path, it_path in files:
        sys.stderr.write(f"  reading {os.path.basename(es_path)} (up to {share:,})\n")
        here = 0
        with open(es_path, errors="ignore") as fe, open(it_path, errors="ignore") as fi:
            for e, i in zip(fe, fi):
                if here >= share:
                    break
                ne, ni = len(e.split()), len(i.split())
                if not (MIN_TOKENS <= ne <= MAX_TOKENS):
                    continue
                if not (MIN_TOKENS <= ni <= MAX_TOKENS):
                    continue
                es_lines.append(e)
                it_lines.append(i)
                here += 1
    return es_lines, it_lines


def train(pairs, iters):
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
                z = sum(row.get(e, 0.0) for e in e_s)
                if z <= 0:
                    continue
                cf = count[f]
                for e in e_s:
                    p = row.get(e, 0.0)
                    if p > 0:
                        c = p / z
                        cf[e] += c
                        total[e] += c
        new, kept = collections.defaultdict(dict), 0
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
    limit = 1_200_000
    iters = 6
    if "--pairs" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--pairs") + 1])
    if "--iters" in sys.argv:
        iters = int(sys.argv[sys.argv.index("--iters") + 1])

    es_lines, it_lines = read_raw(corpus, limit)
    sys.stderr.write(f"{len(es_lines):,} pairs pass the length floor\n")

    sys.stderr.write("tagging Spanish ...\n")
    es_nlp = spacy.load("es_core_news_md", disable=["ner", "parser"])
    es_tok = tagged(es_nlp, es_lines)
    del es_lines
    sys.stderr.write("tagging Italian ...\n")
    it_nlp = spacy.load("it_core_news_md", disable=["ner", "parser"])
    it_tok = tagged(it_nlp, it_lines)
    del it_lines

    pairs = [(tuple(e), tuple(f)) for e, f in zip(es_tok, it_tok) if e and f]
    sys.stderr.write(f"{len(pairs):,} tagged pairs\n")
    t = train(pairs, iters)

    out = collections.defaultdict(list)
    for f, row in t.items():
        for e, p in row.items():
            if p >= 0.01:
                out[e].append((round(p, 4), f))
    result = {e: [[f, p] for p, f in sorted(v, reverse=True)[:20]]
              for e, v in out.items()}
    json.dump(result, open("data/aligned_pos.json", "w"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"\n{len(result)} tagged Spanish entries -> data/aligned_pos.json")
    for w in ("mejor|adj", "mejor|adv", "cuenta|n", "cuenta|vblex",
              "tiempo|n", "bajo|adj", "bajo|pr"):
        print(f"  {w:14s} " + "  ".join(f"{f} {p:.2f}" for f, p in result.get(w, [])[:4]))


if __name__ == "__main__":
    main()
