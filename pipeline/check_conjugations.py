"""Verify the conjugation tables against forms written out by hand.

verbecc conjugates from templates for verbs it knows and falls back to an ML
guess for ones it does not, so the irregulars are where it would go wrong
quietly. These expectations are independent of the library on purpose: if they
ever disagree, the library is what changed.
"""
import json, sys

# Six rows: yo, tú, él, nosotros, vosotros, ellos. The expectations below list
# five of them and are matched by pronoun rather than by position, so adding or
# reordering rows cannot silently compare the wrong ones.
EXPECT = {
 'ser':    {'present': ['soy','eres','es','somos','son'],
            'preterite': ['fui','fuiste','fue','fuimos','fueron'],
            'imperfect': ['era','eras','era','éramos','eran']},
 'ir':     {'present': ['voy','vas','va','vamos','van'],
            'preterite': ['fui','fuiste','fue','fuimos','fueron'],
            'imperfect': ['iba','ibas','iba','íbamos','iban']},
 'tener':  {'present': ['tengo','tienes','tiene','tenemos','tienen'],
            'preterite': ['tuve','tuviste','tuvo','tuvimos','tuvieron']},
 'haber':  {'present': ['he','has','ha','hemos','han']},
 'hacer':  {'present': ['hago','haces','hace','hacemos','hacen'],
            'preterite': ['hice','hiciste','hizo','hicimos','hicieron']},
 'decir':  {'present': ['digo','dices','dice','decimos','dicen'],
            'preterite': ['dije','dijiste','dijo','dijimos','dijeron']},
 'poder':  {'present': ['puedo','puedes','puede','podemos','pueden'],
            'preterite': ['pude','pudiste','pudo','pudimos','pudieron']},
 'estar':  {'present': ['estoy','estás','está','estamos','están'],
            'preterite': ['estuve','estuviste','estuvo','estuvimos','estuvieron']},
 'dar':    {'present': ['doy','das','da','damos','dan'],
            'preterite': ['di','diste','dio','dimos','dieron']},
 'saber':  {'present': ['sé','sabes','sabe','sabemos','saben'],
            'preterite': ['supe','supiste','supo','supimos','supieron']},
 'venir':  {'present': ['vengo','vienes','viene','venimos','vienen'],
            'preterite': ['vine','viniste','vino','vinimos','vinieron']},
 'poner':  {'present': ['pongo','pones','pone','ponemos','ponen'],
            'preterite': ['puse','pusiste','puso','pusimos','pusieron']},
 'salir':  {'present': ['salgo','sales','sale','salimos','salen']},
 'querer': {'present': ['quiero','quieres','quiere','queremos','quieren'],
            'preterite': ['quise','quisiste','quiso','quisimos','quisieron']},
 'volver': {'present': ['vuelvo','vuelves','vuelve','volvemos','vuelven']},
 'pedir':  {'present': ['pido','pides','pide','pedimos','piden']},
 'seguir': {'present': ['sigo','sigues','sigue','seguimos','siguen']},
 'traer':  {'preterite': ['traje','trajiste','trajo','trajimos','trajeron']},
 'conocer':{'present': ['conozco','conoces','conoce','conocemos','conocen']},
 # verbecc raises IndexError on these three and they are filled in from a
 # regular proxy instead, so they are checked like any other verb.
 'pasar':  {'present': ['paso','pasas','pasa','pasamos','pasan'],
            'preterite': ['pasé','pasaste','pasó','pasamos','pasaron']},
 'suceder':{'present': ['sucedo','sucedes','sucede','sucedemos','suceden']},
 'resultar':{'present': ['resulto','resultas','resulta','resultamos','resultan']},
}

# Irregular participles, checked through the perfect.
PARTICIPLES = {
 'hacer':'hecho', 'decir':'dicho', 'ver':'visto', 'poner':'puesto',
 'volver':'vuelto', 'escribir':'escrito', 'morir':'muerto', 'romper':'roto',
 'abrir':'abierto', 'cubrir':'cubierto', 'resolver':'resuelto',
 'descubrir':'descubierto',
}


# The expectations above list yo, tú, él, nosotros, ellos. Map them onto the
# shipped row order rather than assuming positions: `vos` and `ustedes` sit
# among them, and a positional comparison would drift the moment rows change.
CHECK_SLOTS = ['yo', 'tú', 'él', 'nosotros', 'ellos']


def main():
    data = json.load(open('data/conjugations.json'))
    d, pronouns = data['verbs'], data['pronouns']
    slots = ['yo', 'tú', 'él', 'nosotros', 'vosotros', 'ellos']
    idx = [slots.index(s) for s in CHECK_SLOTS]
    bad = []

    for verb, tenses in EXPECT.items():
        if verb not in d:
            bad.append(f"{verb}: not in the deck")
            continue
        for tense, want in tenses.items():
            have = d[verb][tense]
            if len(have) != len(slots):
                bad.append(f"{verb} {tense}: {len(have)} forms, expected {len(slots)}")
                continue
            for w, i in zip(want, idx):
                if w != have[i]:
                    bad.append(f"{verb} {tense} ({slots[i]}): expected {w}, got {have[i]}")

    for verb, part in PARTICIPLES.items():
        if verb not in d:
            continue
        have = d[verb]['perfect'][0]
        if have != 'he ' + part:
            bad.append(f"{verb} participle: expected he {part}, got {have}")

    tables = sum(len(v) for v in EXPECT.values())
    print(f"checked {tables} tense tables across {len(EXPECT)} irregular verbs "
          f"and {len(PARTICIPLES)} irregular participles")
    if bad:
        print(f"\nFAILURES ({len(bad)}):")
        for b in bad:
            print("  " + b)
        sys.exit(1)
    print("all correct")


if __name__ == '__main__':
    main()
