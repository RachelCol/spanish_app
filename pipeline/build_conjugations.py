"""Conjugation tables for the verbs in the deck.

Five tenses only, chosen for what gets someone speaking rather than for
completeness: present, the ir + a + infinitive near future, preterite,
imperfect, and present perfect.

The Italian column is the point. Two rows deliberately show the same Italian
form -- `ho parlato` sits opposite both `hablé` and `he hablado` -- because
that collision IS the lesson: one Italian past maps onto two Spanish ones, and
choosing between them is the single most frequent mistake available to an
Italian speaker. Pairing the preterite with `parlai` instead would be formally
tidy and would teach the wrong habit, since the passato remoto is not what
modern Italian actually uses.
"""
import json, sys, re
from verbecc import CompleteConjugator, LangCodeISO639_1 as L
from wordfreq import zipf_frequency

ES_SLOTS = ['yo', 'tú', 'él', 'nosotros', 'vosotros', 'ellos']
IT_SLOTS = ['io', 'tu', 'lui', 'noi', 'voi', 'loro']

IT_INFINITIVE = re.compile(r'(are|ere|ire|rre)$')


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


def build():
    deck = json.load(open('data/deck.json'))
    verbs = [c for c in deck if c['pos'].startswith('vb')]
    es = CompleteConjugator(L.es)
    it = CompleteConjugator(L.it)

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

        # The Italian column needs an Italian infinitive to conjugate.
        ital = next((s for s in card['senses'] if IT_INFINITIVE.search(s) and ' ' not in s), None)
        if ital:
            try:
                i = json.loads(it.conjugate(ital).to_json())
                entry['it_verb'] = ital
                entry['present']['it']   = forms(i, 'indicativo', 'presente', IT_SLOTS, 'it')
                entry['near']['it']      = forms(i, 'indicativo', 'futuro', IT_SLOTS, 'it')
                entry['imperfect']['it'] = forms(i, 'indicativo', 'imperfetto', IT_SLOTS, 'it')
                pp = forms(i, 'indicativo', 'passato-prossimo', IT_SLOTS, 'it')
                entry['preterite']['it'] = pp      # deliberately the same form
                entry['perfect']['it']   = pp      # as the row above
            except Exception:
                pass

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
    with_it = sum(1 for v in data.values() if 'it_verb' in v)
    print(f"with an Italian column: {with_it}")
    d = data.get('hablar') or next(iter(data.values()))
    for k in ('present','near','preterite','imperfect','perfect'):
        print(f"\n  {k}\n    ES {d[k]['es']}\n    IT {d[k].get('it')}")
