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
               "cnjcoo", "cnjsub", "cnjadv", "preadv", "prn"}

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
    "prn": {"prn": 3, "n": 1, "adj": 1},
}

# An Italian tag with no entry in the affinity table scores neutrally, so
# frequency still decides rather than the sense being pushed to the bottom.
NEUTRAL_AFFINITY = 1

# When a word carries several tags equally often, prefer the ordinary ones.
# `bien` is tagged preadv, n and adv once each, and letting preadv win chose
# the apocopated `ben` over `bene`.
POS_PRIORITY = ["vblex", "n", "adj", "adv", "pr", "prn", "cnjcoo", "cnjsub",
                "cnjadv", "vbser", "vbhaver", "vbmod", "preadv"]

# Four, not three. A cap exists to stop Apertium's long tails filling the card,
# but three was arbitrary enough to start costing real senses: `objetivo` is a
# goal, an objective and a target, and something true had to be dropped to fit.
MAX_SENSES = 4

# Apertium is machine-translation data and is occasionally incomplete or
# domain-skewed in ways no scoring rule can repair, because the right answer is
# simply not in the file. This is the escape hatch: an explicit, auditable list
# of hand-written sense sets, ordered primary first.
#
# `tener` has no `tenere` entry at all -- Apertium offers avere three times and
# dovere once, the latter from `tener que`. For translation that is fine. For a
# learner it hides the most useful fact about the word: tener and tenere are
# cognates that split, so the Italian instinct to read tener as "hold" is
# exactly the error the card should be preventing.
SENSE_OVERRIDES = {
    'tener':   ['avere', 'tenere', 'dovere'],
    'guardar': ['conservare', 'tenere', 'salvare'],   # salvare is the file sense
    # Apertium offers only planning, maestranze and soletta. The real senses
    # are a staff complement, a template, and the insole of a shoe -- soletta
    # being right for the last of those. `organico` beats `personale`, which
    # in Italian also means "personal".
    'plantilla': ['organico', 'modello', 'soletta'],
}

# Two different problems, two different rules.
#
# Archaic and junk glosses are rare in absolute terms, not merely rarer than
# the primary: meco, teco, taluno, allocuzione, a misspelled lievietare and an
# English "corporate tax" all sit at or below Zipf 2.8, while every gloss worth
# keeping -- meteo, granché, parecchio, indossare -- is at 3.7 or above. A
# floor separates them cleanly, and a gap does not: `tiempo -> meteo` is a
# genuine second meaning that a gap rule throws away, and it is exactly the
# case multiple senses exist for, since Spanish has no separate word for it.
#
# Register duplicates are a different thing. `antes -> in precedenza` is common
# enough to clear the floor but says only that Italian has a formal way to say
# "before". Those are phrases, and close enough in meaning to the primary that
# a frequency gap does identify them.
# A phrase needs less of a gap to be dismissed than a single word does, since
# a rarer single word is often a genuine synonym while a rarer phrase is
# usually just formal register.
MIN_SENSE_ZIPF = 3.0     # below this a gloss is archaic, misspelled or foreign
NOISE_GAP_PHRASE = 0.8   # phrases only: register rather than meaning

# English loanwords are NOT filtered out. An earlier version dropped any gloss
# that read more English than Italian, which removed `cuenta -> account`,
# `tendencia -> trend`, `personal -> staff` and twenty-five others. That was
# the wrong test, and it answered the wrong question: what matters on the
# Italian side of the card is what Italians say, and Italians say all of these.
# The Zipf floor below already asks exactly that question, in Italian.
#
# The asymmetry is real but belongs elsewhere -- across thirty-one loanwords,
# every one is commoner in Italian than in Spanish, by around 0.9 Zipf. Spanish
# calques where Italian borrows. That is a fact about Spanish, and a card whose
# Italian column is honest is what makes it visible.


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
        tags = [ps for _, ps, _ in entries if ps]
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
        ranked = [ita for ita, _ in scored]
        senses = [ranked[0]]
        top_z = zipf_frequency(ranked[0], "it")
        for ita in ranked[1:]:
            if len(senses) >= MAX_SENSES:
                break
            z = zipf_frequency(ita, "it")
            if z < MIN_SENSE_ZIPF:
                continue
            if " " in ita and top_z - z >= NOISE_GAP_PHRASE:
                continue
            senses.append(ita)
        # A word can be several things at once -- `bajo` is an adjective and a
        # preposition, `ver` a verb and a noun. One tag drives conjugation and
        # sense ranking, but the filter and the label need all of them, or
        # filtering to Prepositions silently loses `bajo`.
        all_pos = sorted({t for t in tags if t in CONTENT_POS},
                         key=lambda t: POS_PRIORITY.index(t) if t in POS_PRIORITY else 99)
        if spa in SENSE_OVERRIDES:
            senses = SENSE_OVERRIDES[spa][:MAX_SENSES]

        out[spa] = {"it": senses[0], "senses": senses, "pos": pos, "pos_all": all_pos}
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
