"""Verify the conjugation tables against forms written out by hand.

verbecc conjugates from templates for verbs it knows and falls back to an ML
guess for ones it does not, so the irregulars are where it would go wrong
quietly. These expectations are independent of the library on purpose: if they
ever disagree, the library is what changed.
"""
import json, sys

EXPECT = {
 'ser':    {'present': ['soy','eres','es','somos','sois','son'],
            'preterite': ['fui','fuiste','fue','fuimos','fuisteis','fueron'],
            'imperfect': ['era','eras','era','éramos','erais','eran']},
 'ir':     {'present': ['voy','vas','va','vamos','vais','van'],
            'preterite': ['fui','fuiste','fue','fuimos','fuisteis','fueron'],
            'imperfect': ['iba','ibas','iba','íbamos','ibais','iban']},
 'tener':  {'present': ['tengo','tienes','tiene','tenemos','tenéis','tienen'],
            'preterite': ['tuve','tuviste','tuvo','tuvimos','tuvisteis','tuvieron']},
 'haber':  {'present': ['he','has','ha','hemos','habéis','han']},
 'hacer':  {'present': ['hago','haces','hace','hacemos','hacéis','hacen'],
            'preterite': ['hice','hiciste','hizo','hicimos','hicisteis','hicieron']},
 'decir':  {'present': ['digo','dices','dice','decimos','decís','dicen'],
            'preterite': ['dije','dijiste','dijo','dijimos','dijisteis','dijeron']},
 'poder':  {'present': ['puedo','puedes','puede','podemos','podéis','pueden'],
            'preterite': ['pude','pudiste','pudo','pudimos','pudisteis','pudieron']},
 'estar':  {'present': ['estoy','estás','está','estamos','estáis','están'],
            'preterite': ['estuve','estuviste','estuvo','estuvimos','estuvisteis','estuvieron']},
 'dar':    {'present': ['doy','das','da','damos','dais','dan'],
            'preterite': ['di','diste','dio','dimos','disteis','dieron']},
 'saber':  {'present': ['sé','sabes','sabe','sabemos','sabéis','saben'],
            'preterite': ['supe','supiste','supo','supimos','supisteis','supieron']},
 'venir':  {'present': ['vengo','vienes','viene','venimos','venís','vienen'],
            'preterite': ['vine','viniste','vino','vinimos','vinisteis','vinieron']},
 'poner':  {'present': ['pongo','pones','pone','ponemos','ponéis','ponen'],
            'preterite': ['puse','pusiste','puso','pusimos','pusisteis','pusieron']},
 'salir':  {'present': ['salgo','sales','sale','salimos','salís','salen']},
 'querer': {'present': ['quiero','quieres','quiere','queremos','queréis','quieren'],
            'preterite': ['quise','quisiste','quiso','quisimos','quisisteis','quisieron']},
 'volver': {'present': ['vuelvo','vuelves','vuelve','volvemos','volvéis','vuelven']},
 'pedir':  {'present': ['pido','pides','pide','pedimos','pedís','piden']},
 'seguir': {'present': ['sigo','sigues','sigue','seguimos','seguís','siguen']},
 'traer':  {'preterite': ['traje','trajiste','trajo','trajimos','trajisteis','trajeron']},
 'conocer':{'present': ['conozco','conoces','conoce','conocemos','conocéis','conocen']},
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
