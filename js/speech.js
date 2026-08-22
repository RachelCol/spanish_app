// Pronunciation via the platform speech synthesiser.
//
// No audio files and no network: macOS and iOS both ship offline Spanish and
// Italian voices, so this keeps working on a plane alongside the rest of the
// app.
//
// What the user picks is an ACCENT, not a voice. Voice names differ between a
// Mac and a phone -- and change when better ones are installed -- so storing
// `es-MX` and resolving the best available voice for it each time survives
// moving between devices, which storing "Paulina" does not.
//
// iOS will not speak unless the first utterance originates in a user gesture.
// Everything here is triggered from a tap or a keypress for that reason.

export const ACCENTS = [
  { locale: 'es-MX', label: 'Latin America' },
  { locale: 'es-ES', label: 'Spain' },
];

export const SAMPLE = {
  es: 'La ciudad de Zaragoza.',
  it: 'Buongiorno, come stai?',
};

// Novelty voices are fine for a laugh and useless as a pronunciation model.
const NOVELTY = ['Eddy', 'Flo', 'Grandma', 'Grandpa', 'Reed', 'Rocko', 'Sandy',
                 'Shelley', 'Bubbles', 'Jester', 'Superstar', 'Wobble', 'Bells'];

// Apple ships the same voice at several qualities. Higher is better.
const QUALITY = [
  [/premium/i, 3],
  [/enhanced/i, 2],
  [/siri/i, 2],
];

const NAMED = ['Paulina', 'Mónica', 'Monica', 'Alice', 'Luciana', 'Juan', 'Diego'];

let voices = [];
let ready = false;
let accent = 'es-MX';
const listeners = [];

export function available() {
  return typeof speechSynthesis !== 'undefined';
}

export function initVoices() {
  const load = () => {
    voices = dedupe(speechSynthesis.getVoices());
    ready = voices.length > 0;
    if (ready) listeners.splice(0).forEach(fn => fn());
  };
  load();
  if ('onvoiceschanged' in speechSynthesis) {
    speechSynthesis.addEventListener('voiceschanged', load);
  }
}

export function onVoicesReady(fn) {
  if (ready) fn(); else listeners.push(fn);
}

// Some platforms hand back the same entry more than once, sometimes with a
// different voiceURI on each copy -- so the name and locale are the identity
// that actually holds.
function dedupe(list) {
  const seen = new Set();
  return list.filter(v => {
    const id = v.name + '|' + v.lang.toLowerCase().replace('_', '-');
    if (seen.has(id)) return false;
    seen.add(id);
    return true;
  });
}

function isNovelty(v) {
  return NOVELTY.some(n => v.name.includes(n));
}

function score(v) {
  let s = 0;
  for (const [re, points] of QUALITY) if (re.test(v.name)) s = Math.max(s, points);
  if (NAMED.some(n => v.name.includes(n))) s += 1;
  if (v.localService) s += 0.5;    // offline beats network for a plane
  return s;
}

// The best installed voice for a locale, or the closest language match.
export function bestVoice(locale) {
  const want = locale.toLowerCase();
  const lang = want.slice(0, 2);
  const usable = voices.filter(v => !isNovelty(v));
  const norm = v => v.lang.toLowerCase().replace('_', '-');
  const pool = usable.filter(v => norm(v) === want);
  const fallback = usable.filter(v => norm(v).startsWith(lang));
  const chosen = (pool.length ? pool : fallback).sort((a, b) => score(b) - score(a));
  return chosen[0] || null;
}

export function describeVoice(locale) {
  const v = bestVoice(locale);
  if (!v) return null;
  const m = v.name.match(/^(.*?)\s*\((.*)\)\s*$/);
  return m ? { name: m[1], quality: m[2] } : { name: v.name, quality: '' };
}

export function setAccent(locale) {
  if (locale) accent = locale;
}

export function getAccent() {
  return accent;
}

export function hasAccentPair() {
  return Boolean(bestVoice('es-MX') && bestVoice('es-ES'));
}

function utter(text, voice, lang, rate) {
  return new Promise(resolve => {
    const u = new SpeechSynthesisUtterance(text);
    if (voice) u.voice = voice;
    u.lang = voice ? voice.lang : lang;
    u.rate = rate;
    u.onend = resolve;
    u.onerror = resolve;      // never leave a chain hanging
    speechSynthesis.speak(u);
  });
}

function localeFor(which) {
  return which === 'it' ? 'it-IT' : accent;
}

export function speak(text, which, { rate = 0.9 } = {}) {
  if (!available() || !text) return Promise.resolve();
  speechSynthesis.cancel();
  const locale = localeFor(which);
  return utter(text, bestVoice(locale), locale, rate);
}

// Plays two words in order. The caller decides the order, because it follows
// the direction of the card: the side being read leads, and the side being
// recalled answers it.
export async function speakPair(first, firstWhich, second, secondWhich) {
  if (!available()) return;
  speechSynthesis.cancel();
  const fl = localeFor(firstWhich), sl = localeFor(secondWhich);
  await utter(first, bestVoice(fl), fl, 0.85);
  await new Promise(r => setTimeout(r, 320));
  await utter(second, bestVoice(sl), sl, 0.85);
}

// The Spain/Latin America split comes down to one rule: c before e or i, and
// z, are [s] across Latin America and unvoiced th across most of Spain. Four
// words in five are unaffected, so this is only offered where it applies.
const SESEO = /(c[ei]|z)/i;

export function differsByAccent(word) {
  return SESEO.test(word);
}

// The accent being learned is already what cards speak, so the useful offer is
// the other one on its own -- playing both would just repeat what was heard a
// second earlier.
export function otherAccent() {
  return ACCENTS.find(a => a.locale !== accent) || null;
}

export function speakOtherAccent(word) {
  const other = otherAccent();
  if (!other) return Promise.resolve();
  const v = bestVoice(other.locale);
  if (!v) return Promise.resolve();
  speechSynthesis.cancel();
  return utter(word, v, other.locale, 0.8);
}

export function stop() {
  if (available()) speechSynthesis.cancel();
}
