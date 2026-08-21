"""Build the Spanish frequency spine, with Italian frequency alongside.

No lemmatization: words come straight from wordfreq's ranked lists. Inflected
forms are removed later by a membership test against the dictionary, not by
mapping anything onto a lemma.

Zipf is a log scale where 7 is roughly `de` and 3 is roughly rare. It is
comparable across languages, which is the whole point of carrying the Italian
score: a word that is common in Spanish but rare in Italian is a real gap,
while one common in both is probably already yours.
"""
from wordfreq import top_n_list, zipf_frequency

# The closed-class layer. Italian hands these over essentially intact, so they
# are noise in a deck built for this learner.
FUNCTION_CUTOFF = 200

TIERS = [
    ("core",      6.0, 9.0),
    ("common",    5.0, 6.0),
    ("useful",    4.5, 5.0),
    ("extended",  4.0, 4.5),
    ("long_tail", 3.5, 4.0),
]


def tier_for(z):
    for name, lo, hi in TIERS:
        if lo <= z < hi:
            return name
    return None


def build(n=8000):
    forms = top_n_list("es", n)
    skip = set(forms[:FUNCTION_CUTOFF])
    out = []
    for w in forms:
        if w in skip or not w.isalpha() or len(w) < 3:
            continue
        z_es = zipf_frequency(w, "es")
        tier = tier_for(z_es)
        if tier is None:
            continue
        out.append({"es": w, "zipf_es": round(z_es, 2), "tier": tier})
    return out


def gap_score(word, z_es):
    """How much Italian fails to help. Higher means more worth learning."""
    z_it = zipf_frequency(word, "it")
    return round(z_es - z_it, 2), round(z_it, 2)


if __name__ == "__main__":
    import json, sys, collections
    rows = build()
    counts = collections.Counter(r["tier"] for r in rows)
    print("candidates per tier:")
    for name, _, _ in TIERS:
        print(f"  {name:10s} {counts[name]:5d}")
    print(f"\ntotal: {len(rows)}")
    json.dump(rows, open("data/frequency_es.json", "w"), ensure_ascii=False, indent=1)
    print("wrote data/frequency_es.json")
