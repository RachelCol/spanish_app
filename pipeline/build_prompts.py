"""Every Italian prompt, and the Spanish words that answer it.

The deck is keyed on Spanish, so the Italian -> Spanish direction used to be
each card read backwards through its single primary gloss. That left 529
Italian senses that never asked you anything -- including `poi`, `pero`,
`qualche` and `comunque`, which is most of a day's speech.

So a prompt here is an Italian word, not a card. It carries every Spanish word
it can be answered with, and a secondary sense earns its own prompt when it is
common enough in Italian to be worth producing.

Multiword Italian is admitted only where it is already a card's primary gloss;
new prompts are single words. Phrases need their own handling for gender,
audio and sentence highlighting, and that is a separate job.

collisions.json is what the pre-refactor app used and is still read by
classic/; this file supersedes it.
"""
import json
from collections import defaultdict

from wordfreq import zipf_frequency

# An Italian sense that is not a card's primary earns a prompt at this
# frequency. 4.0 takes `poi`, `pero` and `comunque` and stops well before the
# tail; 3.5 would add another 175 with a much worse hit rate.
SECONDARY_FLOOR = 4.0

POS_ORDER = ('vblex', 'n', 'adj', 'adv', 'pr', 'prn', 'cnj', 'det', 'ij', 'num')

GROUPS = {
    'vblex': 'vblex', 'vbmod': 'vblex', 'vbhaver': 'vblex', 'vbser': 'vblex',
    'adv': 'adv', 'preadv': 'adv',
    'cnjcoo': 'cnj', 'cnjsub': 'cnj', 'cnjadv': 'cnj',
}


def pos_groups(card):
    out = set()
    for tag in card.get('pos_all') or [card.get('pos')]:
        if tag:
            out.add(GROUPS.get(str(tag), str(tag)))
    return out


def group_for(card):
    for g in POS_ORDER:
        if g in pos_groups(card):
            return g
    return None


def build(deck):
    by_prompt = defaultdict(list)

    for card in deck:
        by_prompt[card['it']].append(card)

    for card in deck:
        for sense in card['senses']:
            if sense == card['it'] or ' ' in sense:
                continue
            if zipf_frequency(sense, 'it') < SECONDARY_FLOOR:
                continue
            # by_prompt is a defaultdict: touching it before the frequency
            # test above would mint an empty prompt for every rejected sense.
            if card not in by_prompt[sense]:
                by_prompt[sense].append(card)

    out = {}
    for prompt, cards in by_prompt.items():
        # Commonest Spanish word first: the answer most likely wanted leads.
        cards = sorted(cards, key=lambda c: -c.get('zipf', 0))
        out[prompt] = [{'es': c['es'], 'pos': group_for(c)} for c in cards]
    return out


def main(out='data/prompts.json'):
    deck = json.load(open('data/deck.json'))
    prompts = build(deck)
    with open(out, 'w') as fh:
        json.dump(prompts, fh, ensure_ascii=False, separators=(',', ':'))

    primary = {c['it'] for c in deck}
    added = [p for p in prompts if p not in primary]
    multi = {p: v for p, v in prompts.items() if len(v) > 1}
    reachable = {a['es'] for v in prompts.values() for a in v}

    print(f'{len(prompts)} Italian prompts  ({len(deck)} cards)')
    print(f'  carried over from primary senses : {len(prompts) - len(added)}')
    print(f'  new, from common secondary senses: {len(added)}')
    print(f'  prompts with more than one answer: {len(multi)}')
    print(f'  Spanish words reachable          : {len(reachable)} of {len(deck)}')
    unreachable = {c["es"] for c in deck} - reachable
    if unreachable:
        print(f'  UNREACHABLE                      : {len(unreachable)} '
              f'{sorted(unreachable)[:8]}')
    print()
    for p in sorted(added, key=lambda p: -zipf_frequency(p, 'it'))[:10]:
        print(f'  + {p:14s} -> {", ".join(a["es"] for a in prompts[p])}')


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else 'data/prompts.json')
