"""Attach example sentences to the deck, from Tatoeba.

Tatoeba is the right source here rather than a translation site: the sentences
are written by speakers, they come with an Italian translation already linked,
and the licence allows shipping them, so the examples work offline like the
rest of the app. CC BY 2.0 FR -- attribution is in the UI and the README.

Only about 18k Spanish sentences have an Italian pair, which is what limits
coverage. That is still 97% of the `common` band and 88% of `useful`.

This is the one place a lemmatizer earns its keep: finding sentences for
`hablar` means matching `habla`, `habló` and `hablando`, which needs context to
resolve. That is a different job from the frequency spine, which deliberately
avoids lemmatizing at all.
"""
import json, csv, collections
import spacy
from wordfreq import zipf_frequency

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
    n = len(tokens)
    if n < MIN_TOKENS or n > MAX_TOKENS:
        return None
    # An example is only useful if the rest of the sentence is already known.
    others = [t for t in tokens if t != target]
    if not others:
        return None
    mean_zipf = sum(zipf_frequency(t, 'es') for t in others) / len(others)
    return (n * 0.35) - mean_zipf


def build():
    links, spa, ita = load_pairs()
    deck = json.load(open('data/deck.json'))
    words = {c['es'] for c in deck}

    nlp = spacy.load('es_core_news_md', disable=['ner', 'parser'])
    ids = list(spa)
    candidates = collections.defaultdict(list)

    for sid, doc in zip(ids, nlp.pipe([spa[i] for i in ids], batch_size=256)):
        toks = [t.lemma_.lower() for t in doc if t.is_alpha]
        hits = {t for t in toks if t in words}
        if not hits:
            continue
        for target in hits:
            s = score(spa[sid], toks, target)
            if s is not None:
                candidates[target].append((s, sid))

    out, used = {}, 0
    for card in deck:
        best = sorted(candidates.get(card['es'], []))[:PER_CARD]
        rows = []
        for _, sid in best:
            pair = next((ita[i] for i in links[sid] if i in ita), None)
            if pair:
                rows.append({'es': spa[sid], 'it': pair})
        if rows:
            out[card['es']] = rows
            used += len(rows)
    return out, used


if __name__ == '__main__':
    import os
    sentences, used = build()
    json.dump(sentences, open('data/sentences.json', 'w'),
              ensure_ascii=False, separators=(',', ':'))
    deck = json.load(open('data/deck.json'))
    print(f"cards with examples: {len(sentences)} / {len(deck)}  "
          f"({100*len(sentences)/len(deck):.0f}%)")
    print(f"sentences used: {used}")
    print(f"data/sentences.json: {os.path.getsize('data/sentences.json')/1024:.0f} KB")
    for w in ('hermano', 'agua', 'noche', 'ciudad'):
        if w in sentences:
            print(f"\n{w}:")
            for r in sentences[w]:
                print(f"   {r['es']}\n   {r['it']}")
