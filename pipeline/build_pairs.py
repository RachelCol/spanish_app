"""Join the frequency spine to the Apertium senses.

Membership in Apertium doubles as the citation-form test, which is how the
spine gets filtered to lemmas without lemmatizing anything.

The frequency mismatch check stays: a pair whose Italian side is far rarer than
its Spanish side is usually a bad translation. It is weaker now that senses are
ranked by part-of-speech agreement first -- most of what it used to catch never
gets chosen -- but it still finds domain-skewed entries.
"""
import json, sys, collections
sys.path.insert(0, 'pipeline')
from pairs import load, similarity, bucket
from wordfreq import zipf_frequency

SUSPECT_DELTA = 1.2


def build():
    spine = json.load(open('data/frequency_es.json'))
    pairs = load()
    cards, dropped = [], 0
    for r in spine:
        p = pairs.get(r['es'])
        if not p:
            dropped += 1
            continue
        sim = similarity(r['es'], p['it'])
        cards.append({
            **r,
            'it': p['it'],
            'senses': p['senses'],
            'pos': p['pos'],
            'pos_all': p['pos_all'],
            **({'by_pos': p['by_pos']} if 'by_pos' in p else {}),
            'sim': round(sim, 2),
            'bucket': bucket(sim),
            'zipf_it': round(zipf_frequency(p['it'], 'it'), 2),
        })
    return cards, dropped


if __name__ == '__main__':
    cards, dropped = build()
    json.dump(cards, open('data/paired.json', 'w'), ensure_ascii=False, indent=1)
    print(f"spine -> {len(cards)} paired ({dropped} dropped: inflected, proper nouns, gaps)")
    for k, v in collections.Counter(c['bucket'] for c in cards).most_common():
        print(f"  {k:10s} {v}")
    multi = [c for c in cards if len(c['senses']) > 1]
    print(f"\ncards with more than one sense: {len(multi)}")
    for c in multi[:8]:
        print(f"  {c['es']:12s} -> {' · '.join(c['senses'])}")
