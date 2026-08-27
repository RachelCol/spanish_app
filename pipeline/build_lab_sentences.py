"""The sentence bank, rebuilt so both halves contain the word.

The shipping bank matches on the Spanish word alone and takes whatever Italian
translation Tatoeba has linked. That has two costs. Going Italian -> Spanish
the example may not contain the word you were prompted with -- true of 24% of
them. And worse, nothing catches a homograph: `como` is illustrated by *Como
con las manos* / *Mangio con le mani*, which is `comer`, a different word.

Requiring the Italian half to contain one of the card's Italian senses fixes
both. The Italian translation becomes a check on the Spanish match.

Writes lab/data/sentences.json. data/sentences.json is left alone.
"""
import json, csv, collections
import spacy

V = 'vendor/tatoeba/'
PER_CARD = 2
MIN_TOKENS, MAX_TOKENS = 4, 14


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
    from wordfreq import zipf_frequency
    n = len(tokens)
    if not (MIN_TOKENS <= n <= MAX_TOKENS):
        return None
    hard = sum(1 for t in tokens if zipf_frequency(t, 'es') < 3.5 and t != target)
    return (hard, n, len(text))


def build():
    links, spa, ita = load_pairs()
    deck = json.load(open('data/deck.json'))
    words = {c['es'] for c in deck}
    senses = {c['es']: {s.lower() for s in c['senses']} | {c['it'].lower()}
              for c in deck}

    es_nlp = spacy.load('es_core_news_md', disable=['ner', 'parser'])
    it_nlp = spacy.load('it_core_news_md', disable=['ner', 'parser'])

    # Index the Italian side once: which senses does each Italian sentence hold?
    ita_ids = list(ita)
    ita_words = {}
    for sid, doc in zip(ita_ids, it_nlp.pipe([ita[i] for i in ita_ids], batch_size=256)):
        ita_words[sid] = ({t.lemma_.lower() for t in doc if t.is_alpha}
                          | {t.text.lower() for t in doc if t.is_alpha})

    ids = list(spa)
    candidates = collections.defaultdict(list)
    for sid, doc in zip(ids, es_nlp.pipe([spa[i] for i in ids], batch_size=256)):
        toks = [t.lemma_.lower() for t in doc if t.is_alpha]
        hits = {t for t in toks if t in words}
        if not hits:
            continue
        pair_ids = [i for i in links[sid] if i in ita]
        if not pair_ids:
            continue
        for target in hits:
            # the Italian half must show the word too, which is what makes
            # this a sense check and not just a lookup
            ok = [i for i in pair_ids if ita_words.get(i, set()) & senses[target]]
            if not ok:
                continue
            s = score(spa[sid], toks, target)
            if s is not None:
                candidates[target].append((s, sid, ok[0]))

    out, used = {}, 0
    for card in deck:
        best = sorted(candidates.get(card['es'], []))[:PER_CARD]
        rows = [{'es': spa[sid], 'it': ita[iid]} for _, sid, iid in best]
        if rows:
            out[card['es']] = rows
            used += len(rows)
    return out, used


if __name__ == '__main__':
    out, used = build()
    with open('lab/data/sentences.json', 'w') as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(',', ':'))
    old = json.load(open('data/sentences.json'))
    deck = json.load(open('data/deck.json'))
    print(f'cards with examples: {len(out)} of {len(deck)}   ({used} sentences)')
    print(f'  was (Spanish-only match): {len(old)}')
    print(f'  lost: {len(set(old) - set(out))}   gained: {len(set(out) - set(old))}')
