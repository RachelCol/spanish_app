# -*- coding: utf-8 -*-
"""Grammar lessons: what an Italian speaker needs to unlearn.

Written rather than extracted. Every claim is one I can state plainly and
would defend; anything I was unsure of is left out rather than hedged, which
is why some obvious topics are thinner than they might be.

Ordered by how much trouble each thing causes, not by how a textbook would
sequence it.
"""

LESSONS = [
 {
  "id": "auxiliary",
  "title": "One auxiliary, not two",
  "summary": "The essere/avere choice simply does not exist in Spanish.",
  "body": [
   "Italian makes you choose an auxiliary for every compound tense, and then "
   "agree the participle when it is essere. Spanish has one auxiliary, "
   "**haber**, for every verb without exception — and the participle never "
   "agrees.",
   "This is the single biggest simplification Spanish offers you. Movement "
   "verbs, reflexives, **ser** itself: all take haber.",
  ],
  "pairs": [
   ["ho parlato", "he hablado", "avere → haber"],
   ["sono andato", "he ido", "essere → haber too"],
   ["sono stato", "he sido", "even ser takes haber"],
   ["mi sono lavato", "me he lavado", "reflexives too"],
   ["siamo andati", "hemos ido", "no plural agreement"],
   ["è andata", "ha ido", "no feminine agreement"],
  ],
  "watch": "Your instinct will produce *soy ido* and *somos idos*. There is no "
           "context in which that is right.",
 },
 {
  "id": "past-tense",
  "title": "Which past tense to reach for",
  "summary": "Italian's everyday past maps to the Spanish preterite, not the perfect.",
  "body": [
   "In Italian the **passato prossimo** is the ordinary past and the passato "
   "remoto is literary or southern. So your instinct is: past → compound tense.",
   "In Latin American Spanish that instinct is wrong. The ordinary past is the "
   "simple **pretérito**. The compound **pretérito perfecto** exists and looks "
   "exactly like the passato prossimo, which is the trap: it is used far less.",
   "This affects nearly every past-tense sentence you will say, which makes it "
   "the highest-frequency error available to you.",
  ],
  "pairs": [
   ["Ieri ho mangiato alle otto.", "Ayer comí a las ocho.", "not *he comido*"],
   ["Sono andato al mercato.", "Fui al mercado.", "not *he ido*"],
   ["Che cosa hai detto?", "¿Qué dijiste?", "not *has dicho*"],
   ["Stamattina ho visto Ana.", "Esta mañana vi a Ana.", "still the preterite"],
  ],
  "watch": "In Spain `he comido hoy` is normal and much closer to Italian. You "
           "chose Latin American, so the preterite is your default.",
 },
 {
  "id": "articles-possessive",
  "title": "Possessives take no article",
  "summary": "il mio libro → mi libro. Spanish never puts an article there.",
  "body": [
   "Italian requires the definite article before a possessive: *il mio libro*, "
   "*la tua casa*. Spanish never does.",
   "Italian's own exception — dropping the article for singular unmodified "
   "family members, *mio fratello* — is a rule you can forget entirely, because "
   "Spanish treats every noun the same way.",
   "Spanish also has a second, stressed possessive that goes **after** the noun: "
   "*un amigo mío*, *¿es tuyo?* That is the form that looks like Italian's.",
  ],
  "pairs": [
   ["il mio libro", "mi libro", "no article"],
   ["la tua casa", "tu casa", "no article"],
   ["mio fratello", "mi hermano", "same in Spanish, no exception needed"],
   ["i miei genitori", "mis padres", "the possessive itself pluralises"],
   ["un mio amico", "un amigo mío", "stressed form goes after"],
  ],
  "watch": "*el mi libro* is the error, and it is one you will make.",
 },
 {
  "id": "partitive",
  "title": "There is no partitive",
  "summary": "del pane, dei libri → just pan, libros.",
  "body": [
   "Italian uses *del*, *della*, *dei*, *delle* to mean 'some'. Spanish has no "
   "partitive at all. Where Italian puts a word, Spanish puts nothing.",
   "This one is easy to fix because the correction is always deletion.",
  ],
  "pairs": [
   ["Vorrei del pane.", "Quiero pan.", "no word for 'some'"],
   ["Ho comprato dei libri.", "Compré libros.", "bare plural"],
   ["Bevi del vino?", "¿Bebes vino?", "bare noun"],
   ["C'è dell'acqua?", "¿Hay agua?", "bare noun"],
  ],
  "watch": "*Quiero del pan* is wrong. So is *compré de los libros*.",
 },
 {
  "id": "ser-estar",
  "title": "ser and estar are not essere and stare",
  "summary": "The concept transfers; the boundary does not.",
  "body": [
   "Italian has essere and stare, so the idea of two 'to be' verbs is familiar. "
   "The problem is that the line falls in a different place, and the cognate "
   "pull is towards the wrong one.",
   "**estar** covers location, and temporary or changed states — including many "
   "that Italian expresses with essere.",
   "**ser** covers identity, origin, material, time, and inherent qualities.",
   "Location is the clearest rule: things and people are **estar**. The one "
   "exception is events, which use ser: *la fiesta es en mi casa*.",
  ],
  "pairs": [
   ["Sono stanco.", "Estoy cansado.", "state → estar"],
   ["Sono a casa.", "Estoy en casa.", "location → estar"],
   ["Sono italiana.", "Soy italiana.", "identity → ser"],
   ["È mia sorella.", "Es mi hermana.", "identity → ser"],
   ["La zuppa è fredda.", "La sopa está fría.", "it has gone cold → estar"],
   ["Il ghiaccio è freddo.", "El hielo es frío.", "ice is inherently cold → ser"],
   ["Dov'è la stazione?", "¿Dónde está la estación?", "location → estar"],
   ["La festa è a casa mia.", "La fiesta es en mi casa.", "event → ser"],
  ],
  "watch": "*soy cansado* means something like 'I am a tiring person'. *soy en "
           "casa* is simply wrong.",
 },
 {
  "id": "personal-a",
  "title": "The personal a",
  "summary": "Spanish marks a human direct object with a. Italian has nothing like it.",
  "body": [
   "When the direct object of a verb is a specific person, Spanish puts **a** in "
   "front of it. Italian does not, and there is no equivalent to transfer from.",
   "It applies to people and to pets, not to things. It also applies to *alguien*, "
   "*nadie*, and to *quién* in questions.",
  ],
  "pairs" : [
   ["Vedo Maria.", "Veo a María.", "a person → a"],
   ["Vedo la casa.", "Veo la casa.", "a thing → no a"],
   ["Cerco mio fratello.", "Busco a mi hermano.", "a person → a"],
   ["Cerco un taxi.", "Busco un taxi.", "a thing → no a"],
   ["Non vedo nessuno.", "No veo a nadie.", "nadie takes it"],
   ["Chi hai visto?", "¿A quién viste?", "questions too"],
  ],
  "watch": "Omitting it is the classic Italian-speaker error, and it is audible "
           "in every sentence about a person.",
 },
 {
  "id": "por-para",
  "title": "per splits into por and para",
  "summary": "One Italian preposition, two Spanish ones, and the choice is obligatory.",
  "body": [
   "Italian *per* does several jobs. Spanish divides them between **por** and "
   "**para**, and you must pick.",
   "**para** points forwards: destination, purpose, recipient, deadline.",
   "**por** points backwards or through: cause, exchange, duration, means, "
   "movement through a place.",
   "The shortest test that works most of the time: *para* answers 'what for?', "
   "*por* answers 'why?' or 'in exchange for what?'",
  ],
  "pairs": [
   ["Parto per Madrid.", "Salgo para Madrid.", "destination → para"],
   ["È per te.", "Es para ti.", "recipient → para"],
   ["Per domani.", "Para mañana.", "deadline → para"],
   ["Grazie per il regalo.", "Gracias por el regalo.", "cause → por"],
   ["L'ho comprato per dieci euro.", "Lo compré por diez euros.", "exchange → por"],
   ["Ho studiato per due ore.", "Estudié por dos horas.", "duration → por"],
   ["Passo per il parco.", "Paso por el parque.", "through → por"],
  ],
  "watch": "There is no safe default. Guessing *por* everywhere is wrong about "
           "half the time.",
 },
 {
  "id": "prepositions-place",
  "title": "Where things are, and where you are going",
  "summary": "Italian's a/in/da do not line up with Spanish a/en/de.",
  "body": [
   "Italian chooses between *a* and *in* partly by the kind of place — *a Roma* "
   "but *in Italia*. Spanish chooses by whether there is movement.",
   "**en** for being somewhere, whatever the place. **a** for going there.",
   "Italian *da* has no single Spanish equivalent. For a person's place it "
   "becomes *en casa de* or *a casa de*; for origin it becomes *de*.",
  ],
  "pairs": [
   ["Sono a Roma.", "Estoy en Roma.", "location → en"],
   ["Sono in Italia.", "Estoy en Italia.", "also en"],
   ["Vado a Roma.", "Voy a Roma.", "movement → a"],
   ["Vado in Italia.", "Voy a Italia.", "still a"],
   ["Sono a casa.", "Estoy en casa.", "en, not a"],
   ["Vado da Mario.", "Voy a casa de Mario.", "no equivalent of da"],
   ["Vengo da Roma.", "Vengo de Roma.", "origin → de"],
  ],
  "watch": "*Estoy a Roma* and *voy en Roma* are the two errors, and they are "
           "mirror images of each other.",
 },
 {
  "id": "ne-ci",
  "title": "ne and ci do not exist",
  "summary": "Two Italian pronouns with no Spanish counterpart at all.",
  "body": [
   "Italian *ne* ('of it', 'of them') and locative *ci* ('there') have no Spanish "
   "equivalents. Spanish either repeats the noun or says nothing.",
   "The risk is not getting them wrong — it is inventing something to carry them.",
  ],
  "pairs": [
   ["Ne voglio due.", "Quiero dos.", "ne disappears"],
   ["Quanti ne hai?", "¿Cuántos tienes?", "ne disappears"],
   ["Ci vado domani.", "Voy mañana.", "locative ci disappears"],
   ["Non ci credo.", "No lo creo.", "lo, not ci"],
   ["C'è un problema.", "Hay un problema.", "c'è → hay"],
   ["Ci sono due libri.", "Hay dos libros.", "hay never pluralises"],
  ],
  "watch": "**hay** is invariable. *Han dos libros* is a very common error.",
 },
 {
  "id": "gender-shifts",
  "title": "Words that changed gender",
  "summary": "Most nouns keep their gender. These did not.",
  "body": [
   "Gender transfers almost perfectly, which makes the exceptions worth "
   "memorising individually — there are not many, and you will otherwise get "
   "them wrong every time.",
   "Nouns ending in -aje, -or and -ma (from Greek) are masculine in Spanish; "
   "nouns in -umbre, -dad, -tad and -ción are feminine.",
  ],
  "pairs": [
   ["il sangue", "la sangre", "m → f"],
   ["il latte", "la leche", "m → f"],
   ["il fiore", "la flor", "m → f"],
   ["il naso", "la nariz", "m → f"],
   ["il sale", "la sal", "m → f"],
   ["il miele", "la miel", "m → f"],
   ["il costume", "la costumbre", "m → f"],
   ["l'origine (f)", "el origen", "f → m"],
   ["l'analisi (f)", "el análisis", "f → m"],
   ["il viaggio", "el viaje", "both m, note the -aje"],
  ],
  "watch": "*el sangre* and *la origen* are the shape of this error.",
 },
 {
  "id": "sound-shifts",
  "title": "How the words changed shape",
  "summary": "Most vocabulary transfers by rule. Learn the rule, not the words.",
  "body": [
   "Italian and Spanish share the great majority of their vocabulary, and the "
   "differences are largely regular. Recognising the correspondences turns "
   "thousands of Italian words into Spanish ones.",
   "Spanish has **no double consonants** except rr, ll, cc and nn. Italian's "
   "doubles simplify.",
  ],
  "pairs": [
   ["conversazione", "conversación", "-zione → -ción"],
   ["città", "ciudad", "-tà → -dad"],
   ["chiave", "llave", "chi- → ll-"],
   ["fiamma", "llama", "fi- → ll-"],
   ["pioggia", "lluvia", "pi- → ll-"],
   ["scuola", "escuela", "s+cons → es-"],
   ["spagnolo", "español", "s+cons → es-, gn → ñ"],
   ["famiglia", "familia", "gli → li"],
   ["dubbio", "duda", "no doubles"],
   ["difficile", "difícil", "no doubles, -ile → -il"],
  ],
  "watch": "Doubling a consonant is the most audible Italian accent in Spanish.",
 },
 {
  "id": "false-friends",
  "title": "Words that lie to you",
  "summary": "The small set where the cognate is actively wrong.",
  "body": [
   "These are dangerous precisely because you will say them with confidence. "
   "There are not many, and they are worth learning as a list.",
  ],
  "pairs": [
   ["burro = butter", "el burro = donkey", "butter is la mantequilla"],
   ["salire = to go up", "salir = to leave", "to go up is subir"],
   ["guardare = to look at", "guardar = to keep", "to look at is mirar"],
   ["aceto = vinegar", "el aceite = oil", "vinegar is el vinagre"],
   ["largo = wide", "largo = long", "wide is ancho"],
   ["imbarazzata = embarrassed", "embarazada = pregnant", "embarrassed is avergonzada"],
   ["sposa = bride", "la esposa = wife", ""],
   ["prendere = to take", "prender = to arrest, switch on", "to take is tomar"],
   ["topo = mouse", "el topo = mole", "mouse is el ratón"],
   ["gamba = leg", "la gamba = prawn", "leg is la pierna"],
  ],
  "watch": "*Quiero burro en el pan* asks for donkey on your bread.",
 },
]
