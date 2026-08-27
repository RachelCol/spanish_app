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
import json, csv, collections
import spacy
from wordfreq import zipf_frequency

V = 'vendor/tatoeba/'
PER_CARD = 2
MIN_TOKENS, MAX_TOKENS = 4, 14
MAX_INFLECTION = 3       # `casa` may reach `casitas`, not `casualidad`


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
    """Lower is better. Rewards short sentences built from common words."""
    n = len(tokens)
    if not (MIN_TOKENS <= n <= MAX_TOKENS):
        return None
    hard = sum(1 for t in tokens if zipf_frequency(t, 'es') < 3.5 and t != target)
    return (hard, n, len(text))


def stem(word):
    """Enough of a word to catch its inflections and no more. `mucho` keeps
    `much`, which `muy` does not start with; `tan` keeps `tan`."""
    return word[:max(3, len(word) - 2)].lower()


def build():
    links, spa, ita = load_pairs()
    deck = json.load(open('data/deck.json'))
    words = {c['es'] for c in deck}
    # primary sense first, so it leads when only one example survives
    senses = {c['es']: list(dict.fromkeys([c['it']] + list(c['senses'])))
              for c in deck}
    verbs = {c['es'] for c in deck
             if any(str(t).startswith('vb') for t in (c.get('pos_all') or [c['pos']]))}

    by_stem = collections.defaultdict(set)
    for w in words:
        by_stem[stem(w)].add(w)

    def surface_hits(tokens):
        """Non-verb cards whose word appears in the sentence as written."""
        out = set()
        for t in tokens:
            for n in range(3, len(t) + 1):
                for w in by_stem.get(t[:n], ()):
                    if w in verbs:
                        continue
                    if t.startswith(stem(w)) and len(t) - len(stem(w)) <= MAX_INFLECTION:
                        out.add(w)
        return out

    es_nlp = spacy.load('es_core_news_md', disable=['ner', 'parser'])
    it_nlp = spacy.load('it_core_news_md', disable=['ner', 'parser'])

    # Index the Italian side once: which words does each Italian sentence hold?
    ita_ids = list(ita)
    ita_words = {}
    for sid, doc in zip(ita_ids, it_nlp.pipe([ita[i] for i in ita_ids], batch_size=256)):
        ita_words[sid] = ({t.lemma_.lower() for t in doc if t.is_alpha}
                          | {t.text.lower() for t in doc if t.is_alpha})

    ids = list(spa)
    candidates = collections.defaultdict(list)
    for sid, doc in zip(ids, es_nlp.pipe([spa[i] for i in ids], batch_size=256)):
        lemmas = [t.lemma_.lower() for t in doc if t.is_alpha]
        surfaces = [t.text.lower() for t in doc if t.is_alpha]
        hits = {t for t in lemmas if t in verbs} | surface_hits(surfaces)
        if not hits:
            continue
        pair_ids = [i for i in links[sid] if i in ita]
        if not pair_ids:
            continue
        for target in hits:
            held = ita_words.get(pair_ids[0], set())
            for iid in pair_ids:
                held = ita_words.get(iid, set())
                found = next((s for s in senses[target] if s.lower() in held), None)
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
                if any(r['es'] == spa[sid] for r in rows):
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
