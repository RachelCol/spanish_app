"""Conjugation tables for the verbs in the deck.

Five tenses only, chosen for what gets someone speaking rather than for
completeness: present, the ir + a + infinitive near future, preterite,
imperfect, and present perfect.

Spanish only. An Italian column was tempting -- and it is where the contrast
between the preterite and the perfect shows up most clearly -- but a card can
carry several Italian senses, and conjugating just one of them next to the
Spanish asserts a one-to-one mapping that is not there. `tener` glosses to both
avere and dovere; putting `ho` beside `tengo` would teach that as fact.

The contrast survives as prose in the tense notes, which talk about how Italian
behaves without claiming any particular verb is the equivalent.
"""
import json, sys, re
from verbecc import CompleteConjugator, LangCodeISO639_1 as L
from wordfreq import zipf_frequency

# Latin American paradigm: no vosotros. Its slot is filled by ustedes, which
# takes the same form as ellos, so the two collapse into one row rather than
# printing the identical form twice.
ES_SLOTS = ['yo', 'tú', 'él', 'nosotros', 'ellos']

# Corrections to what verbecc returns. Kept tiny and explicit: check_conjugations.py
# verifies nineteen hard irregulars against forms written out by hand, and this
# is everything that came back wrong.
#
# haber third person is `hay` in the library -- right for the impersonal "there
# is", wrong for the auxiliary paradigm this table shows.
OVERRIDES = {
    ('haber', 'present', 2): 'ha',
}


def _pick(word, lang):
    """verbecc offers alternates as "veduto/visto". Take the commoner one --
    taking the first gave `ho veduto`, which is correct and not what anyone
    says."""
    if '/' not in word:
        return word
    alts = word.split('/')
    return max(alts, key=lambda a: zipf_frequency(a, lang))


def forms(conj, mood, tense, slots, lang):
    """Six forms in person order, with the pronoun stripped off."""
    try:
        rows = conj['moods'][mood][tense]
    except (KeyError, TypeError):
        return None
    by_pronoun = {}
    for r in rows:
        pr = r.get('pr')
        if pr in slots and pr not in by_pronoun:
            text = r['c'][0] if isinstance(r.get('c'), list) else r.get('c', '')
            if text.startswith(pr + ' '):
                text = text[len(pr) + 1:]
            text = ' '.join(_pick(part, lang) for part in text.split())
            by_pronoun[pr] = text
    out = [by_pronoun.get(s) for s in slots]
    return out if all(out) else None


# Diphthongisations and vowel raisings, longest first so e->ie is tried before
# e->i.
STEM_PATTERNS = [('e', 'ie'), ('o', 'ue'), ('u', 'ue'), ('i', 'ie'), ('e', 'i')]


def stem_change(infinitive, third_person):
    """Compare the infinitive stem with the third-person present stem.

    Third person rather than first: `tener` gives `tengo`, whose inserted g is
    a first-person quirk that hides the actual e->ie showing in `tiene`.
    """
    if not third_person or ' ' in third_person:
        return None
    if infinitive[-2:] not in ('ar', 'er', 'ir', 'ír'):
        return None
    inf_stem = infinitive[:-2]
    pres_stem = third_person[:-1]          # drop the -a / -e
    if pres_stem == inf_stem:
        return None
    for src, dst in STEM_PATTERNS:
        i = inf_stem.rfind(src)
        if i == -1:
            continue
        if inf_stem[:i] + dst + inf_stem[i + 1:] == pres_stem:
            return f'{src}\u2192{dst}'
    return None


def irregular_yo(infinitive, first_person, third_person):
    """A yo form the stem change does not already account for.

    `puedo` follows from poder's o->ue and needs no separate mention; `tengo`
    does not follow from tener's e->ie and does.
    """
    if not first_person or ' ' in first_person:
        return None
    if infinitive[-2:] not in ('ar', 'er', 'ir', 'ír'):
        return None
    expected = {infinitive[:-2] + 'o'}
    if third_person and ' ' not in third_person:
        expected.add(third_person[:-1] + 'o')       # stem as it appears in él
    return None if first_person in expected else first_person


def build():
    deck = json.load(open('data/deck.json'))
    verbs = [c for c in deck if c['pos'].startswith('vb')]
    es = CompleteConjugator(L.es)

    # "voy a hablar" -- built here rather than looked up, since it is a
    # construction rather than a tense.
    ir = json.loads(es.conjugate('ir').to_json())
    ir_present = forms(ir, 'indicativo', 'presente', ES_SLOTS, 'es')

    out, skipped = {}, []
    for card in verbs:
        try:
            e = json.loads(es.conjugate(card['es']).to_json())
        except Exception:
            skipped.append(card['es'])
            continue

        entry = {
            'present':  {'es': forms(e, 'indicativo', 'presente', ES_SLOTS, 'es')},
            'near':     {'es': [f'{v} a {card["es"]}' for v in ir_present]},
            'preterite':{'es': forms(e, 'indicativo', 'pretérito-perfecto-simple', ES_SLOTS, 'es')},
            'imperfect':{'es': forms(e, 'indicativo', 'pretérito-imperfecto', ES_SLOTS, 'es')},
            'perfect':  {'es': forms(e, 'indicativo', 'pretérito-perfecto-compuesto', ES_SLOTS, 'es')},
        }

        pres = entry['present']['es']
        if pres:
            change = stem_change(card['es'], pres[2])
            yo = irregular_yo(card['es'], pres[0], pres[2])
            if change or yo:
                entry['stem'] = {}
                if change:
                    entry['stem']['change'] = change
                    entry['stem']['example'] = pres[2]
                if yo:
                    entry['stem']['yo'] = yo

        for (verb, tense, idx), form in OVERRIDES.items():
            if verb == card['es'] and entry.get(tense, {}).get('es'):
                entry[tense]['es'][idx] = form

        if entry['present']['es']:
            out[card['es']] = entry
    return out, skipped


if __name__ == '__main__':
    import os
    data, skipped = build()
    json.dump(data, open('data/conjugations.json', 'w'),
              ensure_ascii=False, separators=(',', ':'))
    print(f"verbs conjugated: {len(data)}  (skipped {len(skipped)})")
    print(f"data/conjugations.json: {os.path.getsize('data/conjugations.json')/1024:.0f} KB")
    d = data.get('hablar') or next(iter(data.values()))
    for k in ('present','near','preterite','imperfect','perfect'):
        print(f"  {k:10s} {d[k]['es']}")
