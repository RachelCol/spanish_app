"""Gender for the nouns in the deck, read off real usage.

Not guessed from endings. For each noun the corpus is asked which articles
actually precede it, across 441k Spanish and 982k Italian sentences, and the
answer is whatever speakers do.

The one place raw article counts lie is the `el agua` class: a feminine noun
beginning with a stressed a- takes `el` in the singular, for sound alone. Those
are caught by checking the plural, where the article is unaffected -- `las
aguas` -- so the card can show `el agua` and still label it feminine, which is
the whole point of labelling it.
"""
import csv, json, re, collections

V = 'vendor/tatoeba/'
MIN_EVIDENCE = 2          # below this the counts mean nothing
RATIO = 3                 # how lopsided before we call it

ES_M = {'el', 'un'}
ES_F = {'la', 'una'}
ES_MP = {'los', 'unos'}
ES_FP = {'las', 'unas'}

IT_M = {'il', 'lo', 'un', 'uno'}
IT_F = {'la', 'una'}
IT_MP = {'i', 'gli', 'dei', 'degli'}
IT_FP = {'le', 'delle'}

ES_ARTICLE = re.compile(r"\b(el|la|los|las|un|una|unos|unas)\s+([a-záéíóúüñ]+)")
IT_ARTICLE = re.compile(r"\b(il|lo|la|i|gli|le|un|uno|una|dei|degli|delle)\s+([a-zàèéìòù']+)")

# A feminine noun starting with a stressed a- borrows `el`. `ha-` counts too.
A_INITIAL = re.compile(r'^(a|ha)', re.I)


def read_column(path):
    out = []
    for r in csv.reader(open(path), delimiter='\t', quoting=csv.QUOTE_NONE):
        if len(r) == 3:
            out.append(r[2].lower())
    return out


def article_counts(sentences, pattern):
    counts = collections.defaultdict(collections.Counter)
    for text in sentences:
        for art, noun in pattern.findall(text):
            counts[noun][art] += 1
    return counts


def decide(counter, masc, fem):
    m = sum(v for k, v in counter.items() if k in masc)
    f = sum(v for k, v in counter.items() if k in fem)
    if m + f < MIN_EVIDENCE:
        return None
    if m >= f * RATIO:
        return 'm'
    if f >= m * RATIO:
        return 'f'
    return 'mf'          # genuinely both: el/la estudiante


def plurals_of(word, lang):
    if lang == 'es':
        if word.endswith('z'):
            return [word[:-1] + 'ces']
        return [word + 's'] if word[-1] in 'aeiouáéíóú' else [word + 'es']
    # Italian: -a → -e, -o/-e → -i
    if word.endswith('a'):
        return [word[:-1] + 'e', word[:-1] + 'i']
    if word[-1] in 'oe':
        return [word[:-1] + 'i']
    return [word]


def gender_for(word, counts, lang):
    sing_m, sing_f = (ES_M, ES_F) if lang == 'es' else (IT_M, IT_F)
    plur_m, plur_f = (ES_MP, ES_FP) if lang == 'es' else (IT_MP, IT_FP)

    singular = decide(counts.get(word, collections.Counter()), sing_m, sing_f)

    plural = collections.Counter()
    for p in plurals_of(word, lang):
        plural.update(counts.get(p, collections.Counter()))
    from_plural = decide(plural, plur_m, plur_f)

    # The el-agua case: singular says masculine only because of the article it
    # borrows, while the plural gives the real answer.
    if lang == 'es' and singular == 'm' and A_INITIAL.match(word) and from_plural == 'f':
        return 'f', 'borrowed-el'

    if singular:
        return singular, 'singular'
    if from_plural:
        return from_plural, 'plural'
    return None, None


def article_for(word, gender, lang):
    """The article a speaker would actually use with it."""
    if gender == 'mf':
        return 'el/la' if lang == 'es' else 'il/la'
    if lang == 'es':
        if gender == 'f' and A_INITIAL.match(word):
            return 'el'          # borrowed, and the card still says f
        return 'el' if gender == 'm' else 'la'
    if gender == 'f':
        return "l'" if word[0] in 'aeiou' else 'la'
    if word[0] in 'aeiou':
        return "l'"
    if word[:2] in ('sp', 'st', 'sc', 'sb', 'sf', 'sg', 'sl', 'sm', 'sn', 'sr', 'sv', 'ps', 'gn', 'pn') \
       or word[0] in 'zxy':
        return 'lo'
    return 'il'


def is_noun(card):
    """Worth an article and a gender letter.

    Carrying a noun tag is not enough on its own. `ver`, `hablar` and `decir`
    all carry one, for the nominalised infinitive, and `el ver` on a verb card
    is nonsense. Pronouns likewise: `alguien` is tagged a noun and takes no
    article. But the primary tag alone is too strict the other way -- `madre`,
    `derecho` and `ganador` come out adjectives on a tag vote and are plainly
    nouns.
    """
    tags = card['pos_all']
    if 'n' not in tags:
        return False
    return not any(t.startswith('vb') or t == 'prn' for t in tags)


def main():
    es_counts = article_counts(read_column(V + 'spa_sentences.tsv'), ES_ARTICLE)
    it_counts = article_counts(read_column(V + 'ita_sentences.tsv'), IT_ARTICLE)

    deck = json.load(open('data/deck.json'))
    out, stats = {}, collections.Counter()
    for card in deck:
        if not is_noun(card):
            continue
        g, how = gender_for(card['es'], es_counts, 'es')
        if not g:
            stats['unknown'] += 1
            continue
        entry = {'g': g, 'art': article_for(card['es'], g, 'es')}
        stats[g] += 1
        if how == 'borrowed-el':
            stats['borrowed-el'] += 1

        # The Italian side too, for whichever senses are single words.
        senses = {}
        for sense in card['senses']:
            if ' ' in sense:
                continue
            ig, _ = gender_for(sense, it_counts, 'it')
            if ig:
                senses[sense] = {'g': ig, 'art': article_for(sense, ig, 'it')}
        if senses:
            entry['it'] = senses
        out[card['es']] = entry

    json.dump(out, open('data/gender.json', 'w'),
              ensure_ascii=False, separators=(',', ':'))
    import os
    total = sum(1 for c in deck if 'n' in c['pos_all'])
    print(f"deck nouns: {total}")
    print(f"  gendered: {len(out)} ({100*len(out)/total:.0f}%)   unknown: {stats['unknown']}")
    print(f"  masculine {stats['m']}, feminine {stats['f']}, either {stats['mf']}")
    print(f"  feminine nouns taking a borrowed el: {stats['borrowed-el']}")
    print(f"  with an Italian gender too: {sum(1 for v in out.values() if 'it' in v)}")
    print(f"data/gender.json: {os.path.getsize('data/gender.json')/1024:.0f} KB\n")
    for w in ('casa', 'libro', 'mano', 'día', 'flor', 'agua', 'águila', 'problema',
              'estudiante', 'ciudad', 'viaje', 'sangre'):
        if w in out:
            e = out[w]
            it = ', '.join(
                f"{v['art']}{'' if v['art'].endswith(chr(39)) else ' '}{k} ({v['g']})"
                for k, v in (e.get('it') or {}).items())
            print(f"  {e['art']:6s} {w:12s} {e['g']:3s}   {it}")


if __name__ == '__main__':
    main()
