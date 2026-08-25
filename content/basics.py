# -*- coding: utf-8 -*-
"""Basics: a plain outline of how Spanish works, in English.

Not comparative. The Comparisons section handles what Italian gets wrong; this
one just lays out the machinery, so there is somewhere to look up what the
subjunctive is for or which article goes where.
"""

SECTIONS = [
 {
  "id": "articles",
  "title": "Articles",
  "summary": "Four definite, four indefinite, and the places Spanish uses none.",
  "body": [
   "Definite: **el** (masculine singular), **la** (feminine singular), **los** "
   "and **las** for the plurals. Indefinite: **un**, **una**, and the plurals "
   "**unos** and **unas**, which mean 'some'.",
   "Two contractions are compulsory. **a + el = al** and **de + el = del**. "
   "They never occur uncontracted.",
   "A feminine noun beginning with a stressed **a-** or **ha-** takes **el** in "
   "the singular, for sound alone. The noun stays feminine and its adjectives "
   "agree as feminine: *el agua fría*, *las aguas frías*.",
   "Spanish uses articles where English does not: with abstract nouns, with "
   "languages, with parts of the body, and with days of the week to mean 'on'.",
   "It uses none at all in a few places worth knowing: after most uses of "
   "*hablar* with a language, before an unmodified profession, and where "
   "another language would use a partitive.",
  ],
  "examples": [
   ["el libro, la casa", "the book, the house", ""],
   ["los libros, las casas", "the books, the houses", ""],
   ["un libro, una casa", "a book, a house", ""],
   ["unos libros", "some books", ""],
   ["Voy al centro.", "I'm going downtown.", "a + el"],
   ["La casa del vecino.", "The neighbour's house.", "de + el"],
   ["el agua fría", "the cold water", "el for sound, adjective still feminine"],
   ["Me gusta el café.", "I like coffee.", "abstract noun takes the article"],
   ["Hablo español.", "I speak Spanish.", "no article after hablar"],
   ["Es profesora.", "She's a teacher.", "no article before a bare profession"],
   ["Quiero pan.", "I want some bread.", "no partitive exists"],
   ["El lunes voy a Madrid.", "On Monday I'm going to Madrid.", "el means 'on'"],
   ["Los lunes no trabajo.", "On Mondays I don't work.", "plural means 'every'"],
   ["mi libro", "my book", "possessives never take an article"],
  ],
 },
 {
  "id": "nouns",
  "title": "Nouns and gender",
  "summary": "Endings predict gender most of the time, and the exceptions cluster.",
  "body": [
   "Nouns ending in **-o** are usually masculine and those in **-a** usually "
   "feminine, but the endings that predict gender reliably are the longer ones.",
   "Reliably feminine: **-ción**, **-sión**, **-dad**, **-tad**, **-tud**, "
   "**-umbre**, **-ie**.",
   "Reliably masculine: **-aje**, **-or**, and the Greek-derived **-ma** group.",
   "Plurals add **-s** after a vowel and **-es** after a consonant. A final "
   "**-z** becomes **-ces**.",
  ],
  "examples": [
   ["la nación, la ciudad", "the nation, the city", "-ción, -dad are feminine"],
   ["la costumbre, la serie", "the custom, the series", "-umbre, -ie feminine"],
   ["el viaje, el color", "the journey, the colour", "-aje, -or masculine"],
   ["el problema, el sistema", "the problem, the system", "-ma from Greek, masculine"],
   ["el día, la mano", "the day, the hand", "the common exceptions"],
   ["casa → casas", "house → houses", "vowel takes -s"],
   ["ciudad → ciudades", "city → cities", "consonant takes -es"],
   ["luz → luces", "light → lights", "-z becomes -ces"],
  ],
 },
 {
  "id": "adjectives",
  "title": "Adjectives",
  "summary": "They agree, they usually follow, and moving one changes the meaning.",
  "body": [
   "Adjectives agree in gender and number. Those ending in **-o** have four "
   "forms; most others have two, varying only for number.",
   "The normal position is **after** the noun. Putting one in front is a "
   "deliberate move: it makes the quality inherent or emotional rather than "
   "distinguishing.",
   "A few change meaning outright depending on position, and those are worth "
   "learning as pairs.",
   "**Grande** shortens to **gran** before any singular noun, and **bueno** and "
   "**malo** shorten to **buen** and **mal** before a masculine singular.",
  ],
  "examples": [
   ["un coche rojo", "a red car", "normal position"],
   ["una casa roja", "a red house", "agrees in gender"],
   ["unos coches rojos", "some red cars", "and in number"],
   ["un libro interesante", "an interesting book", "-e adjectives vary only in number"],
   ["un hombre pobre", "a poor (penniless) man", "after: distinguishing"],
   ["un pobre hombre", "a poor (pitiable) man", "before: emotional"],
   ["un amigo viejo", "an old (elderly) friend", ""],
   ["un viejo amigo", "an old (long-standing) friend", ""],
   ["una gran ciudad", "a great city", "grande → gran before the noun"],
   ["un buen día", "a good day", "bueno → buen"],
  ],
 },
 {
  "id": "pronouns",
  "title": "Pronouns",
  "summary": "Subjects are usually dropped; objects go in front, or attach behind.",
  "body": [
   "Subject pronouns exist but are normally omitted, because the verb ending "
   "already says who. Using one adds emphasis or contrast.",
   "Direct objects: **me, te, lo/la, nos, os, los/las**. Indirect objects: "
   "**me, te, le, nos, os, les**.",
   "Placement: before a conjugated verb, or attached to the end of an "
   "infinitive, a gerund or an affirmative command. With a verb plus infinitive "
   "either position is allowed.",
   "When two pronouns meet, the indirect comes first. If both are third person, "
   "**le** and **les** become **se**.",
  ],
  "examples": [
   ["Hablo español.", "I speak Spanish.", "subject dropped"],
   ["Yo hablo español, ella no.", "I speak Spanish, she doesn't.", "used for contrast"],
   ["Lo veo.", "I see him / it.", "before the conjugated verb"],
   ["Quiero verlo.", "I want to see it.", "attached to the infinitive"],
   ["Lo quiero ver.", "I want to see it.", "or in front — both are fine"],
   ["Estoy leyéndolo.", "I'm reading it.", "attached to the gerund"],
   ["¡Dámelo!", "Give it to me!", "attached to the command"],
   ["Me lo das.", "You give it to me.", "indirect first"],
   ["Se lo doy.", "I give it to him.", "le + lo becomes se lo"],
  ],
 },
 {
  "id": "tenses",
  "title": "The verb system",
  "summary": "Four moods, and a small number of tenses that carry most of the work.",
  "body": [
   "Verbs come in three families by infinitive ending: **-ar**, **-er**, "
   "**-ir**. The endings differ, the patterns do not.",
   "**Indicative** states what is. The tenses in daily use are the present, the "
   "preterite for completed past actions, the imperfect for ongoing or habitual "
   "past, the future, and the present perfect.",
   "In practice the future tense is used less than **ir a + infinitive**, which "
   "does the same job and is what people say.",
   "**Subjunctive** covers what is wished, doubted, required or hypothetical. "
   "Two tenses matter: the present and the imperfect.",
   "**Conditional** covers what would happen, and softens requests.",
   "**Imperative** gives commands. Negative commands are borrowed from the "
   "subjunctive, which is why *no hables* looks nothing like *habla*.",
   "Every compound tense is **haber** plus the past participle. There is only "
   "one auxiliary and the participle never agrees.",
  ],
  "examples": [
   ["hablo, como, vivo", "I speak, I eat, I live", "present, the three families"],
   ["hablé", "I spoke", "preterite: a completed action"],
   ["hablaba", "I was speaking / I used to speak", "imperfect: ongoing or habitual"],
   ["he hablado", "I have spoken", "present perfect: haber + participle"],
   ["hablaré", "I will speak", "future"],
   ["voy a hablar", "I'm going to speak", "used far more than the future"],
   ["hablaría", "I would speak", "conditional"],
   ["que yo hable", "that I speak", "present subjunctive"],
   ["si hablara", "if I spoke", "imperfect subjunctive"],
   ["¡Habla!", "Speak!", "affirmative command"],
   ["¡No hables!", "Don't speak!", "negative command, from the subjunctive"],
  ],
 },
 {
  "id": "ser-estar-basics",
  "title": "ser, estar and hay",
  "summary": "Two verbs for 'to be', and a third word for 'there is'.",
  "body": [
   "**ser** for identity, origin, material, profession, time and inherent "
   "qualities. **estar** for location, and for states that are temporary or "
   "changed.",
   "The same adjective can take either, and the choice changes the meaning: "
   "*es aburrido* is boring, *está aburrido* is bored.",
   "**hay** means 'there is' and 'there are'. It never changes form, however "
   "many things there are.",
  ],
  "examples": [
   ["Soy profesora.", "I'm a teacher.", "profession → ser"],
   ["Es de Madrid.", "He's from Madrid.", "origin → ser"],
   ["Son las tres.", "It's three o'clock.", "time → ser"],
   ["Estoy en casa.", "I'm at home.", "location → estar"],
   ["Estoy cansada.", "I'm tired.", "state → estar"],
   ["La sopa está fría.", "The soup is cold.", "it has gone cold"],
   ["El hielo es frío.", "Ice is cold.", "inherently"],
   ["Hay un problema.", "There is a problem.", ""],
   ["Hay dos problemas.", "There are two problems.", "hay never pluralises"],
  ],
 },
 {
  "id": "word-order-basics",
  "title": "Word order",
  "summary": "Subject–verb–object by default, and freer than English after that.",
  "body": [
   "The default is subject, verb, object, but Spanish moves things for emphasis "
   "far more readily than English, and the subject often follows the verb.",
   "Questions normally invert: the verb comes before the subject.",
   "Nothing may come between **haber** and its participle. Adverbs go before "
   "the whole verb phrase or after it, never inside.",
   "A direct object that is a specific person takes **a** in front — the "
   "personal a — which has no counterpart in English.",
  ],
  "examples": [
   ["Ana compró el libro.", "Ana bought the book.", "default order"],
   ["El libro lo compró Ana.", "The book, Ana bought it.", "fronted for emphasis"],
   ["¿Compró Ana el libro?", "Did Ana buy the book?", "verb before subject"],
   ["¿Dónde vive tu hermana?", "Where does your sister live?", "inverted"],
   ["Siempre he dicho eso.", "I've always said that.", "adverb outside the verb phrase"],
   ["No he dicho nada.", "I haven't said anything.", "double negative is required"],
   ["Veo a María.", "I see María.", "personal a"],
   ["Veo la casa.", "I see the house.", "no a for a thing"],
  ],
 },
 {
  "id": "questions",
  "title": "Questions and negation",
  "summary": "Marks at both ends, accented question words, and negatives that stack.",
  "body": [
   "Questions open with **¿** and close with **?**; exclamations use **¡ !**. "
   "The opening mark goes where the question starts, not necessarily at the "
   "start of the sentence.",
   "Question words carry a written accent: **qué, quién, dónde, cuándo, cómo, "
   "cuánto, cuál, por qué**. They keep it in indirect questions and lose it "
   "when not questioning.",
   "Negation is **no** before the verb. Spanish requires a double negative: if a "
   "negative word follows the verb, *no* must still be there.",
  ],
  "examples": [
   ["¿Cómo estás?", "How are you?", "marks at both ends"],
   ["¡Qué bonito!", "How lovely!", "exclamation marks"],
   ["María, ¿adónde vas?", "María, where are you going?", "opens at the question"],
   ["No sé dónde vive.", "I don't know where he lives.", "indirect question keeps the accent"],
   ["La casa donde vivo.", "The house where I live.", "not a question, no accent"],
   ["No veo nada.", "I don't see anything.", "no is still required"],
   ["No viene nadie.", "Nobody is coming.", "double negative"],
   ["Nadie viene.", "Nobody is coming.", "unless the negative comes first"],
  ],
 },
]
