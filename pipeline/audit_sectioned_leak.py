"""Cards whose figure is really measuring a reading that was sectioned away.

`contra` is a preposition, an adverb and -- marginally -- a noun. The
preposition goes to its section and the noun survives, carrying a 54% share
that is actually the two prepositions co-occurring: that is what those words
mostly are, and the corpus counts spellings. The card then prints a
preposition's frequency against a noun nobody uses.

Sharing a part of speech is not the tell -- `gracias`, `ojo` and `fuego` all
double as exclamations and are perfectly good cards. The tell is in the tagged
alignment: what does *this reading* actually align to? A Spanish noun whose own
best answer is an Italian preposition is not being measured as a noun.
"""
import csv
import json

SECTIONED = {"pr", "det", "ij", "prn", "cnj"}
CONTENT = {"n", "adj", "adv", "vblex"}


def main():
    defs = json.load(open("data/definitions.json"))
    lex = {r["spanish"]: r for r in csv.DictReader(open("content/lexicon.csv"))}
    by_reading = json.load(open("data/aligned_pos.json"))

    rows = []
    for es, entry in defs.items():
        for pos, items in entry["by_pos"].items():
            if pos not in CONTENT:
                continue
            top = (by_reading.get(f"{es}|{pos}") or [[None]])[0][0]
            if not top or "|" not in str(top):
                continue
            answer_pos = str(top).split("|")[1]
            if answer_pos in SECTIONED:
                rows.append((items[0]["pct"] or 0, es, pos, items[0]["it"],
                             str(top), lex.get(es, {}).get("band", "?")))
    rows.sort(reverse=True)
    print(f"readings whose own best alignment is glue: {len(rows)}\n")
    print(f"{'band':<8}{'spanish':<14}{'as':<5}{'card says':<14}{'pct':>6}  aligns to")
    for pct, es, pos, it, top, band in rows:
        print(f"  {band:<8}{es:<14}{pos:<5}{it:<14}{pct:>5.1f}%  {top}")
    return rows


if __name__ == "__main__":
    main()
