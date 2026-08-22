"""Emit the deck the app actually loads.

Drops the pairs flagged by the frequency-mismatch check, assigns stable ids,
and keeps only the fields the UI needs. Everything else stays in the
intermediate files so the provenance is still there.
"""
import json

SUSPECT_DELTA = 1.2


def build():
    cards = json.load(open("data/paired.json"))
    out = []
    for c in cards:
        delta = c["zipf_es"] - c["zipf_it"]
        if c["zipf_it"] == 0.0 or delta >= SUSPECT_DELTA:
            continue
        out.append({
            "id": c["es"],          # Spanish lemma is unique in the pair set
            "es": c["es"],
            "it": c["it"],
            "senses": c["senses"],
            "pos": c["pos"],
            "bucket": c["bucket"],
            "tier": c["tier"],
            "zipf": c["zipf_es"],
        })
    # Most frequent first: the deck should introduce useful words early.
    out.sort(key=lambda c: -c["zipf"])
    return out


if __name__ == "__main__":
    deck = build()
    json.dump(deck, open("data/deck.json", "w"), ensure_ascii=False, separators=(",", ":"))
    import collections, os
    print(f"deck: {len(deck)} cards -> data/deck.json ({os.path.getsize('data/deck.json')/1024:.0f} KB)")
    for k, v in collections.Counter(c["bucket"] for c in deck).most_common():
        print(f"  {k:10s} {v}")
    print()
    for k, v in collections.Counter(c["tier"] for c in deck).most_common():
        print(f"  {k:10s} {v}")
