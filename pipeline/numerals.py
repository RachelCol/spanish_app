"""Numerals, which the ordinary pipeline cannot see.

Apertium defines numerals by paradigm reference rather than with inline <s>
tags, so every numeral entry arrives with an empty tag list and is dropped by
the CONTENT_POS test in pairs.py. Nothing is wrong with the data -- the pairs
are all there -- so this reads them back out for a fixed, curated set: one to
twenty, the tens, and a hundred.

The Italian side still comes from the dictionary, not from me. Where an entry
offers several candidates, one carrying a `num` tag wins -- that is what keeps
`uno` the number rather than `un` the article -- and otherwise the most
frequent Italian word does, which is the rule pairs.py uses and is what picks
`tre` over the truncated `tr`.

Tier is deliberately not read off corpus frequency here. Bands exist to order
an open-ended vocabulary, and `dieciséis` being rarer in print than `dos` does
not mean you learn it two years later: the numbers are a closed set learned as
a block. Banding them individually would scatter them across five tiers and
hide most of them behind the default deck filters.
"""
import collections
import xml.etree.ElementTree as ET
from wordfreq import zipf_frequency

from pairs import similarity, bucket
from frequency import tier_for

DIX = "vendor/apertium-spa-ita/apertium-spa-ita.spa-ita.dix"

# One to twenty, then the tens, then a hundred. `cien` and `ciento` are the
# same number in two shapes, and both are worth knowing.
# One band for the whole set -- see the note above. `common` is on by default.
TIER = "common"

WANTED = """
uno dos tres cuatro cinco seis siete ocho nueve diez
once doce trece catorce quince dieciséis diecisiete dieciocho diecinueve veinte
treinta cuarenta cincuenta sesenta setenta ochenta noventa
cien ciento
""".split()


def _text(node):
    """Apertium writes a space as <b/>, which itertext() drops."""
    out = []
    for n in node.iter():
        if n.tag == "b":
            out.append(" ")
        if n.tag == "s":
            continue
        if n.text:
            out.append(n.text)
        if n.tail:
            out.append(n.tail)
    return "".join(out).strip()


def candidates(path=DIX):
    found = collections.defaultdict(collections.Counter)
    root = ET.parse(path).getroot()
    for e in root.iter("e"):
        p = e.find("p")
        if p is None:
            continue
        l, r = p.find("l"), p.find("r")
        if l is None or r is None:
            continue
        es, it = _text(l), _text(r)
        if es in WANTED and it and " " not in it:
            is_num = any(s.get("n") == "num" for s in p.iter("s"))
            found[es][it] += 100 if is_num else 1
    return found


def build(path=DIX):
    found = candidates(path)
    cards = []
    for es in WANTED:
        options = found.get(es)
        if not options:
            continue
        # A `num` reading wins outright; otherwise the commoner Italian word.
        it = max(options, key=lambda w: (options[w] >= 100, zipf_frequency(w, "it")))
        z = zipf_frequency(es, "es")
        cards.append({
            "id": es,
            "es": es,
            "it": it,
            "senses": [it],
            "pos": "num",
            "pos_all": ["num"],
            "bucket": bucket(similarity(es, it)),
            "tier": TIER,
            "zipf": z,
        })
    return cards


if __name__ == "__main__":
    for c in build():
        print(f"  {c['es']:12s} -> {c['it']:12s} {c['bucket']:9s} "
              f"{c['tier']:9s} z={c['zipf']:.2f}")
