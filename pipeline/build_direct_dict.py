"""A Spanish-Italian dictionary with no English in the middle.

Everything up to now went through English: English Wiktionary defines Italian
and Spanish words in English, and a shared gloss was taken as evidence the two
mean the same thing. That works and has one built-in failure -- a cognate
shares its English gloss for free, so the pivot kept telling us `frequentemente`
was a better answer than `spesso`.

The Italian and Spanish Wiktionary editions carry translation sections of their
own: an Italian entry lists its Spanish equivalents outright, tagged with which
of its senses each belongs to. Both editions are read, in both directions, and
merged -- what one edition omits the other often has.

    python pipeline/build_direct_dict.py <dir with it.jsonl.gz and es.jsonl.gz>
"""
import collections
import gzip
import json
import os
import sys

POS = {"noun": "n", "verb": "vblex", "adj": "adj", "adv": "adv",
       "prep": "pr", "conj": "cnj", "pron": "prn", "det": "det",
       "intj": "ij", "num": "num", "article": "det"}


def read(path, own_lang, want_lang):
    """word -> {(other word, pos)} from one edition's translation sections."""
    out = collections.defaultdict(set)
    n = 0
    for line in gzip.open(path, "rt", errors="ignore"):
        if '"translations"' not in line:
            continue
        e = json.loads(line)
        if e.get("lang_code") != own_lang:
            continue
        w = (e.get("word") or "").lower()
        if not w:
            continue
        pos = POS.get(e.get("pos") or "", "")
        for t in e.get("translations") or []:
            if t.get("lang_code") != want_lang:
                continue
            other = (t.get("word") or "").lower().strip()
            if other and " " not in other or (other and other.count(" ") <= 2):
                out[w].add((other, pos))
        n += 1
    sys.stderr.write(f"  {os.path.basename(path)}: {n:,} entries with translations\n")
    return out


def main(d):
    it2es = read(os.path.join(d, "it.jsonl.gz"), "it", "es")
    es2it = read(os.path.join(d, "es.jsonl.gz"), "es", "it")

    # merge into one Spanish-keyed table, remembering which way it was found
    merged = collections.defaultdict(dict)
    for it, pairs in it2es.items():
        for es, pos in pairs:
            merged[es].setdefault(it, set()).add(pos)
    for es, pairs in es2it.items():
        for it, pos in pairs:
            merged[es].setdefault(it, set()).add(pos)

    out = {es: {it: sorted(p - {""}) for it, p in v.items()}
           for es, v in merged.items()}
    json.dump(out, open("data/direct_dict.json", "w"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"\nItalian entries offering Spanish : {len(it2es):,}")
    print(f"Spanish entries offering Italian : {len(es2it):,}")
    print(f"Spanish words in the merged table: {len(out):,}")
    for probe in ("perro", "tiempo", "mejor", "contra", "spesso", "faltar"):
        if probe in out:
            print(f"  {probe:<10} {dict(list(out[probe].items())[:5])}")


if __name__ == "__main__":
    main(sys.argv[1])
