"""Fill-in-the-blank drill items, generated from the Tatoeba pairs.

Nothing here is written. Every sentence is an attested Spanish sentence with an
attested Italian translation, and the gap is cut out of the real thing, so the
answer is what a speaker actually said rather than what I would have guessed.

Three banks: prepositions, articles, and the auxiliaries.

The auxiliary bank drills the split an Italian speaker cannot feel, because
one Italian verb is doing the work of two or three Spanish ones. `avere` is
`tener` when it owns something and `haber` when it holds up a participle;
`dovere` is `tener que` for a plain obligation and `deber` for a duty or a
debt; `essere` is `ser` or `estar` depending on what kind of being is meant.
The wrong options are the same person and tense of the rival verb, so the
choice is only ever about which verb, never about conjugating it.

The article bank includes items whose answer is no article at all, which is the
case an Italian speaker gets wrong most reliably -- `il mio libro` against `mi
libro`. Those are found by looking for a Spanish possessive whose Italian pair
puts an article in front of its own.
"""
import csv, json, re, collections, random

V = 'vendor/tatoeba/'
MAX_WORDS = 12
NO_ARTICLE = '—'

AUX = ['ser', 'estar', 'tener', 'haber', 'deber']

# Which verbs actually compete. A drill teaches nothing if the wrong answers
# are ones no Italian speaker would be tempted by.
AUX_RIVALS = {
    'ser':   ['estar', 'tener', 'haber'],
    'estar': ['ser', 'tener', 'haber'],
    'tener': ['haber', 'ser', 'deber'],
    'haber': ['tener', 'ser', 'estar'],
    'deber': ['tener', 'haber', 'estar'],
}
AUX_TENSES = ['present', 'preterite', 'imperfect', 'future', 'subjPresent']

PREPOSITIONS = ['a', 'en', 'de', 'por', 'para', 'con', 'sin',
                'sobre', 'entre', 'hasta', 'desde', 'hacia', 'según']

# Which prepositions plausibly compete for the same gap. A drill is only worth
# anything if the wrong options are ones you might actually pick.
PREP_RIVALS = {
    'a':      ['en', 'para', 'de'],
    'en':     ['a', 'de', 'con'],
    'de':     ['desde', 'en', 'a'],
    'por':    ['para', 'de', 'en'],
    'para':   ['por', 'a', 'de'],
    'con':    ['sin', 'en', 'de'],
    'sin':    ['con', 'de', 'a'],
    'sobre':  ['en', 'de', 'entre'],
    'entre':  ['con', 'sobre', 'en'],
    'hasta':  ['desde', 'a', 'hacia'],
    'desde':  ['de', 'hasta', 'hacia'],
    'hacia':  ['a', 'hasta', 'para'],
    'según':  ['para', 'por', 'con'],
}

ARTICLES = ['el', 'la', 'los', 'las', 'un', 'una']
ARTICLE_RIVALS = {
    'el':  ['la', 'un', NO_ARTICLE],
    'la':  ['el', 'una', NO_ARTICLE],
    'los': ['las', 'unos', NO_ARTICLE],
    'las': ['los', 'unas', NO_ARTICLE],
    'un':  ['una', 'el', NO_ARTICLE],
    'una': ['un', 'la', NO_ARTICLE],
}

# A Spanish possessive takes no article; the Italian equivalent takes one.
SPA_POSSESSIVE = re.compile(r'\b(mi|tu|su|mis|tus|sus|nuestro|nuestra|nuestros|nuestras)\s+\w+', re.I)
ITA_ARTICLED_POSSESSIVE = re.compile(
    r'\b(il|lo|la|i|gli|le)\s+(mio|mia|miei|mie|tuo|tua|tuoi|tue|suo|sua|suoi|sue|nostro|nostra|nostri|nostre)\b',
    re.I)


def load_pairs():
    links = collections.defaultdict(list)
    for r in csv.reader(open(V + 'spa-ita_links.tsv'), delimiter='\t'):
        if len(r) == 2:
            links[r[0]].append(r[1])

    def read(path, keep):
        out = {}
        for r in csv.reader(open(path), delimiter='\t', quoting=csv.QUOTE_NONE):
            if len(r) == 3 and r[0] in keep:
                out[r[0]] = r[2]
        return out

    spa = read(V + 'spa_sentences.tsv', set(links))
    ita = read(V + 'ita_sentences.tsv', {i for v in links.values() for i in v})
    pairs = []
    for sid, text in spa.items():
        other = next((ita[i] for i in links[sid] if i in ita), None)
        if other:
            pairs.append((text, other))
    return pairs


def word_count(text):
    return len(re.findall(r"[a-záéíóúüñ]+", text.lower()))


def blank_once(text, target):
    """Replace a standalone word with a gap, only if it appears exactly once.

    Once, so there is no question which gap is being asked about. Standalone,
    so `del` and `al` are never mistaken for `de` and `a`.
    """
    pattern = re.compile(r'(?<![\wáéíóúüñ])' + re.escape(target) + r'(?![\wáéíóúüñ])',
                         re.IGNORECASE)
    found = pattern.findall(text)
    if len(found) != 1:
        return None
    return pattern.sub('___', text)


def options(answer, rivals, pool):
    picks = [r for r in rivals if r != answer][:3]
    while len(picks) < 3:
        extra = random.choice(pool)
        if extra != answer and extra not in picks:
            picks.append(extra)
    out = picks + [answer]
    random.shuffle(out)
    return out


def build_prepositions(pairs, per_prep=14):
    by_prep = collections.defaultdict(list)
    for es, it in pairs:
        if word_count(es) > MAX_WORDS:
            continue
        for prep in PREPOSITIONS:
            gapped = blank_once(es, prep)
            if not gapped:
                continue
            by_prep[prep].append({
                'italian': it,
                'gapped': gapped,
                'answer': prep,
                'full': es,
            })
    items = []
    for prep, found in by_prep.items():
        found.sort(key=lambda r: word_count(r['full']))
        for row in found[:per_prep]:
            row['options'] = options(prep, PREP_RIVALS[prep], PREPOSITIONS)
            items.append(row)
    random.shuffle(items)
    return items


def build_auxiliaries(pairs, per_verb=22):
    """Gap a conjugated auxiliary; offer the same slot of its rivals."""
    conj = json.load(open('data/conjugations.json'))['verbs']
    # form -> (verb, tense, person), for forms only one of these verbs claims
    slot, clash = {}, set()
    for v in AUX:
        for tense in AUX_TENSES:
            for i, form in enumerate(conj.get(v, {}).get(tense, [])):
                f = form.lower()
                if ' ' in f:
                    continue
                if f in slot and slot[f][0] != v:
                    clash.add(f)
                slot[f] = (v, tense, i)
    for f in clash:
        slot.pop(f, None)          # `fue` is ser and ir; drop the ambiguous ones

    out, seen, made = [], set(), collections.Counter()
    for es, it in pairs:
        words = es.split()
        if not (3 <= len(words) <= MAX_WORDS):
            continue
        for i, w in enumerate(words):
            bare = re.sub(r"[^\wáéíóúüñ]", "", w.lower())
            hit = slot.get(bare)
            if not hit:
                continue
            verb, tense, person = hit
            if made[verb] >= per_verb or es in seen:
                continue
            rivals = []
            for r in AUX_RIVALS[verb]:
                forms = conj.get(r, {}).get(tense, [])
                if len(forms) > person and ' ' not in forms[person]:
                    rivals.append(forms[person])
            if len(rivals) < 2:
                continue
            gapped = words[:i] + ['___'] + words[i + 1:]
            row = {'italian': it, 'gapped': ' '.join(gapped), 'answer': w.strip('.,;:!?¿¡'),
                   'full': es}
            # Match the answer's case, or a sentence-initial gap gives the
            # answer away: `Tengo` beside `soy`, `debo`, `he`.
            if row['answer'][:1].isupper():
                rivals = [r[:1].upper() + r[1:] for r in rivals]
            row['options'] = options(row['answer'], rivals[:3], [])
            out.append(row)
            seen.add(es)
            made[verb] += 1
            break
    return out


def build_articles(pairs, per_article=16, no_article_target=24):
    by_article = collections.defaultdict(list)
    bare = []
    for es, it in pairs:
        if word_count(es) > MAX_WORDS:
            continue

        # Spanish possessive against an Italian article: the gap goes in front
        # of the possessive, and the answer is that nothing belongs there.
        m = SPA_POSSESSIVE.search(es)
        if m and ITA_ARTICLED_POSSESSIVE.search(it):
            start = m.start()
            gapped = es[:start] + '___ ' + es[start:]
            bare.append({'italian': it, 'gapped': gapped,
                         'answer': NO_ARTICLE, 'full': es})
            continue

        for art in ARTICLES:
            gapped = blank_once(es, art)
            if gapped:
                by_article[art].append({'italian': it, 'gapped': gapped,
                                        'answer': art, 'full': es})

    items = []
    for art, found in by_article.items():
        found.sort(key=lambda r: word_count(r['full']))
        for row in found[:per_article]:
            row['options'] = options(art, ARTICLE_RIVALS[art], ARTICLES)
            items.append(row)

    bare.sort(key=lambda r: word_count(r['full']))
    for row in bare[:no_article_target]:
        row['options'] = options(NO_ARTICLE, ['el', 'la', 'un'], ARTICLES)
        items.append(row)

    random.shuffle(items)
    return items


if __name__ == '__main__':
    random.seed(11)          # stable output between runs
    pairs = load_pairs()
    preps = build_prepositions(pairs)
    arts = build_articles(pairs)
    auxes = build_auxiliaries(pairs)
    json.dump({'prepositions': preps, 'articles': arts, 'auxiliaries': auxes},
              open('data/drill_bank.json', 'w'),
              ensure_ascii=False, separators=(',', ':'))

    import os
    print(f"pairs read: {len(pairs)}")
    print(f"preposition items: {len(preps)}")
    print(f"article items: {len(arts)}  "
          f"(no-article: {sum(1 for a in arts if a['answer'] == NO_ARTICLE)})")
    print(f"auxiliary items: {len(auxes)}")
    print(f"data/drill_bank.json: {os.path.getsize('data/drill_bank.json')/1024:.0f} KB\n")
    for row in auxes[:5]:
        print(f"  {row['italian']}\n  {row['gapped']}\n  {row['options']}  -> {row['answer']}\n")
    for row in preps[:4]:
        print(f"  {row['italian']}\n  {row['gapped']}\n  {row['options']}  -> {row['answer']}\n")
    for row in [a for a in arts if a['answer'] == NO_ARTICLE][:3]:
        print(f"  {row['italian']}\n  {row['gapped']}\n  {row['options']}  -> {row['answer']}\n")
