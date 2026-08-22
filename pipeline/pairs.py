"""Extract Spanish->Italian sense sets from the Apertium bilingual dictionary.

Apertium is machine-translation data, so entries are citation forms by
construction -- which is what lets the frequency spine be filtered to lemmas
without lemmatizing anything. Membership here IS the citation-form test.

Two things this deliberately does not do any more.

It no longer keeps only the first entry per word. Apertium lists senses in file
order, not in order of usefulness, so first-wins gave `haber -> dovere` (from
`haber de`) over `haber -> avere`, and `ante -> prima` over `ante -> davanti`.
Senses are now ranked and the best several kept.

It no longer trusts the part-of-speech tag blindly. Apertium tags `ser`,
`decir`, `ver` and `poder` as nouns; anything that looks like an infinitive is
corrected back to a verb.
"""
import xml.etree.ElementTree as ET
import collections
from wordfreq import zipf_frequency

DIX = "vendor/apertium-spa-ita/apertium-spa-ita.spa-ita.dix"

# Tags worth making cards from. Prepositions are included because Spanish
# prepositions are real vocabulary for an Italian speaker -- `ante`, `bajo`,
# `hacia`, `según` -- and because dropping them is what lost `davanti`.
CONTENT_POS = {"n", "vblex", "adj", "adv", "vbmod", "vbhaver", "vbser", "pr",
               "cnjcoo", "cnjsub", "cnjadv", "preadv"}

# How the Spanish tag ranks Italian senses: a preposition should be glossed by
# a preposition, not by an adverb that happens to be commoner.
POS_AFFINITY = {
    "pr": {"pr": 3, "adv": 1},
    "vblex": {"vblex": 3, "vbmod": 1, "vbhaver": 2, "vbser": 2},
    "vbhaver": {"vbhaver": 3, "vblex": 2, "vbmod": 0},
    "vbmod": {"vbmod": 3, "vblex": 2},
    "n": {"n": 3, "adj": 1},
    "adj": {"adj": 3, "n": 1},
    "adv": {"adv": 3, "pr": 1, "preadv": 2},
    "cnjcoo": {"cnjcoo": 3, "cnjsub": 2, "cnjadv": 2, "adv": 1},
    "cnjsub": {"cnjsub": 3, "cnjcoo": 2, "cnjadv": 2, "adv": 1},
    "cnjadv": {"cnjadv": 3, "cnjcoo": 2, "cnjsub": 2, "adv": 1},
    "preadv": {"preadv": 3, "adv": 2},
}

# An Italian tag with no entry in the affinity table scores neutrally, so
# frequency still decides rather than the sense being pushed to the bottom.
NEUTRAL_AFFINITY = 1

# When a word carries several tags equally often, prefer the ordinary ones.
# `bien` is tagged preadv, n and adv once each, and letting preadv win chose
# the apocopated `ben` over `bene`.
POS_PRIORITY = ["vblex", "n", "adj", "adv", "pr", "cnjcoo", "cnjsub", "cnjadv",
                "vbser", "vbhaver", "vbmod", "preadv"]

MAX_SENSES = 3


def _surface(node):
    """Flatten an <l>/<r> node into its lemma string and first POS tag."""
    parts = [node.text or ""]
    pos = None
    for child in node:
        if child.tag == "b":
            parts.append(" ")
        elif child.tag == "s" and pos is None:
            pos = child.get("n")
        parts.append(child.tail or "")
    return "".join(parts).strip(), pos


def _fix_pos(spa, pos):
    """Apertium calls plenty of infinitives nouns. The ending gives it away."""
    if pos == "n" and len(spa) > 3 and spa[-2:] in ("ar", "er", "ir") and " " not in spa:
        return "vblex"
    return pos


def load():
    root = ET.parse(DIX).getroot()
    section = root.find("section")

    raw = collections.defaultdict(list)
    for e in section.findall("e"):
        p = e.find("p")
        if p is None:
            continue
        l, r = p.find("l"), p.find("r")
        if l is None or r is None:
            continue
        spa, pos_s = _surface(l)
        ita, pos_i = _surface(r)
        if not spa or not ita:
            continue
        raw[spa].append((ita, pos_s, pos_i))

    out = {}
    for spa, entries in raw.items():
        tags = [_fix_pos(spa, ps) for _, ps, _ in entries if ps]
        if not any(t in CONTENT_POS for t in tags):
            continue
        # Majority across ALL tags, not just the content ones. Restricting the
        # vote to content tags let a minority sense win: `pero` is a
        # conjunction twice and an adverb once, and counting only the adverb
        # chose `eppure` over `ma`.
        counts = collections.Counter(tags)
        def rank(t):
            pri = POS_PRIORITY.index(t) if t in POS_PRIORITY else len(POS_PRIORITY)
            return (-counts[t], pri)
        pos = sorted(counts, key=rank)[0]
        if pos not in CONTENT_POS:
            pos = sorted((t for t in counts if t in CONTENT_POS), key=rank)[0]
        affinity = POS_AFFINITY.get(pos, {})

        # The same Italian word is often listed several times under different
        # tags. Keep its best-matching one: `molto` appears as det, adj and adv
        # for `mucho`, and taking whichever came first buried it under a
        # phrase that happened to be tagged adv.
        best = {}
        for ita, ps, pi in entries:
            a = affinity.get(pi, NEUTRAL_AFFINITY)
            if ita not in best or a > best[ita]:
                best[ita] = a

        # One combined score rather than sorting on agreement first. Sense
        # agreement is worth about one Zipf point; letting it sort first meant a
        # rare exact-tag match beat an ordinary word every time.
        scored = sorted(
            best.items(),
            key=lambda kv: (-(kv[1] * 1.2 + zipf_frequency(kv[0], "it")), len(kv[0])),
        )
        senses = [ita for ita, _ in scored[:MAX_SENSES]]
        out[spa] = {"it": senses[0], "senses": senses, "pos": pos}
    return out


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
    print(f"lemmas: {len(pairs)}")
    multi = [k for k, v in pairs.items() if len(v["senses"]) > 1]
    print(f"with more than one sense: {len(multi)}")
    for w in ("ante", "haber", "deber", "tener", "ser", "poner", "tiempo", "dejar"):
        print(f"  {w:8s} -> {pairs.get(w)}")
