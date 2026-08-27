// Verb conjugation drills, and the Italian/Spanish preposition drill.
//
// Typed answers rather than self-grading. A conjugation either is or is not
// the form, so there is a right answer to check against -- and typing it is
// production practice, which recognising it is not.
//
// Deliberately separate from the flashcard scheduler. These are practice runs
// with a score, not scheduled reviews, and giving them their own state keeps
// them from disturbing anything the cards depend on.

import { speak, available as canSpeak } from './speech.js';

export const DRILL_TENSES = [
  { key: 'present',       label: 'Present' },
  { key: 'imperfect',     label: 'Imperfect' },
  { key: 'preterite',     label: 'Preterite' },
  { key: 'perfect',       label: 'Present perfect' },
  { key: 'future',        label: 'Future' },
  { key: 'conditional',   label: 'Conditional' },
  { key: 'subjPresent',   label: 'Present subjunctive' },
  { key: 'subjImperfect', label: 'Imperfect subjunctive' },
];

let verbCache = null;

export async function loadDrillVerbs() {
  if (verbCache) return verbCache;
  const res = await fetch('data/drill_verbs.json');
  verbCache = res.ok ? await res.json() : [];
  return verbCache;
}

// Accents are part of the answer, but a missing one is a typo rather than a
// wrong conjugation, so it is accepted and pointed out.
const DEACCENT = { 'á':'a','é':'e','í':'i','ó':'o','ú':'u','ü':'u' };

function normalise(s) {
  return s.trim().toLowerCase().replace(/[áéíóúü]/g, c => DEACCENT[c]);
}

export function checkAnswer(given, expected) {
  const g = given.trim().toLowerCase();
  const e = expected.toLowerCase();
  if (g === e) return 'right';
  if (normalise(given) === normalise(expected)) return 'accents';
  return 'wrong';
}

// One question per verb, tense and person. Shuffled, then capped.
export function buildVerbQuestions(conjugations, verbs, tenses, pronouns, limit) {
  const out = [];
  for (const verb of verbs) {
    const entry = conjugations.verbs[verb];
    if (!entry) continue;
    for (const tense of tenses) {
      const forms = entry[tense];
      if (!forms) continue;
      forms.forEach((form, i) => {
        out.push({ verb, tense, person: pronouns[i] || '', answer: form });
      });
    }
  }
  return shuffle(out).slice(0, limit);
}

function shuffle(a) {
  const out = a.slice();
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

export function speakerButton(text, which) {
  if (!canSpeak()) return null;
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'say';
  b.textContent = '▶';
  b.setAttribute('aria-label', 'Hear ' + text);
  b.addEventListener('click', e => { e.preventDefault(); speak(text, which); });
  return b;
}
