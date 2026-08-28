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
    words = {w["es"]: w for w in json.load(open("data/wordlist.json"))}
    defs = json.load(open("data/definitions.json"))
    prompts = json.load(open("data/prompts_new.json"))

    deck = []
    for es, entry in defs.items():
        w = words[es]
        by_pos = {pos: [{"it": i["it"], "pct": i["pct"]} for i in items]
                  for pos, items in entry["by_pos"].items()}
        senses, seen = [], set()
        for items in by_pos.values():
            for i in items:
                if i["it"] not in seen:
                    seen.add(i["it"])
                    senses.append(i["it"])
        deck.append({
            "id": es, "es": es, "it": senses[0],
            "senses": senses,
            "pos": w["pos"][0], "pos_all": w["pos"],
            "by_pos": by_pos,
            "bucket": bucket(es, senses[0]),
            "tier": w["tier"], "zipf": w["zipf"],
        })
    deck.sort(key=lambda c: -c["zipf"])

    out_prompts = {}
    for it, answers in prompts.items():
        rows = []
        for a in answers:
            row = {"es": a["es"], "pos": a["pos"] or None}
            if a.get("share") is not None:
                row["pct"] = a["share"]
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
