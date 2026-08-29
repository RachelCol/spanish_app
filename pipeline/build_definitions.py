"""Step 2: an Italian definition for each Spanish word, by part of speech.

The dictionary proposes and the corpus decides. Candidate Italian words come
from Apertium and Wiktionary, which know what *can* translate a word; the
aligned corpus says which of them actually do, how often, and in what order.
Neither alone is enough -- the corpus by itself misses `no -> non`, and the
dictionaries by themselves gave us `dovere -> tener`.

Two numbers per sense, and they answer different questions. The alignment
probability decides -- it is how often, when this Spanish word is translated,
it comes out as this Italian one, and it is what ranks and trims. The corpus
percentage is displayed -- it is how often the Italian word appears at all in
sentences containing the Spanish one, so a low figure means the sentence is
usually restructured, which is worth seeing.

Three things come out besides the definitions, all for review rather than for
the deck:

  additions   an Italian word the corpus attests above the threshold that no
              dictionary lists. Say `yes` and it joins that definition.
  dropped     a part of speech with no attested translation, and the word it
              was dropped from.
  thin        a word the corpus has too little evidence about to judge.
"""
import collections
import csv
import json
import sys
import unicodedata

import editorial
import xml.etree.ElementTree as ET

sys.path.insert(0, "pipeline")
from pairs import _surface, DIX          # noqa: E402

# Closed classes. A preposition, conjunction, determiner or pronoun is glue
# rather than meaning, and alignment has nothing to grip: the corpus gets the
# top answer right -- `si` is `se` at 0.72, `porque` is `perché` at 0.66 -- and
# fills the rest with noise. For these readings the dictionary is taken as it
# stands, in its own order, and no percentage is shown, because a percentage
# for `de` -> `di` would say nothing anyone needs.
CLOSED = {"pr", "cnj", "det", "prn"}

# Owned by their own sections rather than by the flashcard deck. Definitions
# are still built for them -- the sections need the data -- but they do not
# become cards, and they are kept off the review lists so no time is spent on
# words that are leaving. What a preposition needs taught is which words it
# attaches to, which a translation card cannot carry.
# Cards are for words you produce: nouns, verbs, adjectives, adverbs, plus
# numbers and the fixed phrases. Everything else is glue you choose inside a
# sentence, and it is learned by choosing it -- so prepositions, determiners,
# pronouns and conjunctions go to their sections, and interjections are
# dropped outright, being five words and not worth a room of their own.
SECTIONED = {"det", "ij", "prn", "cnj"}

RESCUE_PROB = 0.25     # what the corpus must reach to save a word from vanishing
RELATIVE = 15.0        # keep anything within this % of the top translation
MIN_PAIRS = 30         # below this the corpus has no opinion worth having
MIN_PROB = 0.01        # an alignment weaker than this is noise
ADD_PROB = 0.15        # what an unlisted word must reach to be worth reviewing
BEATS = 1.5            # how far the corpus must beat the dictionary to overrule it

# Apertium's Spanish-side tags, grouped the way the app groups them.
GROUP = {"vblex": "vblex", "vbmod": "vblex", "vbhaver": "vblex", "vbser": "vblex",
         "adv": "adv", "preadv": "adv", "cnjcoo": "cnj", "cnjsub": "cnj",
         "cnjadv": "cnj", "n": "n", "adj": "adj", "pr": "pr", "prn": "prn",
         "det": "det", "ij": "ij", "num": "num"}


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


strip_accents = norm


def dictionary(wikt_it2es_path):
    """spanish -> {italian -> {spanish parts of speech it was listed under}}"""
    out = collections.defaultdict(lambda: collections.defaultdict(set))
    root = ET.parse(DIX).getroot()
    for e in root.find("section").findall("e"):
        p = e.find("p")
        if p is None:
            continue
        l, r = p.find("l"), p.find("r")
        if l is None or r is None:
            continue
        es, pos_es = _surface(l)
        it, _ = _surface(r)
        if not es or not it:
            continue
        out[norm(es)][norm(it)].add(GROUP.get(pos_es or "", ""))
    # Wiktionary knows nothing about which Spanish part of speech, so its
    # candidates are offered to every part of speech the word has.
    for it, esl in json.load(open(wikt_it2es_path)).items():
        for es in esl:
            out[norm(es)][norm(it)].add("")
    return out


def read_lexicon(path="content/lexicon.csv"):
    """The frozen list. Membership does not change here; definitions do."""
    out = []
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            out.append({"es": r["spanish"], "pos": r["pos"].split(),
                        "tier": r["band"], "zipf": float(r["zipf"]),
                        "rank": int(r["rank"])})
    return out


def build(wikt_it2es_path):
    words = read_lexicon()
    matrix = json.load(open("data/matrix.json"))
    aligned = json.load(open("data/aligned.json"))
    # Alignment over tagged tokens, where available: `mejor|adj` and
    # `mejor|adv` are separate entries, so `migliore` leads the adjective and
    # `meglio` the adverb rather than both appearing under both.
    try:
        by_reading = json.load(open("data/aligned_pos.json"))
    except FileNotFoundError:
        by_reading = {}
    it_pos = json.load(open("data/italian_pos.json"))
    # The Italian side was never lemmatised, so `lascia`, `vanno`, `succede`
    # and 113 others became prompts. italian_pos.json is built from readings a
    # word has in its own right, so membership in it is the test.
    # Apertium writes Italian without accents -- `perche`, `abilita`,
    # `affinita` -- where Wiktionary accents them. 395 candidates were being
    # rejected for that alone, most of them the whole `-ità` class. Match the
    # exact spelling first, then the accent-free one where nothing else claims
    # it, exactly as the Spanish side does.
    it_base = set(it_pos)
    _bare = collections.defaultdict(set)
    for _w in it_base:
        _bare[strip_accents(_w)].add(_w)
    # Where several spellings collapse to the same bare form -- `perché` and
    # the common misspelling `perchè` -- take the commonest in Italian rather
    # than giving up, which is what left `porque` with no definition at all.
    from wordfreq import zipf_frequency as _z
    it_alias = {b: max(v, key=lambda w: _z(w, "it")) for b, v in _bare.items()}

    def italian(it, from_dictionary=True):
        """The Italian word as it should be written, or None if unknown.

        Where the spelling came from decides how to read it. Apertium drops
        accents as a matter of course, so its `citta` means `città` and should
        be resolved through the accent-free form. The corpus reads real text
        through a lemmatiser, so its `papà` really is `papà` and must be left
        alone -- resolving that one too turned the word for "dad" into the
        Pope, and `metà` into a destination.

        Accent pairs are mostly not variants of one another: Wiktionary has
        `citta` as the feminine of `citto`, and only `perchè` is actually
        marked a misspelling of `perché`."""
        if it in it_base and not from_dictionary:
            return it
        best = it_alias.get(strip_accents(it))
        if best:
            return best
        return it if it in it_base else None
    try:
        shares = json.load(open("data/shares.json"))["share"]
    except FileNotFoundError:
        shares = {}
    dic = dictionary(wikt_it2es_path)

    defs, additions, dropped, thin, unsupported, overruled = {}, [], [], [], [], []
    rescued = []

    # Fixed phrases replace the bare word they contain: `sin embargo` is a card
    # and `embargo` is not, because 98% of that word's uses are the phrase and
    # aligning the bare form credits it with the phrase's meaning.
    try:
        phrases = json.load(open("data/phrases.json"))
    except FileNotFoundError:
        phrases = {}
    # `replaces: null` means the phrase joins the bare word rather than
    # standing in for it.
    replaced = {v["replaces"] for v in phrases.values() if v["replaces"]}
    EXCLUDED = editorial.excluded()
    REVERTS, OVERRIDES = editorial.reverts(), editorial.overrides()

    for phrase, v in phrases.items():
        defs[phrase] = {"pairs": v["pairs"],
                        "by_pos": {"phrase": [{"it": i["it"], "prob": None,
                                               "pct": i["pct"]} for i in v["it"]]}}

    for w in words:
        es, poss = w["es"], w["pos"]
        if es in replaced or es in EXCLUDED:
            continue
        nes = norm(es)
        entry = matrix.get(es)
        # A word set by hand is not waiting on corpus evidence -- that is the
        # reason it was set. `soler` has zero pairs because it is written
        # `suele`, and skipping it here threw the override away.
        forced_here = any(w == es for w, _ in OVERRIDES)
        if forced_here and (not entry or entry["pairs"] < MIN_PAIRS):
            entry = entry or {"pairs": 0, "it": []}
        elif not entry or entry["pairs"] < MIN_PAIRS:
            thin.append({"spanish": es, "pos": ",".join(poss),
                         "pairs": entry["pairs"] if entry else 0})
            continue

        # Exact counts where we have them; matrix.json truncates at thirty
        # neighbours and those are mostly function words.
        pct = dict(shares.get(es) or shares.get(nes) or {}) \
            or {it: p for it, p in entry["it"]}

        def share_of(it, from_dict=True):
            """The count is stored under the canonical spelling, so look it up
            there -- `citta` was asking for a figure filed under `città`.

            None where the pair was never counted, which is not the same as
            counted and found to be zero. Returning 0.0 for both is how 261
            senses came to claim a measured zero they had never been measured
            for, and how `avere bisogno di` -- a phrase, so never in the share
            table at all -- came to read 0%."""
            can = italian(it, from_dict)
            for k in (can, it):
                if k is not None and k in pct:
                    return round(pct[k], 1)
            return None
        prob = {it: p for it, p in aligned.get(es, [])}

        def tagged_prob(pos):
            """Alignment for this reading of the word, if it was tagged.

            Italian candidates of the same part of speech first: a Spanish noun
            is answered by an Italian noun, and `tener en cuenta` does not make
            `tenere` the meaning of `cuenta`."""
            rows = by_reading.get(f"{es}|{pos}") or []
            same, other = {}, {}
            for key, p in rows:
                it_word, _, it_p = key.partition("|")
                (same if it_p == pos else other)[it_word] = max(
                    (same if it_p == pos else other).get(it_word, 0.0), p)
            return same or other
        proposed = dic.get(nes, {})

        # Apertium keys its candidates unaccented, the corpus returns them
        # accented, so testing membership directly said `verità` was not what
        # the dictionary meant by `verita`. Compare through the canonical form.
        canon_proposed = {}
        for _it in proposed:
            _c = italian(_it)
            if _c:
                canon_proposed[_c] = _it

        def in_dictionary(it):
            return it in proposed or italian(it, False) in canon_proposed \
                or italian(it) in canon_proposed


        # what the dictionary offers, ranked by how often it is the alignment
        scored = sorted(((prob.get(it, 0.0), it) for it in proposed
                         if italian(it)), reverse=True)
        attested = [(p, it) for p, it in scored if p >= MIN_PROB]

        corpus_only = False
        if attested:
            top = attested[0][0]
            keep = [(it, p) for p, it in attested if 100 * p / top >= RELATIVE]
        else:
            # No dictionary candidate survives. Falling back to the alignment
            # rather than dropping the word: `anterior` is `precedente` and
            # `acta` is `verbale`, and in both the corpus is right and the
            # dictionary is not. Losing `año` for want of an agreement is the
            # worse error. Flagged so these can be looked at.
            # Through the tagged alignment where it exists, so the fallback
            # obeys part of speech too. Untagged, `intento` fell back on
            # `tentativo, di` -- a noun answered by a preposition, because
            # nothing here was checking.
            rows = []
            for pos in poss:
                tp = tagged_prob(pos)
                for it, p in sorted(tp.items(), key=lambda kv: -kv[1]):
                    if p >= 0.10 and italian(it):
                        rows.append((it, p))
            if not rows:
                rows = [(it, p) for it, p in aligned.get(es, [])
                        if p >= 0.10 and italian(it)
                        and not (it_pos.get(italian(it))
                                 and set(it_pos[italian(it)]) <= CLOSED
                                 and not ((set(poss) - SECTIONED) & CLOSED))]
            # The exemption is for a word that really is glue, and glue no
            # longer gets a card -- so it has to be measured against the
            # readings that survive. `para` is a preposition and a noun; the
            # preposition is sectioned, and leaving the exemption on let `per`
            # sit in the noun slot. Same for `yo` and `io`.
            if not rows and not forced_here:
                continue
            if not rows:
                # `soler` is written `suele` and `suelen`, so it has no corpus
                # rows at all. That is exactly why it was set by hand, and the
                # override is applied further down.
                keep, corpus_only = [], True
            else:
                rows.sort(key=lambda r: -r[1])
                topp = rows[0][1]
                keep = [(it, p) for it, p in rows if 100 * p / topp >= RELATIVE]
                corpus_only = True

        # Organise by the Spanish word's parts of speech. Apertium says which
        # Spanish part of speech it listed a pair under; where it does not --
        # Wiktionary's candidates carry none -- the Italian word's own part of
        # speech decides, which is what separates `meglio` the adverb from
        # `migliore` the adjective on a word that is both.
        by_pos = {}
        for pos in poss:
            tp = tagged_prob(pos)
            if tp and pos not in CLOSED:
                ranked = sorted(((p, it) for it, p in tp.items()
                                 if in_dictionary(it) and italian(it)), reverse=True)
                # A word the dictionary never lists that beats everything it
                # does list is not an extra sense -- it says the dictionary has
                # the primary wrong. `carta` is `lettera` before it is `carta`,
                # `papel` is `ruolo`, and `más` is `più` rather than `oltre`.
                # Must be a real Italian word: `parlamente` is a tagger slip.
                outside = sorted(((p, it) for it, p in tp.items()
                                  if not in_dictionary(it) and italian(it)
                                  and italian(it) in it_pos), reverse=True)
                if outside and (not ranked or outside[0][0] > ranked[0][0] * BEATS) \
                        and outside[0][0] >= ADD_PROB:
                    if pos not in SECTIONED:
                        overruled.append({
                            "band": w["tier"], "spanish": es, "pos": pos,
                            "corpus": italian(outside[0][1], False),
                            "prob": round(outside[0][0], 3),
                            "dictionary": italian(ranked[0][1]) if ranked else "",
                            "revert": "",
                            "note": ("dictionary offered nothing"
                                     if not ranked else
                                     "corpus beats dictionary %.1fx"
                                     % (outside[0][0] / max(ranked[0][0], 1e-9)))})
                    ranked = [outside[0]] + [r for r in ranked
                                             if r[0] >= outside[0][0] * RELATIVE / 100]
                if ranked:
                    # Glue cannot be the meaning of a noun. The other branch
                    # checked this and this one did not, which is how `para`
                    # kept `per` and `yo` kept `io` once their preposition and
                    # pronoun readings were sectioned away.
                    ranked = [(p, it) for p, it in ranked
                              if not (it_pos.get(italian(it))
                                      and set(it_pos[italian(it)]) <= CLOSED)]
                if ranked:
                    top_p = ranked[0][0]
                    here = [(it, p) for p, it in ranked
                            if 100 * p / top_p >= RELATIVE]
                    by_pos[pos] = [{"it": italian(it, it in proposed),
                                    "prob": round(p, 3), "pct": share_of(it)}
                                   for it, p in here]
                    continue
            if pos in CLOSED:
                # dictionary order, no corpus ranking, no percentage
                offered = [it for it in proposed
                           if pos in (proposed[it] - {""}) or not (proposed[it] - {""})]
                offered = [it for it in offered if italian(it)]
                offered = [it for it in offered
                           if not it_pos.get(italian(it))
                           or pos in it_pos[italian(it)]
                           or set(it_pos[italian(it)]) & CLOSED]
                if offered:
                    by_pos[pos] = [{"it": italian(it), "prob": None, "pct": None}
                                   for it in offered[:4]]
                continue
            here = []
            for it, p in keep:
                # a corpus fallback is not in `proposed` at all
                tagged = proposed.get(it, set()) - {""}
                if tagged:
                    if pos in tagged:
                        here.append((it, p))
                elif pos in it_pos.get(it, []):
                    here.append((it, p))
                elif it_pos.get(it) and set(it_pos[it]) <= CLOSED:
                    continue      # glue cannot be the meaning of a noun
                elif not it_pos.get(it) and pos in ("n", "adj", "vblex", "adv"):
                    # unknown to Wiktionary; allow only for open classes, so a
                    # stray preposition cannot become a noun's definition
                    here.append((it, p))
            # No fallback that re-admits everything. It was letting `di`, a
            # preposition, stand as the definition of `intento`, a noun --
            # the part of speech is the whole point of grouping.
            if here:
                by_pos[pos] = [{"it": italian(it), "prob": round(p, 3),
                                "pct": share_of(it)} for it, p in here]
        for pos in poss:
            if pos not in by_pos:
                dropped.append({"spanish": es, "dropped_pos": pos,
                                "kept": ",".join(sorted(by_pos)) or "nothing"})
        # A word in the lexicon is a word we set out to learn, so it should not
        # disappear without anyone seeing it. Two ways that happened: `si` is a
        # conjunction, and function words take the dictionary only, so when the
        # dictionary held nothing the word went -- though the corpus reads
        # `se` at 69.6% and aligns it at 0.78. And `mayor` is tagged a noun and
        # nothing else, so the corpus was asked about `mayor|n` and answered
        # noise, while untagged it aligns to `maggiore` at 0.33.
        #
        # The rescue is deliberately strict: only where nothing else survived,
        # only from the untagged alignment, and only when it is confident.
        # Glue is not rescued: a word that is only a preposition or a pronoun
        # is meant to leave the deck, and rescuing it put `de`, `que` and
        # `hola` straight back.
        if not by_pos and not set(poss) <= SECTIONED:
            rescue = [(p, it) for it, p in aligned.get(es, [])
                      if p >= RESCUE_PROB and italian(it, False)
                      and not (it_pos.get(italian(it, False))
                               and set(it_pos[italian(it, False)]) <= CLOSED)]
            if rescue:
                p_best, it_best = max(rescue)
                canon = italian(it_best, False)
                by_pos[poss[0]] = [{"it": canon, "prob": round(p_best, 3),
                                    "pct": share_of(canon, False)}]
                rescued.append({"spanish": es, "pos": poss[0], "italian": canon,
                                "prob": round(p_best, 3),
                                "note": "would have had no card at all; taken "
                                        "from the untagged alignment"})
        if not by_pos and forced_here:
            by_pos = {poss[0]: []}      # finish() fills it from the override
        if not by_pos:
            thin.append({"spanish": es, "pos": ",".join(poss),
                         "pairs": entry["pairs"]})
            continue
        by_pos = finish(es, by_pos, share_of, REVERTS, OVERRIDES)
        # A hand decision can empty a word too -- dropping `cuando -> tanto`
        # left `cuando` with nothing, though it aligns to `quando` at 0.61.
        # The rescue above runs before those decisions, so try it again here.
        if not by_pos and not set(poss) <= SECTIONED:
            again = [(p, it) for it, p in aligned.get(es, [])
                     if p >= RESCUE_PROB and italian(it, False)
                      and not (it_pos.get(italian(it, False))
                               and set(it_pos[italian(it, False)]) <= CLOSED)]
            if again:
                p_best, it_best = max(again)
                canon = italian(it_best, False)
                by_pos = {poss[0]: [{"it": canon, "prob": round(p_best, 3),
                                     "pct": share_of(canon, False)}]}
                rescued.append({"spanish": es, "pos": poss[0], "italian": canon,
                                "prob": round(p_best, 3),
                                "note": "a hand decision left no card; taken "
                                        "from the untagged alignment"})
        if not by_pos:
            continue
        defs[es] = {"pairs": entry["pairs"], "by_pos": by_pos}
        if corpus_only and not (set(poss) <= SECTIONED):
            unsupported.append({"spanish": es, "band": w["tier"],
                                "definition": ", ".join(it for it, _ in keep),
                                "keep": "",
                                "note": "no dictionary candidate was attested"})

        # what the alignment found that no dictionary lists
        cutoff = keep[0][1] * RELATIVE / 100 if keep else 0
        best_dict = keep[0][1] if keep else 0.0
        for it, p in aligned.get(es, []):
            if in_dictionary(it) or not cutoff or p < cutoff or p < ADD_PROB:
                continue
            if not italian(it):
                continue
            # A word the dictionary never lists that outranks everything it
            # does list is not an extra sense -- it says the dictionary has the
            # primary meaning wrong. `carta` is `lettera` before it is `carta`.
            if set(poss) <= SECTIONED:
                continue
            additions.append({"beats_dictionary": "yes" if p > best_dict else "",
                              "spanish": es, "italian": it,
                              "prob": round(p, 3),
                              "pct": share_of(it),
                              "of_top": round(100 * p / keep[0][1]),
                              "band": w["tier"], "add": "",
                              "note": ""})

    return defs, additions, dropped, thin, unsupported, overruled, rescued


def finish(es, by_pos, share_of, reverts, overrides):
    """The hand decisions, the de-duplication, and the ordering.

    Ordering is by measured share, not by alignment probability. Probability
    still decides what survives -- it is the better judge of whether an Italian
    word is the translation at all, and trimming on share would have cut
    `haber -> avere`, which co-occurs at 2.4% only because Italian takes
    `essere` as its auxiliary. But share is what the card prints, and a card
    reading `nonno 1.9%` above `nonna 85.9%` is wrong whatever the internal
    justification.
    """
    # An override states the whole word, not one of its readings. Spanish
    # nominalises its infinitives freely, so Wiktionary gives every verb a noun
    # reading and the corpus fills it -- which is where `hacer -> lavoro` and
    # `haber -> essere` came from. Setting the verb by hand should retire them.
    for (w, pos), forced in overrides.items():
        if w == es:
            return {pos: [{"it": it, "prob": None, "pct": share_of(it, False)}
                          for it in forced]}

    out = {}
    for pos, items in by_pos.items():
        # Glue does not get a card. It is chosen inside a sentence, so it is
        # learned by choosing it, in its own section.
        if pos in SECTIONED:
            continue
        if True:
            swap = reverts.get((es, pos))
            if swap:
                drop, keep = swap
                items = [i for i in items if i["it"] != drop]
                # An empty `keep` means the reading was simply wrong and there
                # is nothing to put in its place -- `nadie` is not `vero`.
                if keep and keep not in {i["it"] for i in items}:
                    items.insert(0, {"it": keep, "prob": None,
                                     "pct": share_of(keep, False)})

            seen, unique = set(), []
            for i in items:
                if i["it"] not in seen:
                    seen.add(i["it"])
                    unique.append(i)
            items = unique

            # A sense the corpus measured at zero is not a sense, so long as
            # the word has one it did attest.
            best = max((i["pct"] or 0) for i in items) if items else 0
            if best > 0:
                items = [i for i in items if i["pct"] is None or i["pct"] > 0]

        items.sort(key=lambda i: -(i["pct"] if i["pct"] is not None else -1))
        if items:
            out[pos] = items

    # The same Italian word under two readings of one Spanish word says nothing
    # twice: `ser` gave `essere` as both noun and verb. Keep it where it scores
    # best, and where the scores tie, where it appeared first.
    # On a tie the verb reading wins: `decir` and `saber` both scored the same
    # as noun and as verb, and they are verbs.
    PREF = {"vblex": 0, "adj": 1, "adv": 2, "n": 3}
    best = {}
    for pos, items in out.items():
        for n, i in enumerate(items):
            k = i["it"]
            rank = (-(i["pct"] if i["pct"] is not None else -1),
                    PREF.get(pos, 4), n)
            if k not in best or rank < best[k][0]:
                best[k] = (rank, pos)
    out = {pos: [i for i in items if best[i["it"]][1] == pos]
           for pos, items in out.items()}
    return {pos: items for pos, items in out.items() if items}


def write_csv(path, rows, fields):
    with open(path, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields)
        wr.writeheader()
        wr.writerows(rows)


if __name__ == "__main__":
    wikt = sys.argv[1]
    defs, additions, dropped, thin, unsupported, overruled, rescued = build(wikt)
    json.dump(defs, open("data/definitions.json", "w"),
              ensure_ascii=False, separators=(",", ":"))
    additions.sort(key=lambda r: (r["beats_dictionary"] != "yes", -r["prob"]))
    # The review rows are collected while each word is resolved, which is
    # before the hand decisions in finish() have been applied. A row about a
    # reading that no longer reaches a card is not a question anyone can
    # answer -- 256 of the additions were already on the card, and 28 of the
    # overruled rows concerned readings an override had retired.
    def on_card(es, it, pos=None):
        entry = defs.get(es)
        if not entry:
            return False
        items = entry["by_pos"].get(pos, []) if pos else \
            [i for l in entry["by_pos"].values() for i in l]
        return any(i["it"] == it for i in items)

    additions = [r for r in additions if not on_card(r["spanish"], r["italian"])]
    overruled = [r for r in overruled
                 if on_card(r["spanish"], r["corpus"], r["pos"])]
    unsupported = [r for r in unsupported
                   if any(on_card(r["spanish"], it.strip())
                          for it in r["definition"].split(","))]

    write_csv("review_additions.csv", additions,
              ["beats_dictionary", "band", "spanish", "italian",
               "prob", "pct", "of_top", "add", "note"])
    write_csv("review_dropped_pos.csv", dropped, ["spanish", "dropped_pos", "kept"])
    write_csv("review_thin.csv", thin, ["spanish", "pos", "pairs"])
    write_csv("review_rescued.csv", rescued,
              ["spanish", "pos", "italian", "prob", "note"])
    write_csv("review_corpus_only.csv", unsupported,
              ["band", "spanish", "definition", "keep", "note"])
    write_csv("review_overruled.csv", overruled,
              ["band", "spanish", "pos", "corpus", "prob", "dictionary",
               "revert", "note"])

    print(f"{len(defs)} Spanish words defined -> data/definitions.json")
    n_senses = sum(len(v) for d in defs.values() for v in d["by_pos"].values())
    print(f"  {n_senses} Italian senses across them")
    print(f"\n  review_additions.csv    {len(additions):5d}  corpus found, no dictionary lists")
    print(f"  review_dropped_pos.csv  {len(dropped):5d}  parts of speech with no translation")
    print(f"  review_thin.csv         {len(thin):5d}  too little corpus evidence")
    print(f"  review_corpus_only.csv  {len(unsupported):5d}  defined by the corpus, no dictionary agreed")
    print(f"  review_overruled.csv    {len(overruled):5d}  corpus overruled the dictionary")
