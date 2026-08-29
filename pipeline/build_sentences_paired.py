"""The sentence bank: examples where both halves contain the word.

Matching on the Spanish word alone and taking whatever Italian translation
Tatoeba has linked has two costs. Going Italian -> Spanish the example may not
contain the word you were prompted with. And nothing catches a homograph:
`como` was illustrated by *Como con las manos* / *Mangio con le mani*, which is
`comer`, a different word entirely.

Requiring the Italian half to contain one of the card's Italian senses fixes
both -- the translation becomes a check on the Spanish match.

Two further things the Spanish side gets wrong on its own:

  spaCy lemmatises `muy` to `mucho` and `tan` to `tanto`, so sentences were
  filed under the wrong headword. `tan` ended up with no examples at all while
  its sentences sat on `tanto`. Lemma matching is right for verbs, where
  inflection genuinely changes the shape, and wrong for everything else, which
  is matched on the surface instead.

  Where a Spanish word carries several Italian senses, both examples used to
  come from whichever sense was commonest. They are now spread across senses
  where Tatoeba allows it, so `tiempo` shows a `tempo` sentence and a `meteo`
  sentence rather than two of the first.

This is the shipping bank. pipeline/build_sentences.py is the older
Spanish-only matcher, kept because classic/ was built with it.
"""
import json, csv, collections, re
import spacy
from wordfreq import zipf_frequency

V = 'vendor/tatoeba/'
PER_CARD = 2
MIN_TOKENS, MAX_TOKENS = 6, 14
SWEET = (6, 8)         # the norm; anything longer is only a fallback


def load_pairs():
    links = collections.defaultdict(list)
    for row in csv.reader(open(V + 'spa-ita_links.tsv'), delimiter='\t'):
        if len(row) == 2:
            links[row[0]].append(row[1])

    def read(path, keep=None):
        out = {}
        for row in csv.reader(open(path), delimiter='\t', quoting=csv.QUOTE_NONE):
            if len(row) == 3 and (keep is None or row[0] in keep):
                out[row[0]] = row[2]
        return out

    spa = read(V + 'spa_sentences.tsv', set(links))
    wanted = {i for ids in links.values() for i in ids}
    ita = read(V + 'ita_sentences.tsv', wanted)
    return links, spa, ita


def score(text, tokens, target):
    """Lower is better. Six to eight words, then as far as fourteen.

    Length leads the key rather than filtering, so a card with nothing in the
    sweet spot widens one word at a time instead of being left bare. Some
    cards end up with no example, which is the honest outcome when Tatoeba has
    nothing short enough -- `luego` has three pairs and all are ten words or
    more.
    """
    n = len(tokens)
    if not (MIN_TOKENS <= n <= MAX_TOKENS):
        return None
    hard = sum(1 for t in tokens if zipf_frequency(t, 'es') < 3.5 and t != target)
    # Six to eight words is the norm and every one of them ranks ahead of
    # anything longer. Past that the tier grows a step per word, so a card with
    # nothing in the sweet spot reaches for nine before ten, and ten before
    # eleven, rather than jumping to whatever is shortest overall. Nothing
    # under six is offered at all -- a five-word example carried too little.
    tier = 0 if n <= SWEET[1] else n - SWEET[1]
    return (tier, hard, n, len(text))


def too_alike(a, b):
    """Two examples that differ by a letter teach nothing twice.

    `Yo no soy baja` and `Yo no soy bajo` were offered together for `bajo` --
    the same sentence in two genders. Exact-match de-duplication could not see
    it, so this compares the words they are built from.
    """
    wa = set(re.findall(r"[\w']+", a.lower()))
    wb = set(re.findall(r"[\w']+", b.lower()))
    if not wa or not wb:
        return a == b
    return len(wa & wb) / len(wa | wb) >= 0.6


def variants(word):
    """The written forms a word may legitimately take in a sentence.

    Truncating to a stem was catching other words entirely. `hasta` became
    `has`, so `has` -- a form of `haber` -- illustrated it; `tanto` became
    `tan`, so `tan` sentences were offered for `el tanto`. Spelling out the
    regular inflections instead costs nothing and cannot reach a different
    word.
    """
    w = word.lower()
    out = {w, w + "s", w + "es"}
    if w.endswith(("o", "a", "e")):
        root = w[:-1]
        out |= {root + x for x in ("o", "a", "os", "as")}
    return out


def build():
    links, spa, ita = load_pairs()
    deck = json.load(open('data/deck.json'))
    words = {c['es'] for c in deck}
    # primary sense first, so it leads when only one example survives
    senses = {c['es']: list(dict.fromkeys([c['it']] + list(c['senses'])))
              for c in deck}
    verbs = {c['es'] for c in deck
             if any(str(t).startswith('vb') for t in (c.get('pos_all') or [c['pos']]))}

    # Multiword cards -- the fixed phrases, and any card whose Spanish is more
    # than one word -- cannot be found in a set of single tokens. They are
    # matched against the sentence as written instead.
    multi = {w for w in words if " " in w}
    by_form = collections.defaultdict(set)
    for w in words - multi:
        for v in variants(w):
            by_form[v].add(w)

    def flat(text):
        """Lowercased words with punctuation gone, so `Sin embargo,` matches."""
        return " " + " ".join(re.findall(r"[\w']+", text.lower())) + " "

    def phrase_hits(text):
        """Multiword cards, found in the sentence text rather than its tokens."""
        low = flat(text)
        return {w for w in multi if f" {w} " in low}

    def surface_hits(tagged):
        """Non-verb cards whose word appears in the sentence as written.

        The token's own part of speech has to agree. `era` is a noun on its
        card and a form of `ser` in most sentences, and offering one for the
        other teaches the wrong word.
        """
        out = set()
        for text, pos in tagged:
            for w in by_form.get(text, ()):
                if w in verbs:
                    continue
                if pos in ("VERB", "AUX") and w not in verbs:
                    continue
                out.add(w)
        return out

    es_nlp = spacy.load('es_core_news_md', disable=['ner', 'parser'])
    it_nlp = spacy.load('it_core_news_md', disable=['ner', 'parser'])

    # Index the Italian side once: which words does each Italian sentence hold?
    ita_ids = list(ita)
    ita_words = {}
    ita_text = {}
    for sid, doc in zip(ita_ids, it_nlp.pipe([ita[i] for i in ita_ids], batch_size=256)):
        ita_words[sid] = ({t.lemma_.lower() for t in doc if t.is_alpha}
                          | {t.text.lower() for t in doc if t.is_alpha})
        ita_text[sid] = flat(ita[sid])

    ids = list(spa)
    candidates = collections.defaultdict(list)
    for sid, doc in zip(ids, es_nlp.pipe([spa[i] for i in ids], batch_size=256)):
        lemmas = [t.lemma_.lower() for t in doc if t.is_alpha]
        surfaces = [(t.text.lower(), t.pos_) for t in doc if t.is_alpha]
        found_phrases = phrase_hits(spa[sid])
        hits = {t for t in lemmas if t in verbs} | surface_hits(surfaces)
        # A word inside a phrase belongs to the phrase. `Empezo a pesar de la
        # lluvia` illustrates `a pesar de`, and offering it as the example for
        # `pesar` would show "despite" on a card that means "to weigh".
        for p in found_phrases:
            hits -= set(p.split())
        hits |= found_phrases
        if not hits:
            continue
        pair_ids = [i for i in links[sid] if i in ita]
        if not pair_ids:
            continue
        for target in hits:
            held = ita_words.get(pair_ids[0], set())
            for iid in pair_ids:
                held = ita_words.get(iid, set())
                def matches(sense):
                    if " " not in sense:
                        return sense.lower() in held
                    parts = [p for p in sense.lower().split() if len(p) > 2]
                    return all(p in held for p in parts)

                found = next((s for s in senses[target] if matches(s)), None)
                if found:
                    sc = score(spa[sid], lemmas, target)
                    if sc is not None:
                        candidates[target].append((sc, sid, iid, found))
                    break

    out, used = {}, 0
    for card in deck:
        rows, seen_senses = [], set()
        ranked = sorted(candidates.get(card['es'], []))
        # one per Italian sense first, then fill from whatever is left
        for pass_no in (0, 1):
            for sc, sid, iid, sense in ranked:
                if len(rows) >= PER_CARD:
                    break
                if pass_no == 0 and sense in seen_senses:
                    continue
                if any(too_alike(r['es'], spa[sid]) for r in rows):
                    continue
                seen_senses.add(sense)
                rows.append({'es': spa[sid], 'it': ita[iid]})
        if rows:
            out[card['es']] = rows
            used += len(rows)
    return out, used


if __name__ == '__main__':
    out, used = build()
    with open('data/sentences.json', 'w') as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(',', ':'))
    deck = json.load(open('data/deck.json'))
    print(f'cards with examples: {len(out)} of {len(deck)}   ({used} sentences)')
