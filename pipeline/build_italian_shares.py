"""The percentage an Italian card should print, measured from the Italian word.

The card was showing the Spanish word's share -- of the pairs holding `nunca`,
76% hold `mai`; of the pairs holding `jamás`, 74% do. Two different
denominators, sitting side by side on one card as though they were parts of a
whole. They also hid what matters: `nunca` appears in 246,000 pairs and
`jamás` in 25,000, so one is ten times commoner and the card made them look
alike.

Counting from the Italian word instead answers the question the card asks --
you have `mai`, which Spanish word do you reach for -- and the figures share a
denominator.

    python pipeline/build_italian_shares.py <corpus-dir>
"""
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from phrase_mask import masker

TOKEN = re.compile(r"[A-Za-zÀ-ÿ']+")


def main(corpus_dir):
    prompts = json.load(open("data/prompts.json"))
    wanted = {}                      # italian word -> {spanish answers}
    for it, answers in prompts.items():
        wanted[it.lower()] = {a["es"].lower() for a in answers}

    # a Spanish answer may be a phrase, so match those on the line, not tokens
    multi = {es for v in wanted.values() for es in v if " " in es}

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
                its = {t.lower() for t in TOKEN.findall(it_line)} & wanted.keys()
                if not its:
                    continue
                # Single words are counted off the masked line, so `pesar` is
                # not counted inside `a pesar de`. A phrase has to be counted
                # off the raw line -- the mask exists to hide it, and hiding a
                # phrase from its own tally gave `a menudo` nothing at all.
                low = " " + " ".join(TOKEN.findall(mask(es_line).lower())) + " "
                raw = " " + " ".join(TOKEN.findall(es_line.lower())) + " "
                es_toks = set(low.split())
                for it in its:
                    seen[it] += 1
                    for es in wanted[it]:
                        if (f" {es} " in raw) if es in multi else (es in es_toks):
                            hit[it][es] += 1
        sys.stderr.write(f"    {n:,}\n")

    out = {}
    for it, total in seen.items():
        if total < 20:
            continue
        out[it] = {"pairs": total,
                   "share": {es: round(100 * c / total, 1)
                             for es, c in hit[it].items()}}
    json.dump(out, open("data/italian_shares.json", "w"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"\n{len(out)} Italian words counted -> data/italian_shares.json")
    for probe in ("mai", "ora", "molto", "dopo"):
        if probe in out:
            top = sorted(out[probe]["share"].items(), key=lambda kv: -kv[1])[:4]
            print(f"  {probe:<8} ({out[probe]['pairs']:,} pairs) {top}")


if __name__ == "__main__":
    main(sys.argv[1])
