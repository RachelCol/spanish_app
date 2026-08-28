"""Step 1: the Spanish frequency list, base forms only, with parts of speech.

A word earns a place if Wiktionary gives it at least one sense that is not an
inflection of something else. `problemas` is only ever "plural of problema", so
it goes; `habla` is a noun in its own right as well as a form of `hablar`, so
it stays -- as a noun, not as a verb. That last distinction is the point: the
parts of speech recorded here are the ones the word has in its own right.

Apertium supplied these tags before and was wrong often enough to matter --
`hecho` was marked a noun and nothing else for weeks, when it is a noun and an
adjective. Wiktionary knows.

    python pipeline/build_wordlist.py <kaikki-es.jsonl>
"""
import collections
import json
import sys

from wordfreq import top_n_list, zipf_frequency

# Wiktionary's part-of-speech labels, mapped to the ones the app groups by.
POS_MAP = {
    "noun": "n", "verb": "vblex", "adj": "adj", "adv": "adv",
    "prep": "pr", "pron": "prn", "conj": "cnj", "det": "det",
    "intj": "ij", "num": "num", "article": "det", "particle": "adv",
    "phrase": "phrase", "prep_phrase": "phrase", "proverb": "phrase",
    "name": "name",
}

TIERS = [("core", 6.0, 9.0), ("common", 5.0, 6.0), ("useful", 4.5, 5.0),
         ("extended", 4.0, 4.5), ("long_tail", 3.5, 4.0)]


def tier_for(z):
    for name, lo, hi in TIERS:
        if lo <= z < hi:
            return name
    return None


def _is_form_of(sense):
    return bool(sense.get("form_of") or sense.get("alt_of")
                or "form-of" in (sense.get("tags") or []))


def read_wiktionary(path, lang="es"):
    """word -> {part of speech} for the readings the word has in its own right.

    Decided on the FIRST sense listed, not on whether any sense qualifies.
    Wiktionary gives many plurals a marginal extra meaning -- `datos` also
    means "data", `flores` has an obscure sense, `miles` means "thousands" --
    and accepting a word on any non-inflected sense let every one of those
    through as a base form. Sense order carries the answer: `flores` leads with
    "plural of flor", while `hecho` leads with its adjective senses and lists
    the participle last.
    """
    own = collections.defaultdict(set)
    inflected = collections.defaultdict(set)
    for line in open(path, errors="ignore"):
        if '"word"' not in line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("lang_code") != lang:
            continue
        w, pos = r.get("word"), POS_MAP.get(r.get("pos"))
        if not w or not pos:
            continue
        senses = [s for s in (r.get("senses") or []) if s.get("glosses")]
        if not senses:
            continue
        if _is_form_of(senses[0]):
            inflected[w].add(pos)
        else:
            own[w].add(pos)
    return own, inflected


def singular_of(w):
    """The Spanish singular this might be the plural of."""
    if w.endswith("es") and len(w) > 4:
        yield w[:-2]
        yield w[:-2] + "z"      # luces -> luz
    if w.endswith("s") and len(w) > 3:
        yield w[:-1]
        for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")):
            pass
    if w.endswith("ías") and len(w) > 4:
        yield w[:-1]


def build(wikt_path, n=12000):
    own, inflected = read_wiktionary(wikt_path)
    out = []
    skipped = collections.Counter()
    for w in top_n_list("es", n):
        if not w.isalpha() or len(w) < 2:
            skipped["not a word"] += 1
            continue
        pos = own.get(w)
        if not pos:
            skipped["inflected form only" if w in inflected else "not in Wiktionary"] += 1
            continue
        pos = {p for p in pos if p not in ("name",)}
        if not pos:
            skipped["proper noun"] += 1
            continue
        z = zipf_frequency(w, "es")
        tier = tier_for(z)
        if not tier:
            skipped["outside the frequency bands"] += 1
            continue
        out.append({"es": w, "pos": sorted(pos), "zipf": round(z, 2), "tier": tier})

    # Second pass for the plurals Wiktionary happens to gloss in their own
    # right -- `miles` as "thousands", `trámites`, `mercancías`. If stripping
    # the plural ending yields a word already on the list sharing a part of
    # speech, the singular is the base form and this is not.
    have = {w["es"]: set(w["pos"]) for w in out}
    kept = []
    for w in out:
        drop = False
        for s in singular_of(w["es"]):
            if s in have and (have[s] & set(w["pos"])):
                pos = sorted(set(w["pos"]) - have[s])
                if not pos:
                    drop = True
                else:
                    w["pos"] = pos          # `aguas` keeps only the interjection
                break
        if drop:
            skipped["plural of a word already listed"] += 1
        else:
            kept.append(w)
    return kept, skipped


if __name__ == "__main__":
    words, skipped = build(sys.argv[1])
    json.dump(words, open("data/wordlist.json", "w"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"{len(words)} Spanish base forms -> data/wordlist.json\n")
    for k, v in skipped.most_common():
        print(f"  skipped, {k:28s} {v}")
    print()
    for t, _, _ in TIERS:
        n = sum(1 for w in words if w["tier"] == t)
        print(f"  {t:10s} {n}")
    print()
    multi = [w for w in words if len(w["pos"]) > 1]
    print(f"  words with more than one part of speech: {len(multi)}")
    byp = collections.Counter(p for w in words for p in w["pos"])
    print("  by part of speech:", dict(byp.most_common()))
