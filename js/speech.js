// Pronunciation via the built-in speech synthesiser.
//
// No audio files and no network: macOS and iOS both ship offline Spanish and
// Italian voices, so this keeps working on a plane alongside the rest of the
// app. Voice quality varies by platform and there is nothing to be done about
// that, but es-MX and it-IT are reliably present on Apple devices.
//
// iOS will not speak unless the first utterance originates in a user gesture.
// Everything here is triggered from a tap or a keypress for that reason -- do
// not move autoSpeak onto a timer or it will silently do nothing on a phone.

const LANG = { es: 'es-MX', it: 'it-IT' };

// Sample lines for previewing a voice. The Spanish one is chosen to expose the
// single clearest accent tell: `ciudad` and `Zaragoza` are [s] in Latin
// America and [θ] in most of Spain.
export const SAMPLE = {
  es: 'La ciudad de Zaragoza.',
  it: 'Buongiorno, come stai?',
};

// macOS and iOS ship a set of novelty voices that are fine for a laugh and bad
// for learning pronunciation. They still get listed -- just not first.
const NOVELTY = ['Eddy', 'Flo', 'Grandma', 'Grandpa', 'Reed', 'Rocko', 'Sandy',
                 'Shelley', 'Bubbles', 'Jester', 'Superstar', 'Wobble', 'Bells'];

const chosen = { es: null, it: null };

// macOS ships a pile of novelty voices (Grandma, Rocko, Bubbles) that sort
// ahead of the good ones. Prefer the standard voices by name, then fall back
// to whatever matches the language.
const PREFERRED = ['Paulina', 'Mónica', 'Monica', 'Alice', 'Luciana', 'Juan', 'Diego'];

let voices = [];
let ready = false;

const listeners = [];

export function initVoices() {
  const load = () => {
    voices = speechSynthesis.getVoices();
    ready = voices.length > 0;
    if (ready) listeners.splice(0).forEach(fn => fn());
  };
  load();
  if ('onvoiceschanged' in speechSynthesis) {
    speechSynthesis.addEventListener('voiceschanged', load);
  }
}

// The voice list arrives asynchronously on most browsers, so anything that
// renders it has to wait rather than read an empty array once.
export function onVoicesReady(fn) {
  if (ready) fn(); else listeners.push(fn);
}

export function isNovelty(voice) {
  return NOVELTY.some(n => voice.name.includes(n));
}

// Grouped by locale, because the Spain/Latin America split is the distinction
// that matters here. Better voices sort first inside each group.
export function listVoices(which) {
  const want = which === 'es' ? 'es' : 'it';
  const matches = voices.filter(v => v.lang.toLowerCase().replace('_', '-').startsWith(want));
  const groups = new Map();
  for (const v of matches) {
    const lang = v.lang.replace('_', '-');
    if (!groups.has(lang)) groups.set(lang, []);
    groups.get(lang).push(v);
  }
  for (const list of groups.values()) {
    list.sort((a, b) => (isNovelty(a) - isNovelty(b)) || a.name.localeCompare(b.name));
  }
  // Latin American locales ahead of Spain, matching what this deck teaches.
  const order = which === 'es' ? ['es-MX', 'es-US', 'es-419', 'es-AR', 'es-CO', 'es-CL', 'es-ES'] : ['it-IT'];
  return [...groups.entries()].sort((a, b) => {
    const ia = order.indexOf(a[0]), ib = order.indexOf(b[0]);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
  });
}

export function setVoice(which, name) {
  chosen[which] = name || null;
}

export function getVoice(which) {
  return chosen[which];
}

export function available() {
  return typeof speechSynthesis !== 'undefined';
}

function pickVoice(lang) {
  const want = lang.slice(0, 2);
  // An explicit choice wins, but only while that voice still exists -- the
  // list differs between a Mac and a phone, so a stored name can go stale.
  const override = chosen[want];
  if (override) {
    const hit = voices.find(v => v.name === override);
    if (hit) return hit;
  }
  const matches = voices.filter(v => v.lang.toLowerCase().replace('_', '-').startsWith(want));
  if (!matches.length) return null;
  const exact = matches.filter(v => v.lang.toLowerCase().replace('_', '-') === lang.toLowerCase());
  const pool = exact.length ? exact : matches;
  for (const name of PREFERRED) {
    const hit = pool.find(v => v.name.includes(name));
    if (hit) return hit;
  }
  return pool.find(v => v.localService) || pool[0];
}

// Resolves when the utterance finishes, so callers can chain two languages.
function utter(text, lang, rate) {
  return new Promise(resolve => {
    const u = new SpeechSynthesisUtterance(text);
    u.lang = lang;
    u.rate = rate;
    const v = pickVoice(lang);
    if (v) u.voice = v;
    u.onend = resolve;
    u.onerror = resolve;   // never leave a chain hanging
    speechSynthesis.speak(u);
  });
}

export function speak(text, which, { rate = 0.9 } = {}) {
  if (!available() || !text) return Promise.resolve();
  speechSynthesis.cancel();
  return utter(text, LANG[which] || which, rate);
}

// Italian first, then Spanish, with a beat between them. The order matters:
// the familiar word sets up the ear for what changed in the unfamiliar one.
export async function compare(it, es) {
  if (!available()) return;
  speechSynthesis.cancel();
  await utter(it, LANG.it, 0.85);
  await new Promise(r => setTimeout(r, 320));
  await utter(es, LANG.es, 0.85);
}

export function stop() {
  if (available()) speechSynthesis.cancel();
}
