"""Italian prompts that belong to more than one Spanish card.

The deck is keyed on the Spanish word, so the Italian -> Spanish direction is
the Spanish -> Italian card read backwards. That is fine until two Spanish
words share a primary Italian gloss: `fare` is the prompt for arrancar, echar,
formar, hacer and pasear, and only one of them is on the card being graded.
Answering with any of the others is correct and used to look wrong.

This emits, for each colliding Italian prompt, every Spanish word that answers
it, so the card can show the alternatives when it flips. Nothing here changes
card ids -- the map is looked up at review time, so review history survives.
"""
import json
from collections import defaultdict

POS_LABEL = {
    'n': 'noun', 'vblex': 'verb', 'adj': 'adjective', 'adv': 'adverb',
    'pr': 'preposition', 'prn': 'pronoun', 'cnj': 'conjunction',
    'det': 'determiner', 'ij': 'expression', 'num': 'number',
}


# Mirrors POS_GROUPS in js/deck.js: Apertium splits verbs and conjunctions
# finer than a learner cares about, and `preadv` is just an adverb.
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
    """The part-of-speech group, as the code the app already labels with.

    A code rather than a word, so the card can render these with exactly the
    same heading logic as the Spanish -> Italian side.
    """
    for g in ('vblex', 'n', 'adj', 'adv', 'pr', 'prn', 'cnj', 'det', 'ij', 'num'):
        if g in pos_groups(card):
            return g
    return None


def build(deck):
    by_prompt = defaultdict(list)
    for card in deck:
        by_prompt[card['it']].append(card)

    out = {}
    for prompt, cards in by_prompt.items():
        if len(cards) < 2:
            continue
        # Sort by frequency so the answer a learner is likeliest to want is
        # named first.
        cards.sort(key=lambda c: -c.get('zipf', 0))
        out[prompt] = [
            {'es': c['es'], 'pos': group_for(c)}
            for c in cards
        ]
    return out


def main():
    deck = json.load(open('data/deck.json'))
    coll = build(deck)
    with open('data/collisions.json', 'w') as fh:
        json.dump(coll, fh, ensure_ascii=False, separators=(',', ':'))

    cards = sum(len(v) for v in coll.values())
    print(f'{len(coll)} Italian prompts answer more than one Spanish card')
    print(f'{cards} cards affected of {len(deck)}')
    worst = sorted(coll.items(), key=lambda kv: -len(kv[1]))[:8]
    for prompt, alts in worst:
        shown = ', '.join(f"{a['es']} ({POS_LABEL.get(a['pos'], a['pos'])})" for a in alts)
        print(f'  {prompt:14s} -> {shown}')


if __name__ == '__main__':
    main()
