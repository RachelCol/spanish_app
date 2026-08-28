"""Step 2: an Italian definition for each Spanish word, by part of speech.

The dictionary proposes and the corpus decides. Candidate Italian words come
from Apertium and Wiktionary, which know what *can* translate a word; the
aligned corpus says which of them actually do, how often, and in what order.
Neither alone is enough -- the corpus by itself misses `no -> non`, and the
dictionaries by themselves gave us `dovere -> tener`.

Two numbers per sense, and they answer different questions. The alignment
probability decides -- it is how often, when this Spanish word is translated,
it comes out as this Italian one, and it is what ranks and trims. The corpus
percentage is displayed -- it is how often the Italian word appears at all in
sentences containing the Spanish one, so a low figure means the sentence is
usually restructured, which is worth seeing.

Three things come out besides the definitions, all for review rather than for
the deck:

  additions   an Italian word the corpus attests above the threshold that no
              dictionary lists. Say `yes` and it joins that definition.
  dropped     a part of speech with no attested translation, and the word it
              was dropped from.
  thin        a word the corpus has too little evidence about to judge.
"""
import collections
import csv
import json
import sys
import unicodedata
import xml.etree.ElementTree as ET

sys.path.insert(0, "pipeline")
from pairs import _surface, DIX          # noqa: E402

RELATIVE = 15.0        # keep anything within this % of the top translation
MIN_PAIRS = 30         # below this the corpus has no opinion worth having
MIN_PROB = 0.01        # an alignment weaker than this is noise
ADD_PROB = 0.15        # what an unlisted word must reach to be worth reviewing

# Apertium's Spanish-side tags, grouped the way the app groups them.
GROUP = {"vblex": "vblex", "vbmod": "vblex", "vbhaver": "vblex", "vbser": "vblex",
         "adv": "adv", "preadv": "adv", "cnjcoo": "cnj", "cnjsub": "cnj",
         "cnjadv": "cnj", "n": "n", "adj": "adj", "pr": "pr", "prn": "prn",
         "det": "det", "ij": "ij", "num": "num"}


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def dictionary(wikt_it2es_path):
    """spanish -> {italian -> {spanish parts of speech it was listed under}}"""
    out = collections.defaultdict(lambda: collections.defaultdict(set))
    root = ET.parse(DIX).getroot()
    for e in root.find("section").findall("e"):
        p = e.find("p")
        if p is None:
            continue
        l, r = p.find("l"), p.find("r")
        if l is None or r is None:
            continue
        es, pos_es = _surface(l)
        it, _ = _surface(r)
        if not es or not it:
            continue
        out[norm(es)][norm(it)].add(GROUP.get(pos_es or "", ""))
    # Wiktionary knows nothing about which Spanish part of speech, so its
    # candidates are offered to every part of speech the word has.
    for it, esl in json.load(open(wikt_it2es_path)).items():
        for es in esl:
            out[norm(es)][norm(it)].add("")
    return out


def build(wikt_it2es_path):
    words = json.load(open("data/wordlist.json"))
    matrix = json.load(open("data/matrix.json"))
    aligned = json.load(open("data/aligned.json"))
    it_pos = json.load(open("data/italian_pos.json"))
    dic = dictionary(wikt_it2es_path)

    defs, additions, dropped, thin = {}, [], [], []

    for w in words:
        es, poss = w["es"], w["pos"]
        nes = norm(es)
        entry = matrix.get(es)
        if not entry or entry["pairs"] < MIN_PAIRS:
            thin.append({"spanish": es, "pos": ",".join(poss),
                         "pairs": entry["pairs"] if entry else 0})
            continue

        pct = {it: p for it, p in entry["it"]}
        prob = {it: p for it, p in aligned.get(es, [])}
        proposed = dic.get(nes, {})

        # what the dictionary offers, ranked by how often it is the alignment
        scored = sorted(((prob.get(it, 0.0), it) for it in proposed), reverse=True)
        attested = [(p, it) for p, it in scored if p >= MIN_PROB]

        if attested:
            top = attested[0][0]
            keep = [(it, p) for p, it in attested if 100 * p / top >= RELATIVE]
        else:
            keep = []

        # Organise by the Spanish word's parts of speech. Apertium says which
        # Spanish part of speech it listed a pair under; where it does not --
        # Wiktionary's candidates carry none -- the Italian word's own part of
        # speech decides, which is what separates `meglio` the adverb from
        # `migliore` the adjective on a word that is both.
        by_pos = {}
        for pos in poss:
            here = []
            for it, p in keep:
                tagged = proposed[it] - {""}
                if tagged:
                    if pos in tagged:
                        here.append((it, p))
                elif pos in it_pos.get(it, []) or not it_pos.get(it):
                    here.append((it, p))
            if not here:
                here = [(it, p) for it, p in keep
                        if not proposed[it] - {""} or pos in proposed[it]]
            if here:
                by_pos[pos] = [{"it": it, "prob": round(p, 3),
                                "pct": round(pct.get(it, 0.0), 1)} for it, p in here]
        for pos in poss:
            if pos not in by_pos:
                dropped.append({"spanish": es, "dropped_pos": pos,
                                "kept": ",".join(sorted(by_pos)) or "nothing"})
        if not by_pos:
            continue
        defs[es] = {"pairs": entry["pairs"], "by_pos": by_pos}

        # what the alignment found that no dictionary lists
        cutoff = keep[0][1] * RELATIVE / 100 if keep else 0
        for it, p in aligned.get(es, []):
            if it in proposed or not cutoff or p < cutoff or p < ADD_PROB:
                continue
            additions.append({"spanish": es, "italian": it,
                              "prob": round(p, 3),
                              "pct": round(pct.get(it, 0.0), 1),
                              "of_top": round(100 * p / keep[0][1]),
                              "band": w["tier"], "add": ""})

    return defs, additions, dropped, thin


def write_csv(path, rows, fields):
    with open(path, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields)
        wr.writeheader()
        wr.writerows(rows)


if __name__ == "__main__":
    wikt = sys.argv[1]
    defs, additions, dropped, thin = build(wikt)
    json.dump(defs, open("data/definitions.json", "w"),
              ensure_ascii=False, separators=(",", ":"))
    additions.sort(key=lambda r: -r["prob"])
    write_csv("review_additions.csv", additions,
              ["band", "spanish", "italian", "prob", "pct", "of_top", "add"])
    write_csv("review_dropped_pos.csv", dropped, ["spanish", "dropped_pos", "kept"])
    write_csv("review_thin.csv", thin, ["spanish", "pos", "pairs"])

    print(f"{len(defs)} Spanish words defined -> data/definitions.json")
    n_senses = sum(len(v) for d in defs.values() for v in d["by_pos"].values())
    print(f"  {n_senses} Italian senses across them")
    print(f"\n  review_additions.csv    {len(additions):5d}  corpus found, no dictionary lists")
    print(f"  review_dropped_pos.csv  {len(dropped):5d}  parts of speech with no translation")
    print(f"  review_thin.csv         {len(thin):5d}  too little corpus evidence")
