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

# Cutting the top 200 by rank was too blunt: it took `ser`, `estar`, `tener`,
# `hacer`, `ir`, `decir`, `ver`, `poder`, `casa`, `día` and seventy more with
# it -- the most useful words in the language. What actually needs excluding is
# the closed class plus forms that are not citation forms at all.
FUNCTION_WORDS = set("""
el la los las un una unos unas lo al del
de a en con por para sin
y e o u que ni si
yo tu tú él ella usted nosotros nosotras vosotros vosotras ellos ellas ustedes
me te se nos os le les mi mis su sus nuestro nuestra nuestros nuestras
mío mía tuyo tuya suyo suya
este esta esto estos estas ese esa eso esos esas aquel aquella aquello
aquellos aquellas
qué quién quiénes cuál cuáles cómo dónde adónde cuándo cuánto cuánta
cuántos cuántas cuyo cuya quien quienes cual cuales
""".split())

# Apertium lists these, but they are contractions, apocopated forms, conjugated
# forms or superseded spellings -- not words to put on a card.
NOT_LEMMAS = set("""
hay sólo aún aun gran primer buen algún ningún tercer
""".split())

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
    skip = FUNCTION_WORDS | NOT_LEMMAS
    out = []
    for w in forms:
        if w in skip or not w.isalpha() or len(w) < 2:
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
