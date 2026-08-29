// Deck loading and item construction.
//
// A "card" is a word pair. An "item" is one direction of one card, and it is
// the unit the scheduler tracks. es>it and it>es are genuinely different
// skills -- reading Spanish and recalling the Italian is recognition, while
// going the other way is production and much harder -- so giving them one
// shared schedule would let the easy direction hide the hard one.

import { newItem } from './srs.js';

export const DIRECTIONS = {
  'es>it': { prompt: 'es', answer: 'it', label: 'Spanish → Italian', kind: 'recognition' },
  'it>es': { prompt: 'it', answer: 'es', label: 'Italian → Spanish', kind: 'production' },
};

export const BUCKET_LABEL = {
  identical: 'identical in both',
  near: 'almost the same',
  shifted: 'similar but shifted',
  distinct: 'completely different',
};

// `core` was missing here, which meant the twenty-two most frequent words in
// the language -- ser, así, no, más, hacer, nada, vez -- had no filter chip,
// were absent from the defaults and were not even in the "Everything" scope.
// They were unreachable.
// The bands content/lexicon.csv actually writes, most frequent first. These
// drifted: the list still named `extended` and `long_tail`, which no longer
// exist, and omitted `first` -- so the 300 commonest Spanish words could not
// be switched on from Settings at all, because they were never a chip.
export const TIER_ORDER = ['first', 'core', 'common', 'useful', 'wider'];

// Apertium's tags, grouped the way a learner thinks about them. vbmod is a
// single modal verb, which does not deserve a category of its own.
// Abbreviations for the marker on the face of a card, where even a short word
// would crowd out the word being learned. The word list wants its own, longer
// set -- see POS_SHORT in main.js.
export const POS_ABBR = {
  n: 'n.', vblex: 'v.', adj: 'adj.', adv: 'adv.', pr: 'prep.',
  prn: 'pron.', cnj: 'conj.', det: 'det.', ij: 'interj.', num: 'num.',
};

export const POS_LABEL = {
  n: 'Nouns',
  vblex: 'Verbs',
  adj: 'Adjectives',
  adv: 'Adverbs',
  pr: 'Prepositions',
  prn: 'Pronouns',
  cnj: 'Conjunctions',
  det: 'Determiners',
  ij: 'Expressions',
  num: 'Numbers',
  phrase: 'Phrases',
};

// Apertium distinguishes more verb and conjunction types than a learner cares
// about. Collapse them onto the categories people actually think in.
const POS_GROUPS = {
  vblex: 'vblex', vbmod: 'vblex', vbhaver: 'vblex', vbser: 'vblex',
  adv: 'adv', preadv: 'adv',
  cnjcoo: 'cnj', cnjsub: 'cnj', cnjadv: 'cnj',
};

export function posGroup(pos) {
  return POS_GROUPS[pos] || pos;
}

// A word is often several things at once -- `bajo` is an adjective and a
// preposition, `ver` a verb and a noun -- so filtering on a single tag loses
// it from every category but one.
export function posGroups(card) {
  const tags = card.pos_all && card.pos_all.length ? card.pos_all : [card.pos];
  return [...new Set(tags.map(posGroup))];
}

let deckCache = null;

export async function loadDeck() {
  if (deckCache) return deckCache;
  const res = await fetch('data/deck.json');
  if (!res.ok) throw new Error('could not load deck: ' + res.status);
  deckCache = await res.json();
  return deckCache;
}

// 365 KB of example sentences, fetched the first time they are asked for
// rather than on boot. The service worker precaches the file, so this still
// resolves offline.
let sentenceCache = null;

export async function loadSentences() {
  if (sentenceCache) return sentenceCache;
  const res = await fetch('data/sentences.json');
  sentenceCache = res.ok ? await res.json() : {};
  return sentenceCache;
}

// Gender for nouns, read off corpus usage. Lazily fetched: it is only needed
// once a noun card is turned over.
let genderCache = null;

export async function loadGender() {
  if (genderCache) return genderCache;
  const res = await fetch('data/gender.json');
  genderCache = res.ok ? await res.json() : {};
  return genderCache;
}

// Italian prompts that answer more than one Spanish card. Small, and needed
// the moment an Italian->Spanish card flips, so it loads with the gender file.
// Every Italian prompt and the Spanish words that answer it. This is what the
// deck is now driven from: a prompt is an Italian word, not a card read
// backwards, so `poi` can ask for `luego` even though `luego`'s own card
// glosses it as `dopo`.
let promptCache = null;

export async function loadPrompts() {
  if (promptCache) return promptCache;
  const res = await fetch('data/prompts.json');
  if (!res.ok) throw new Error('could not load prompts: ' + res.status);
  promptCache = await res.json();
  return promptCache;
}

let conjCache = null;

export async function loadConjugations() {
  if (conjCache) return conjCache;
  const res = await fetch('data/conjugations.json');
  conjCache = res.ok ? await res.json() : {};
  return conjCache;
}

export function itemKey(cardId, direction) {
  return direction + '|' + cardId;
}

// Combine the static deck with stored progress into the full item list.
// One scheduled item per Italian prompt, in the production direction only.
//
// Spanish -> Italian is no longer a review: it survives as the detail view
// behind each Spanish answer, which is the same information doing a more
// useful job. Recognition is the half already known.
export function buildItems(deck, prompts, progressList, settings) {
  const byId = new Map(deck.map(c => [c.id, c]));
  const stored = new Map(progressList.map(p => [p.key, p]));
  const passes = card => card
    && settings.tiers.includes(card.tier)
    && settings.buckets.includes(card.bucket)
    && posGroups(card).some(g => settings.pos.includes(g));

  const items = [];
  for (const [prompt, all] of Object.entries(prompts)) {
    // The prompt belongs to its best answer, and is only asked where that
    // answer is in scope. Keeping a prompt because some *other* answer
    // survived the filter is how `fare` came to mean `desayunar` in the wider
    // deck: `hacer` is a first-band word, so it was filtered out and the
    // leftovers were shown as though they were the meaning.
    if (!passes(byId.get(all[0].es))) continue;
    const answers = all.filter(a => passes(byId.get(a.es)));
    if (!answers.length) continue;
    const lead = byId.get(answers[0].es);
    const key = itemKey(prompt, 'it>es');
    const item = stored.get(key) || newItem(key, prompt, 'it>es', lead.bucket);
    items.push({ ...item, card: lead, prompt, answers });
  }
  return items;
}

export const DEFAULT_SETTINGS = {
  tiers: ['first', 'core', 'common', 'useful'],   // `wider` off: the long tail
  buckets: ['near', 'shifted', 'distinct'],   // `identical` off by default: little to learn
  pos: ['n', 'vblex', 'adj', 'adv', 'pr', 'prn', 'cnj', 'det', 'ij', 'num', 'phrase'],
  directions: ['it>es'],
  autoSpeak: true,
  accent: 'es-MX',   // locale, not a voice name -- see speech.js
  sessionSize: 15,   // cards per sitting; the daily plan is separate
  grades: [],        // empty = the normal mixed queue, not a grade drill
  newOnly: false,
};

export const SESSION_SIZES = [5, 10, 15, 20, 30, 40, 60];
