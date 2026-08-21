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

let deckCache = null;

export async function loadDeck() {
  if (deckCache) return deckCache;
  const res = await fetch('data/deck.json');
  if (!res.ok) throw new Error('could not load deck: ' + res.status);
  deckCache = await res.json();
  return deckCache;
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
  directions: ['es>it', 'it>es'],
  autoSpeak: true,
  voiceEs: null,   // voice name; null = pick a sensible default
  voiceIt: null,
  newPerDay: 15,
  maxSession: 60,
};
