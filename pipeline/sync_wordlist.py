"""Keep data/wordlist.json a superset of content/lexicon.csv.

There are two Spanish word lists and they are not the same thing. The lexicon
is the curated list of what to study. wordlist.json is wider on purpose: the
corpus steps need words we do *not* teach, so that step 3 can show a Spanish
word from outside the deck when it genuinely translates an Italian one.

Wider must still mean wider. build_matrix and build_italian read wordlist.json
alone, so a word in the lexicon but missing here gets no corpus data at all --
which is how `encantar` and `preferir` came to be added to the lexicon and then
produce no card, along with 37 others, nearly all of them pronominal verbs the
older surface-frequency list never reached.
"""
import csv
import json

TIERS = {"first", "core", "common", "useful", "wider"}


def main():
    words = json.load(open("data/wordlist.json"))
    have = {w["es"]: w for w in words}
    added = []
    for r in csv.DictReader(open("content/lexicon.csv")):
        es = r["spanish"]
        if es in have:
            have[es]["tier"] = r["band"]        # the lexicon owns the banding
            continue
        words.append({"es": es, "pos": r["pos"].split(),
                      "zipf": float(r["zipf"] or 0), "tier": r["band"]})
        added.append(es)
    json.dump(words, open("data/wordlist.json", "w"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"wordlist: {len(words)} words ({len(added)} taken from the lexicon)")
    if added:
        print("  " + ", ".join(added[:20]) + (" ..." if len(added) > 20 else ""))


if __name__ == "__main__":
    main()
