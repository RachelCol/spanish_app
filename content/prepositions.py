# -*- coding: utf-8 -*-
"""How Spanish prepositions map onto Italian ones.

Two passes over the same ground. The first goes Spanish → Italian, which is
what you need when producing. The second goes Italian → Spanish for the four
that cause real trouble, which is what you need when your instinct fires and
you have to check it.
"""

# Spanish preposition, what it covers, and which Italian ones land on it.
SPANISH = [
 {
  "prep": "a",
  "gloss": "movement, indirect object, time, manner — and people",
  "italian": "a, in (movement), and nothing at all for the personal a",
  "uses": [
   ["movement", "Voy a Madrid.", "Vado a Madrid."],
   ["movement to a country", "Voy a Italia.", "Vado in Italia.", "Italian in becomes a"],
   ["indirect object", "Le doy el libro a Ana.", "Do il libro ad Ana."],
   ["clock time", "A las tres.", "Alle tre."],
   ["manner", "A pie. A mano.", "A piedi. A mano."],
   ["before a person", "Veo a María.", "Vedo Maria.", "Italian has no equivalent"],
  ],
 },
 {
  "prep": "en",
  "gloss": "being somewhere, transport, periods of time",
  "italian": "a and in both — the distinction Italian makes here disappears",
  "uses": [
   ["in a city", "Estoy en Roma.", "Sono a Roma.", "Italian a becomes en"],
   ["in a country", "Estoy en Italia.", "Sono in Italia.", "Italian in becomes en"],
   ["at home", "Estoy en casa.", "Sono a casa."],
   ["transport", "Voy en tren.", "Vado in treno."],
   ["season, year", "En verano. En 2020.", "In estate. Nel 2020."],
   ["thinking about", "Pienso en ti.", "Penso a te.", "pensare a becomes pensar en"],
  ],
 },
 {
  "prep": "de",
  "gloss": "possession, origin, material, contents",
  "italian": "di, and da when it means where something came from",
  "uses": [
   ["possession", "El libro de Ana.", "Il libro di Ana."],
   ["origin", "Soy de Italia.", "Sono italiana.", "Italian prefers the adjective"],
   ["coming from", "Vengo de Roma.", "Vengo da Roma.", "Italian da becomes de"],
   ["material", "Una mesa de madera.", "Un tavolo di legno."],
   ["contents", "Un vaso de agua.", "Un bicchiere d'acqua."],
   ["at someone's place", "Estoy en casa de Mario.", "Sono da Mario.", "da has no single equivalent"],
  ],
 },
 {
  "prep": "por",
  "gloss": "cause, exchange, duration, movement through — it looks backwards",
  "italian": "per, and da for the agent of a passive",
  "uses": [
   ["cause", "Gracias por todo.", "Grazie per tutto."],
   ["reason", "Por eso no vine.", "Per questo non sono venuta."],
   ["exchange", "Lo compré por diez euros.", "L'ho comprato per dieci euro."],
   ["duration", "Estudié por dos horas.", "Ho studiato per due ore."],
   ["through a place", "Paso por el parque.", "Passo per il parco."],
   ["by means of", "Por teléfono.", "Per telefono."],
   ["passive agent", "Escrito por Ana.", "Scritto da Ana.", "Italian da becomes por"],
  ],
 },
 {
  "prep": "para",
  "gloss": "purpose, recipient, destination, deadline — it looks forwards",
  "italian": "per, the same word that also becomes por",
  "uses": [
   ["purpose", "Para aprender.", "Per imparare."],
   ["recipient", "Es para ti.", "È per te."],
   ["destination", "Salgo para Madrid.", "Parto per Madrid."],
   ["deadline", "Para mañana.", "Per domani."],
   ["employer", "Trabajo para un banco.", "Lavoro per una banca."],
   ["in someone's view", "Para mí, está bien.", "Per me, va bene."],
  ],
 },
 {
  "prep": "desde",
  "gloss": "from a point in time or space, onwards",
  "italian": "da, in its other sense",
  "uses": [
   ["since", "Desde ayer.", "Da ieri."],
   ["from a place", "Desde aquí se ve el mar.", "Da qui si vede il mare."],
   ["paired with hasta", "Desde las dos hasta las cinco.", "Dalle due alle cinque."],
  ],
 },
 {
  "prep": "con",
  "gloss": "accompaniment and instrument",
  "italian": "con, one for one",
  "uses": [
   ["with someone", "Voy con Ana.", "Vado con Ana."],
   ["with me", "Ven conmigo.", "Vieni con me.", "Spanish fuses it: conmigo, contigo, consigo"],
   ["instrument", "Escribo con lápiz.", "Scrivo con la matita."],
   ["dreaming of", "Sueño con salir.", "Sogno di partire.", "sognare di becomes soñar con"],
  ],
 },
 {
  "prep": "sobre",
  "gloss": "on top of, and about",
  "italian": "su and sopra",
  "uses": [
   ["on top of", "El libro está sobre la mesa.", "Il libro è sul tavolo."],
   ["about", "Un libro sobre México.", "Un libro sul Messico."],
   ["approximately", "Sobre las diez.", "Verso le dieci.", "Italian uses verso here"],
  ],
 },
 {
  "prep": "entre",
  "gloss": "between and among",
  "italian": "tra and fra",
  "uses": [
   ["between two", "Entre tú y yo.", "Tra me e te.", "Spanish keeps subject pronouns here"],
   ["among", "Entre los libros.", "Tra i libri."],
  ],
 },
 {
  "prep": "hasta",
  "gloss": "up to, until",
  "italian": "fino a",
  "uses": [
   ["until a time", "Hasta las cinco.", "Fino alle cinque."],
   ["as far as", "Hasta la esquina.", "Fino all'angolo."],
   ["even", "Hasta yo lo sé.", "Perfino io lo so."],
  ],
 },
 {
  "prep": "hacia",
  "gloss": "towards",
  "italian": "verso",
  "uses": [
   ["direction", "Camina hacia el río.", "Cammina verso il fiume."],
  ],
 },
 {
  "prep": "sin",
  "gloss": "without",
  "italian": "senza",
  "uses": [
   ["without a thing", "Café sin azúcar.", "Caffè senza zucchero."],
   ["without doing", "Se fue sin decir nada.", "È andato via senza dire niente."],
  ],
 },
 {
  "prep": "según",
  "gloss": "according to",
  "italian": "secondo",
  "uses": [
   ["according to", "Según Ana.", "Secondo Ana."],
  ],
 },
]

# The four Italian prepositions that cause the trouble, and where each one goes.
ITALIAN = [
 {
  "prep": "da",
  "warning": "The worst of them. Italian da does four separate jobs and Spanish "
             "uses a different word for each.",
  "splits": [
   ["coming from", "de", "Vengo da Roma.", "Vengo de Roma."],
   ["from a time onwards", "desde", "Da ieri.", "Desde ayer."],
   ["at someone's place", "en casa de", "Sono da Mario.", "Estoy en casa de Mario."],
   ["to someone's place", "a casa de", "Vado da Mario.", "Voy a casa de Mario."],
   ["by, in a passive", "por", "Scritto da Ana.", "Escrito por Ana."],
  ],
 },
 {
  "prep": "per",
  "warning": "Splits in two, and the choice is obligatory. para looks forwards "
             "to a purpose or destination; por looks back at a cause or through "
             "a space.",
  "splits": [
   ["purpose", "para", "Per imparare.", "Para aprender."],
   ["recipient", "para", "È per te.", "Es para ti."],
   ["destination", "para", "Parto per Madrid.", "Salgo para Madrid."],
   ["cause", "por", "Grazie per tutto.", "Gracias por todo."],
   ["exchange", "por", "Per dieci euro.", "Por diez euros."],
   ["duration", "por", "Per due ore.", "Por dos horas."],
   ["through", "por", "Per il parco.", "Por el parque."],
  ],
 },
 {
  "prep": "a",
  "warning": "Fine for movement and time. The trap is location: Italian says "
             "a Roma, Spanish says en Roma.",
  "splits": [
   ["movement", "a", "Vado a Madrid.", "Voy a Madrid."],
   ["being in a city", "en", "Sono a Roma.", "Estoy en Roma."],
   ["at home", "en", "Sono a casa.", "Estoy en casa."],
   ["clock time", "a", "Alle tre.", "A las tres."],
   ["thinking about", "en", "Penso a te.", "Pienso en ti."],
  ],
 },
 {
  "prep": "in",
  "warning": "Becomes en for location and a for movement — the opposite of what "
             "the spelling suggests.",
  "splits": [
   ["being in a country", "en", "Sono in Italia.", "Estoy en Italia."],
   ["going to a country", "a", "Vado in Italia.", "Voy a Italia."],
   ["transport", "en", "In treno.", "En tren."],
   ["season", "en", "In estate.", "En verano."],
  ],
 },
]
