"""Extract Spanish->Italian lemma pairs from the Apertium bilingual dictionary.

Apertium is machine-translation data, so entries are citation forms by
construction -- which is what lets us filter the frequency spine down to
lemmas without lemmatizing anything. Membership in this dictionary IS the
citation-form test.

Caveat: it is built for MT, not for learners. Some pairs are domain-skewed
(alero -> pallacanestro) and some are junk. Anything that reaches a card
still needs checking against Wiktionary.
"""
import xml.etree.ElementTree as ET

DIX = "vendor/apertium-spa-ita/apertium-spa-ita.spa-ita.dix"

# Parts of speech worth making cards from. Closed-class items are excluded:
# Italian supplies them, and they are learned through grammar, not drilling.
CONTENT_POS = {"n", "vblex", "adj", "adv", "vbmod", "vbhaver", "vbser"}


def _surface(node):
    """Flatten an <l>/<r> node into its lemma string and POS tag."""
    parts = [node.text or ""]
    pos = None
    for child in node:
        if child.tag == "b":
            parts.append(" ")
        elif child.tag == "s" and pos is None:
            pos = child.get("n")
        parts.append(child.tail or "")
    return "".join(parts).strip(), pos


def load():
    root = ET.parse(DIX).getroot()
    section = root.find("section")
    pairs = {}
    for e in section.findall("e"):
        p = e.find("p")
        if p is None:
            continue
        l, r = p.find("l"), p.find("r")
        if l is None or r is None:
            continue
        spa, pos_s = _surface(l)
        ita, pos_i = _surface(r)
        if not spa or not ita or pos_s not in CONTENT_POS:
            continue
        # keep the first translation only; Apertium orders by preference
        pairs.setdefault(spa, {"it": ita, "pos": pos_s})
    return pairs


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


def similarity(a, b):
    if not a or not b:
        return 0.0
    return 1 - levenshtein(a, b) / max(len(a), len(b))


def bucket(sim):
    if sim == 1.0:
        return "identical"
    if sim >= 0.75:
        return "near"        # almost the same
    if sim >= 0.45:
        return "shifted"     # similar but not quite -- the interesting one
    return "distinct"        # completely different


if __name__ == "__main__":
    pairs = load()
    print(f"content-word pairs: {len(pairs)}")
    import collections
    b = collections.Counter(bucket(similarity(s, v["it"])) for s, v in pairs.items())
    for k in ("identical", "near", "shifted", "distinct"):
        print(f"  {k:10s} {b[k]:5d}  ({100*b[k]/len(pairs):.1f}%)")
