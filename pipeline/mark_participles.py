"""Tag past participles as adjectives too.

Spanish past participles double as adjectives -- `hecho a mano`, `una puerta
abierta`, `el año pasado` -- but Apertium usually files them under a single
tag, so `hecho` reached the deck as a noun and nothing else.

The participles are not hand-listed. Every one is already sitting in the
conjugation tables, since the perfect is `he` plus the participle, so the list
derives from data that is verified rather than from a list that can rot.

Runs after build_conjugations.py, and rewrites data/deck.json in place.
"""
import json


def participles(conj):
    """Map each participle back to the verb it came from."""
    out = {}
    for verb, entry in conj['verbs'].items():
        forms = entry.get('perfect', {}).get('es') or []
        if not forms:
            continue
        parts = forms[0].split()          # "he hecho"
        if len(parts) == 2:
            out.setdefault(parts[1], verb)
    return out


def main():
    conj = json.load(open('data/conjugations.json'))
    deck = json.load(open('data/deck.json'))
    parts = participles(conj)

    tagged = []
    for card in deck:
        verb = parts.get(card['es'])
        if not verb or 'adj' in card['pos_all']:
            continue
        # A participle is adjectival by nature; say so, keeping the tag it
        # already had first since that is what the word usually is.
        card['pos_all'] = card['pos_all'] + ['adj']
        tagged.append((card['es'], verb))

    json.dump(deck, open('data/deck.json', 'w'),
              ensure_ascii=False, separators=(',', ':'))
    print(f"participles in the deck: {len(parts)}")
    print(f"cards gaining an adjective tag: {len(tagged)}")
    for es, verb in tagged[:20]:
        print(f"  {es:14s} (from {verb})")


if __name__ == '__main__':
    main()
