"""Cross-check every pairing against English Wiktionary, through meaning.

The deck's translations come from one source. That was fine until it wasn't:
`dovere -> tener`, `successo -> suceso`, `oltre -> allende` all shipped because
nothing independent ever looked at them. A second opinion is not a filter --
tested, Wiktionary is wrong often enough that filtering on it would cut good
cards -- but it is a very good way to decide which of 3,400 pairings are worth
reading by hand.

English is the pivot, and never reaches a card. English Wiktionary defines
Italian and Spanish words in English, so `dovere` glosses as "duty, must" and
`deber` glosses as "duty, must, owe"; a shared content word is evidence the two
mean the same thing. `tener` glosses as "have, hold, own" and shares nothing
with `dovere`, which is exactly the signal that was missing.

Scope is every Italian sense a card carries, not only the ones that became
prompts. A Spanish answer opens its own entry listing all of its senses, so
all of them are on screen and all of them need checking -- 293 were visible
and unaudited when this only followed the prompt map.

Writes data/crosscheck.json, keyed by Spanish word: for each of its Italian
senses, a verdict of `agree`, `differ` or `unknown`. Nothing here changes a
card.
"""
import json
import re
import sys
from collections import defaultdict

# Words too common in a definition to be evidence of anything.
STOP = set("""
a an the of to in on for with by from as at or and not is are be being been
that this these those it its his her their your our my one any some such
something someone anything person thing which who whom what when where how
used use usually especially typically often also more most very much many
form forms sense senses figuratively literally transitive intransitive
reflexive auxiliary plural singular masculine feminine noun verb adjective
adverb pronoun preposition conjunction interjection archaic obsolete dated
colloquial informal formal slang chiefly esp e g i e etc etc
""".split())

WORD = re.compile(r"[a-z]+")


def content(gloss):
    """The words in a definition that carry its meaning."""
    gloss = re.sub(r"\([^)]*\)", " ", gloss.lower())
    # Two letters counts. `be`, `go`, `do` carry the whole meaning of a gloss,
    # and dropping them scored `essere -> estar` as a disagreement when both
    # sides simply said "be".
    return {w for w in WORD.findall(gloss) if w not in STOP and len(w) > 1}


def read_glosses(path, wanted, lang_code):
    """word -> set of meaning-bearing English words, for the words we care about."""
    out = defaultdict(set)
    with open(path, errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("lang_code") != lang_code:
                continue
            w = r.get("word")
            if w not in wanted:
                continue
            for s in r.get("senses") or []:
                for g in s.get("glosses") or []:
                    out[w] |= content(g)
    return out


def main(it_path, es_path, out_path="data/crosscheck.json"):
    deck = json.load(open("data/deck.json"))
    senses = {c["es"]: list(dict.fromkeys([c["it"]] + list(c["senses"])))
              for c in deck}
    es_words = set(senses)
    it_words = {s for v in senses.values() for s in v}

    sys.stderr.write("reading Italian glosses ...\n")
    it_gloss = read_glosses(it_path, it_words, "it")
    sys.stderr.write("reading Spanish glosses ...\n")
    es_gloss = read_glosses(es_path, es_words, "es")

    out = {}
    tally = defaultdict(int)
    for es, its in senses.items():
        ge = es_gloss.get(es)
        rows = []
        for it in its:
            gi = it_gloss.get(it)
            if not gi or not ge:
                verdict, shared = "unknown", []
            else:
                shared = sorted(gi & ge)
                verdict = "agree" if shared else "differ"
            tally[verdict] += 1
            rows.append({"it": it, "verdict": verdict, "shared": shared[:6]})
        out[es] = rows

    json.dump(out, open(out_path, "w"), ensure_ascii=False, separators=(",", ":"))
    total = sum(tally.values())
    print(f"{total} pairings checked -> {out_path}")
    for k in ("agree", "differ", "unknown"):
        print(f"  {k:8s} {tally[k]:5d}  ({100*tally[k]//total}%)")
    print(f"\n  Italian words with glosses : {len(it_gloss)} of {len(it_words)}")
    print(f"  Spanish words with glosses : {len(es_gloss)} of {len(es_words)}")
    print(f"  (every sense a detail card shows, not only prompts)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
