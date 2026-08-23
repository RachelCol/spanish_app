"""Verify the conjugation tables against forms written out by hand.

verbecc conjugates from templates for verbs it knows and falls back to an ML
guess for ones it does not, so the irregulars are where it would go wrong
quietly. These expectations are independent of the library on purpose: if they
ever disagree, the library is what changed.
"""
import json, sys

# Five forms, not six: the tables use the Latin American paradigm, where
# ustedes shares its form with ellos and vosotros does not appear.
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
}

# Irregular participles, checked through the perfect.
PARTICIPLES = {
 'hacer':'hecho', 'decir':'dicho', 'ver':'visto', 'poner':'puesto',
 'volver':'vuelto', 'escribir':'escrito', 'morir':'muerto', 'romper':'roto',
 'abrir':'abierto', 'cubrir':'cubierto', 'resolver':'resuelto',
 'descubrir':'descubierto',
}


def main():
    d = json.load(open('data/conjugations.json'))
    bad = []

    for verb, tenses in EXPECT.items():
        if verb not in d:
            bad.append(f"{verb}: not in the deck")
            continue
        for tense, want in tenses.items():
            have = d[verb][tense]['es']
            for i, (w, h) in enumerate(zip(want, have)):
                if w != h:
                    bad.append(f"{verb} {tense}[{i}]: expected {w}, got {h}")

    for verb, part in PARTICIPLES.items():
        if verb not in d:
            continue
        have = d[verb]['perfect']['es'][0]
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
