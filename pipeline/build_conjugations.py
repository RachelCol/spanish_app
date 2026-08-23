"""Conjugation tables for the verbs in the deck.

Every simple tense, grouped by mood, plus two things that are not simple
tenses and earn their place anyway: the present perfect, because it is the one
compound tense in daily use and the one an Italian speaker will reach for
wrongly, and `ir a` + infinitive, because Latin American speakers use it far
more than the simple future.

Deliberately absent: the future subjunctive, which survives only in legal
formulas, and every other compound tense, which are all `haber` plus the
participle once the perfect has shown how that works.

The Italian column was removed earlier and is not coming back: a card can gloss
to several Italian verbs -- tener is avere and tenere -- and conjugating one of
them beside the Spanish asserts a mapping that does not hold. The contrast
lives in the per-tense notes instead, which describe how Italian behaves
without naming an equivalent verb.
"""
import json, re, difflib
from verbecc import CompleteConjugator, LangCodeISO639_1 as L
from wordfreq import zipf_frequency

# Six rows, the paradigm as it is taught. ustedes shares the ellos form and
# rides with it; vosotros keeps its own row even though Latin America does not
# use it, because leaving it out makes the second person plural look missing.
SLOTS = ['yo', 'tú', 'él', 'nosotros', 'vosotros', 'ellos']
PRONOUNS = ['yo', 'tú', 'él/ella/usted', 'nosotros', 'vosotros', 'ellos/ustedes']

# The imperative has no first person singular -- you cannot command yourself --
# and its usted forms are borrowed from the subjunctive.
IMP_SLOTS = ['tú', 'él', 'nosotros', 'vosotros', 'ellos']
IMP_PRONOUNS = ['tú', 'usted', 'nosotros', 'vosotros', 'ustedes']

# (key, verbecc mood, verbecc tense, uses the imperative row set)
TENSES = [
    ('present',      'indicativo', 'presente', False),
    ('preterite',    'indicativo', 'pretérito-perfecto-simple', False),
    ('imperfect',    'indicativo', 'pretérito-imperfecto', False),
    ('future',       'indicativo', 'futuro', False),
    ('perfect',      'indicativo', 'pretérito-perfecto-compuesto', False),
    ('subjPresent',  'subjuntivo', 'presente', False),
    ('subjImperfect','subjuntivo', 'pretérito-imperfecto-1', False),
    ('impAffirm',    'imperativo', 'afirmativo', True),
    ('impNegative',  'imperativo', 'negativo', True),
    ('conditional',  'condicional', 'presente', False),
]

# haber's third person is `hay` in the library: right for the impersonal
# "there is", wrong for the auxiliary paradigm these tables show.
OVERRIDES = {('haber', 'present', 'él'): 'ha'}

# Regular present endings, used to work out which letters a verb changes.
REGULAR_PRESENT = {
    'ar': ['o', 'as', 'a', 'amos', 'áis', 'an'],
    'er': ['o', 'es', 'e', 'emos', 'éis', 'en'],
    'ir': ['o', 'es', 'e', 'imos', 'ís', 'en'],
}

# A stem-changer marks exactly four forms -- the boot: yo, tú, él, ellos. Above
# that the verb is suppletive rather than stem-changing: `ser` and `ir` share
# almost nothing with what a regular verb would produce, so marking `so[y]`,
# `[er]es`, `[e]s` highlights the whole word and teaches nothing.
MAX_MARKED_FORMS = 4


def present_marks(infinitive, forms):
    """Character ranges where each form departs from the regular pattern."""
    ending = infinitive[-2:]
    if ending not in REGULAR_PRESENT or len(forms) != 6:
        return None
    stem = infinitive[:-2]
    marks, marked_count = [], 0
    for actual, suffix in zip(forms, REGULAR_PRESENT[ending]):
        spans = []
        for tag, _, _, j1, j2 in difflib.SequenceMatcher(
                None, stem + suffix, actual).get_opcodes():
            if tag in ('replace', 'insert') and j2 > j1:
                spans.append([j1, j2])
        if spans:
            marked_count += 1
        marks.append(spans)
    if marked_count > MAX_MARKED_FORMS:
        return None
    return marks if any(marks) else []


def _pick(word, lang):
    """verbecc offers alternates as "veduto/visto". Take the commoner one."""
    if '/' not in word:
        return word
    return max(word.split('/'), key=lambda a: zipf_frequency(a, lang))


def forms(conj, mood, tense, slots):
    """One form per slot, in order, with the pronoun stripped off."""
    try:
        rows = conj['moods'][mood][tense]
    except (KeyError, TypeError):
        return None
    by_pronoun = {}
    for r in rows:
        pr = r.get('pr')
        if pr in slots and pr not in by_pronoun:
            text = r['c'][0] if isinstance(r.get('c'), list) else r.get('c', '')
            # Imperatives come back as "no digas"; only a leading pronoun goes.
            if text.startswith(pr + ' '):
                text = text[len(pr) + 1:]
            by_pronoun[pr] = ' '.join(_pick(p, 'es') for p in text.split())
    out = [by_pronoun.get(s) for s in slots]
    return out if all(out) else None


def build():
    deck = json.load(open('data/deck.json'))
    verbs = [c for c in deck if any(p.startswith('vb') for p in c['pos_all'])]
    es = CompleteConjugator(L.es)

    ir_present = forms(json.loads(es.conjugate('ir').to_json()),
                       'indicativo', 'presente', SLOTS)

    out, skipped = {}, []
    for card in verbs:
        try:
            c = json.loads(es.conjugate(card['es']).to_json())
        except Exception:
            skipped.append(card['es'])
            continue

        entry = {}
        for key, mood, tense, imperative in TENSES:
            f = forms(c, mood, tense, IMP_SLOTS if imperative else SLOTS)
            if f:
                entry[key] = f

        # A construction rather than a tense, so it is assembled here.
        if ir_present:
            entry['near'] = [f'{v} a {card["es"]}' for v in ir_present]

        if 'present' not in entry:
            skipped.append(card['es'])
            continue

        for (verb, key, slot), form in OVERRIDES.items():
            if verb == card['es'] and entry.get(key):
                entry[key][SLOTS.index(slot)] = form

        pres = entry['present']
        marks = present_marks(card['es'], pres)
        if marks is not None:
            entry['marks'] = marks

        out[card['es']] = entry
    return out, skipped


if __name__ == '__main__':
    import os
    data, skipped = build()
    json.dump({'pronouns': PRONOUNS, 'imperativePronouns': IMP_PRONOUNS,
               'verbs': data},
              open('data/conjugations.json', 'w'),
              ensure_ascii=False, separators=(',', ':'))
    print(f"verbs conjugated: {len(data)}  (skipped {len(skipped)})")
    print(f"data/conjugations.json: {os.path.getsize('data/conjugations.json')/1024:.0f} KB")
    d = data.get('decir') or next(iter(data.values()))
    for k, _, _, _ in TENSES:
        print(f"  {k:14s} {d.get(k)}")
    print(f"  {'near':14s} {d.get('near')}")
