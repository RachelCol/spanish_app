"""Steps 4 and 5: turn the new pipeline's output into what the app loads.

data/deck.json     one entry per Spanish word: its parts of speech, its Italian
                   definitions grouped by part of speech, each with the share
                   of sentence pairs it accounts for.
data/prompts.json  one entry per Italian word: the Spanish words that answer
                   it, commonest first, each with its share.

Closeness to Italian is still measured here rather than counted, since it is a
fact about spelling rather than usage.
"""
import json

import editorial

from wordfreq import zipf_frequency


def levenshtein(a, b):
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def bucket(a, b):
    if not a or not b:
        return "distinct"
    sim = 1 - levenshtein(a, b) / max(len(a), len(b))
    if sim == 1.0:
        return "identical"
    if sim >= 0.75:
        return "near"
    if sim >= 0.45:
        return "shifted"
    return "distinct"


def main():
    import csv
    words = {}
    with open("content/lexicon.csv", newline="") as fh:
        for r in csv.DictReader(fh):
            words[r["spanish"]] = {"es": r["spanish"], "pos": r["pos"].split(),
                                   "tier": r["band"], "zipf": float(r["zipf"])}
    defs = json.load(open("data/definitions.json"))
    prompts = json.load(open("data/prompts_new.json"))

    # Prepositions, articles and interjections are taught in their own
    # sections. What matters about a preposition is which words it goes with,
    # which a translation card cannot show.
    SECTIONED = editorial.SECTIONED

    # Fixed phrases are cards but not lexicon rows, so give them a band from
    # the word they replaced.
    try:
        phrases = json.load(open("data/phrases.json"))
    except FileNotFoundError:
        phrases = {}
    for p, v in phrases.items():
        base = words.get(v["replaces"])
        words[p] = {"es": p, "pos": ["phrase"],
                    "tier": base["tier"] if base else "common",
                    "zipf": base["zipf"] if base else 4.5}

    deck = []
    for es, entry in defs.items():
        w = words.get(es)
        if not w:
            continue
        by_pos = {pos: [{"it": i["it"], "pct": i["pct"]} for i in items]
                  for pos, items in entry["by_pos"].items()
                  if pos not in SECTIONED}
        if not by_pos:
            continue
        # Ordered by measured share across every reading, not by the order the
        # parts of speech happen to sit in. `pesar` is a noun and a verb, and
        # taking the noun first led the card with `nonostante` at 1.7% ahead of
        # `pesare` at 5.7% -- the phrase meaning in front of the word's own.
        senses, seen = [], set()
        ranked_pos = sorted(
            by_pos.values(),
            key=lambda items: -max((i["pct"] or 0) for i in items))
        for items in ranked_pos:
            for i in items:
                if i["it"] not in seen:
                    seen.add(i["it"])
                    senses.append(i["it"])
        deck.append({
            "id": es, "es": es, "it": senses[0],
            "senses": senses,
            "pos": sorted(by_pos)[0],
            "pos_all": [p for p in w["pos"] if p in by_pos],
            "by_pos": by_pos,
            **({"see_also": entry["see_also"]} if entry.get("see_also") else {}),
            "bucket": bucket(es, senses[0]),
            "tier": w["tier"], "zipf": w["zipf"],
        })
    deck.sort(key=lambda c: -c["zipf"])

    out_prompts = {}
    for it, answers in prompts.items():
        rows = []
        for a in answers:
            row = {"es": a["es"], "pos": a["pos"] or None}
            # the corpus share, not the split between answers
            if a.get("pct") is not None:
                row["pct"] = a["pct"]
            if a.get("share") is not None:
                row["rank"] = a["share"]
            if a.get("off_list"):
                row["off"] = True
            rows.append(row)
        out_prompts[it] = rows

    json.dump(deck, open("data/deck.json", "w"),
              ensure_ascii=False, separators=(",", ":"))
    json.dump(out_prompts, open("data/prompts.json", "w"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"{len(deck)} cards -> data/deck.json")
    print(f"{len(out_prompts)} prompts -> data/prompts.json")
    import collections
    for k, v in collections.Counter(c["tier"] for c in deck).most_common():
        print(f"  {k:10s} {v}")
    print()
    for k, v in collections.Counter(c["bucket"] for c in deck).most_common():
        print(f"  {k:10s} {v}")

    try:
        import changes
        open("changes.md", "w").write(changes.report())
        print("\nchange log written to changes.md")
    except Exception as err:
        print(f"\n(change log failed: {err})")


if __name__ == "__main__":
    main()
