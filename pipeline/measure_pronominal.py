"""What Italian actually says where Spanish uses a pronominal verb.

The lexicon holds bare infinitives, so `bañar` has no corpus data: nobody
writes it. The language writes `me baño`, `se bañó`, `bañarse`. Searching for
those instead is the only way to find out whether `bañarse` is `fare il bagno`
or `bagnarsi` -- the bare form cannot tell us, and neither can a dictionary
that lists the bare form.

Counts single Italian words and two-word units side by side, because the
answer is a phrase as often as it is a verb.
"""
import collections
import json
import os
import re
import sys

from wordfreq import zipf_frequency

CLITIC = r"(?:me|te|se|nos|os)"
IT_TOKEN = re.compile(r"[a-zàèéìòùA-ZÀÈÉÌÒÙ']+")
STOP = set("""il lo la i gli le un uno una di a da in con su per tra fra e o ma
che non è sono ho hai ha abbiamo avete hanno mi ti si ci vi lo la li le ne del
della dei delle al alla ai alle dal dalla nel nella sul sulla questo questa
quello quella io tu lui lei noi voi loro come più molto poi già anche se""".split())


def stems(verb):
    """Enough of the verb to catch its conjugations."""
    root = verb[:-2]
    return root, [f"{root}", f"{verb}"]


def main(corpus_dir, verbs, limit=8_000_000):
    pats = {}
    for v in verbs:
        root, _ = stems(v)
        pats[v] = re.compile(
            rf"\b(?:{CLITIC}\s+{root}\w*|{root}\w*(?:r|rse|ndose)\b\s*|{root}\w*se\b)",
            re.IGNORECASE)

    words = collections.defaultdict(collections.Counter)
    bigrams = collections.defaultdict(collections.Counter)
    hits = collections.Counter()

    files = sorted(f for f in os.listdir(corpus_dir) if f.endswith(".es"))
    n = 0
    for f in files:
        es_path = os.path.join(corpus_dir, f)
        it_path = os.path.join(corpus_dir, f[:-3] + ".it")
        with open(es_path, errors="ignore") as fe, open(it_path, errors="ignore") as fi:
            for es_line, it_line in zip(fe, fi):
                n += 1
                if n > limit:
                    break
                for v, rx in pats.items():
                    if rx.search(es_line):
                        hits[v] += 1
                        toks = [t.lower() for t in IT_TOKEN.findall(it_line)]
                        keep = [t for t in toks
                                if t not in STOP and zipf_frequency(t, "it") > 2.0]
                        words[v].update(set(keep))
                        bigrams[v].update({" ".join(toks[i:i + 2])
                                           for i in range(len(toks) - 1)})
        if n > limit:
            break

    out = {}
    for v in verbs:
        tot = hits[v] or 1
        top_w = [(w, round(100 * c / tot, 1)) for w, c in words[v].most_common(6)]
        top_b = [(b, round(100 * c / tot, 1)) for b, c in bigrams[v].most_common(40)
                 if not set(b.split()) <= STOP][:6]
        out[v] = {"lines": hits[v], "words": top_w, "phrases": top_b}
        print(f"\n{v}  ({hits[v]:,} Spanish lines)")
        print("   words  :", ", ".join(f"{w} {p}%" for w, p in top_w))
        print("   phrases:", ", ".join(f"{b} {p}%" for b, p in top_b))
    json.dump(out, open("data/pronominal.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
