"""Write every pairing to a CSV for review in a spreadsheet.

The audit so far has been mine. This puts the same material in front of you,
in the order worth reading it, with the machine's verdict alongside so the
suspicious ones stand out -- and with two empty columns to fill in.

Round trip:

    python pipeline/export_review.py          # writes review.csv
    (open in Google Sheets, fill in `call` and `note`)
    (File > Download > CSV, save as content/review.csv)
    python pipeline/build_pairs.py            # your calls are applied

`call` understands `drop` -- remove this Italian sense from this Spanish card.
Anything else is treated as "leave it alone". Corrections go in `note` rather
than being applied automatically: removing a sense can only cost a card, but
asserting one can teach a wrong word, and that is how `dovere -> tener` got in.
"""
import csv
import json
import os

from wordfreq import zipf_frequency

BAND_ORDER = {"core": 0, "common": 1, "useful": 2, "extended": 3, "long_tail": 4}


def main(out="review.csv"):
    deck = json.load(open("data/deck.json"))
    prompts = json.load(open("data/prompts.json"))
    cc = json.load(open("data/crosscheck.json"))
    existing = load_decisions()

    asks = {(a["es"], it) for it, ans in prompts.items() for a in ans}

    rows = []
    for card in deck:
        verdicts = {r["it"]: r for r in cc.get(card["es"], [])}
        senses = list(dict.fromkeys([card["it"]] + list(card["senses"])))
        for it in senses:
            v = verdicts.get(it, {})
            key = (card["es"], it)
            rows.append({
                "band": card["tier"],
                "es_zipf": f"{card['zipf']:.2f}",
                "it_zipf": f"{zipf_frequency(it, 'it'):.2f}",
                "italian": it,
                "spanish": card["es"],
                "asked": "yes" if key in asks else "",
                "card_shows": ", ".join(s for s in senses if s != it),
                "check": v.get("verdict", "unknown"),
                "shared_meaning": " ".join(v.get("shared", [])[:4]),
                "call": existing.get(key, ("", ""))[0],
                "note": existing.get(key, ("", ""))[1],
            })

    rows.sort(key=lambda r: (BAND_ORDER.get(r["band"], 9), -float(r["it_zipf"])))
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"{len(rows)} pairings -> {out}")
    for band in ("core", "common", "useful", "extended", "long_tail"):
        n = sum(1 for r in rows if r["band"] == band)
        flagged = sum(1 for r in rows if r["band"] == band and r["check"] != "agree")
        print(f"  {band:10s} {n:5d}   ({flagged} the check is unsure about)")
    if existing:
        print(f"\n  carried over {len(existing)} calls you had already made")


DECISIONS = "content/review.csv"


def load_decisions(path=DECISIONS):
    """Your reviewed CSV, if it is there. Returns {(spanish, italian): (call, note)}."""
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            call = (r.get("call") or "").strip().lower()
            note = (r.get("note") or "").strip()
            if call or note:
                out[(r["spanish"], r["italian"])] = (call, note)
    return out


def dropped(path=DECISIONS):
    """The pairings you marked `drop`."""
    return {k for k, (call, _) in load_decisions(path).items() if call == "drop"}


if __name__ == "__main__":
    main()
