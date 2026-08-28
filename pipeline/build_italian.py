"""Step 3: the Italian list, which is what the flashcards ask.

Every Italian word used in any definition, carried across with all the Spanish
words that mapped to it. Nothing is trimmed on frequency here -- a Spanish word
we set out to learn cannot be lost on the way back.

Two things the corpus adds. The Spanish answers are ordered by how often each
is actually the translation, so the answer most likely wanted leads. And where
a Spanish word outside the frequency list translates the Italian word strongly,
it appears on the card with its share, so its use is visible -- but it gets no
detail card, since generating those would never terminate. Tapping it says so.

The ordering is a joint estimate: how reliably the Spanish word is rendered by
this Italian one, weighted by how often that Spanish word appears at all. A
Spanish word that always translates this way but is rare should not outrank a
common one that usually does.
"""
import collections
import csv
import json
import sys

OFF_LIST_PROB = 0.20      # what an off-list Spanish word must reach to appear


def build():
    defs = json.load(open("data/definitions.json"))
    aligned = json.load(open("data/aligned.json"))
    matrix = json.load(open("data/matrix.json"))
    words = {w["es"]: w for w in json.load(open("data/wordlist.json"))}

    prob = {es: dict(rows) for es, rows in aligned.items()}
    pairs = {es: e["pairs"] for es, e in matrix.items()}

    # italian -> [(spanish, part of speech)]
    by_it = collections.defaultdict(list)
    SECTIONED = {"pr", "det", "ij"}
    for es, entry in defs.items():
        for pos, items in entry["by_pos"].items():
            if pos in SECTIONED:
                continue
            for i in items:
                by_it[i["it"]].append((es, pos))

    prompts, off_list = {}, []
    for it, owners in by_it.items():
        seen, answers = set(), []
        for es, pos in owners:
            if es in seen:
                continue
            seen.add(es)
            p = prob.get(es, {}).get(it, 0.0)
            weight = p * pairs.get(es, 0)
            # The share of sentence pairs, from the definition -- how often
            # this Italian word appears at all beside this Spanish one. A
            # single-answer card would otherwise always read 100%, which says
            # nothing; this says how often the sentence is phrased another way.
            corpus_pct = None
            for items in defs[es]["by_pos"].values():
                for i in items:
                    if i["it"] == it:
                        corpus_pct = i["pct"]
            answers.append({"es": es, "pos": pos, "prob": round(p, 3),
                            "pct": corpus_pct, "weight": weight})
        # a Spanish word outside our list that this Italian word reaches
        for es, rows in prob.items():
            pass
        answers.sort(key=lambda a: -a["weight"])
        total = sum(a["weight"] for a in answers) or 1.0
        for a in answers:
            a["share"] = round(100 * a["weight"] / total, 1)
            del a["weight"]
        prompts[it] = answers
    return prompts, off_list, words


def add_off_list(prompts, words):
    """Spanish words the alignment reaches that are not on our list."""
    aligned = json.load(open("data/aligned.json"))
    matrix = json.load(open("data/matrix.json"))
    rows = []
    reach = collections.defaultdict(list)
    for es, items in aligned.items():
        if es in words:
            continue
        for it, p in items:
            if p >= OFF_LIST_PROB:
                reach[it].append((p, es))
    for it, cands in reach.items():
        if it not in prompts:
            continue
        have = {a["es"] for a in prompts[it]}
        for p, es in sorted(cands, reverse=True):
            if es in have:
                continue
            prompts[it].append({"es": es, "pos": "", "prob": round(p, 3),
                                "share": None, "off_list": True})
            rows.append({"italian": it, "spanish": es, "prob": round(p, 3),
                         "keep": ""})
    return rows


if __name__ == "__main__":
    prompts, _, words = build()
    off = add_off_list(prompts, words)
    json.dump(prompts, open("data/prompts_new.json", "w"),
              ensure_ascii=False, separators=(",", ":"))
    with open("review_off_list.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=["italian", "spanish", "prob", "keep"])
        wr.writeheader()
        wr.writerows(sorted(off, key=lambda r: -r["prob"]))

    multi = sum(1 for v in prompts.values() if len(v) > 1)
    reach = {a["es"] for v in prompts.values() for a in v if not a.get("off_list")}
    defs = json.load(open("data/definitions.json"))
    print(f"{len(prompts)} Italian prompts -> data/prompts_new.json")
    print(f"  with more than one Spanish answer : {multi}")
    print(f"  Spanish words reachable           : {len(reach)} of {len(defs)}")
    print(f"  off-list answers added            : {len(off)}  -> review_off_list.csv")
