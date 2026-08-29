"""Cards whose answer is an Italian light verb standing in for a phrase.

Italian says `fare colazione`, `fare male`, `andare a letto`. Alignment sees
the light verb, which carries none of the meaning, and hands it to the Spanish
word as though it were the translation -- so `desayunar` answered `fare`, and
the `fare` prompt then reached `desayunar` as one of its Spanish words.

The check is cheap and worth re-running after any rebuild. A light verb is
only wrong here when it is not the word's real one-word equivalent, which is
what TRUE lists.
"""
import csv
import json

LIGHT = {"fare", "andare", "stare", "dare", "avere", "essere", "mettere",
         "prendere", "venire", "tenere", "portare", "trovare"}

TRUE = {("hacer", "fare"), ("ir", "andare"), ("estar", "stare"),
        ("dar", "dare"), ("haber", "avere"), ("tener", "avere"),
        ("ser", "essere"), ("estar", "essere"), ("poner", "mettere"),
        ("meter", "mettere"), ("colocar", "mettere"), ("tomar", "prendere"),
        ("coger", "prendere"), ("agarrar", "prendere"), ("atrapar", "prendere"),
        ("venir", "venire"), ("llevar", "portare"), ("traer", "portare"),
        ("portar", "portare"), ("encontrar", "trovare"), ("hallar", "trovare")}


def main():
    defs = json.load(open("data/definitions.json"))
    lex = {r["spanish"]: r for r in csv.DictReader(open("content/lexicon.csv"))}
    rows = []
    for es, entry in defs.items():
        senses = [(i["it"], i["pct"] or 0)
                  for items in entry["by_pos"].values() for i in items]
        if not senses:
            continue
        it, pct = max(senses, key=lambda s: s[1])
        if it in LIGHT and (es, it) not in TRUE:
            rows.append((pct, es, it, lex.get(es, {}).get("band", "?")))
    rows.sort()
    print(f"light-verb answers that are probably phrase fragments: {len(rows)}")
    for pct, es, it, band in rows:
        print(f"   {band:<7} {es:<14} -> {it:<9} {pct:5.1f}%")
    return rows


if __name__ == "__main__":
    main()
