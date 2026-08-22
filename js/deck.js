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

export const TIER_ORDER = ['common', 'useful', 'extended', 'long_tail'];

// Apertium's tags, grouped the way a learner thinks about them. vbmod is a
// single modal verb, which does not deserve a category of its own.
export const POS_LABEL = {
  n: 'Nouns',
  vblex: 'Verbs',
  adj: 'Adjectives',
  adv: 'Adverbs',
  pr: 'Prepositions',
  cnj: 'Conjunctions',
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

export function itemKey(cardId, direction) {
  return direction + '|' + cardId;
}

// Combine the static deck with stored progress into the full item list.
export function buildItems(deck, progressList, settings) {
  const stored = new Map(progressList.map(p => [p.key, p]));
  const items = [];
  for (const card of deck) {
    if (!settings.tiers.includes(card.tier)) continue;
    if (!settings.buckets.includes(card.bucket)) continue;
    if (!settings.pos.includes(posGroup(card.pos))) continue;
    for (const dir of settings.directions) {
      const key = itemKey(card.id, dir);
      const item = stored.get(key) || newItem(key, card.id, dir, card.bucket);
      items.push({ ...item, card });
    }
  }
  return items;
}

export const DEFAULT_SETTINGS = {
  tiers: ['common', 'useful'],
  buckets: ['near', 'shifted', 'distinct'],   // `identical` off by default: little to learn
  pos: ['n', 'vblex', 'adj', 'adv', 'pr', 'cnj'],
  directions: ['es>it', 'it>es'],
  autoSpeak: true,
  accent: 'es-MX',   // locale, not a voice name -- see speech.js
  sessionSize: 15,   // cards per sitting; the daily plan is separate
  grades: [],        // empty = the normal mixed queue, not a grade drill
  newOnly: false,
};

export const SESSION_SIZES = [5, 10, 15, 20, 30, 40, 60];
