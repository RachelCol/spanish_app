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

// macOS ships a pile of novelty voices (Grandma, Rocko, Bubbles) that sort
// ahead of the good ones. Prefer the standard voices by name, then fall back
// to whatever matches the language.
const PREFERRED = ['Paulina', 'Mónica', 'Monica', 'Alice', 'Luciana', 'Juan', 'Diego'];

let voices = [];
let ready = false;

export function initVoices() {
  const load = () => { voices = speechSynthesis.getVoices(); ready = voices.length > 0; };
  load();
  if (!ready && 'onvoiceschanged' in speechSynthesis) {
    speechSynthesis.addEventListener('voiceschanged', load);
  }
}

export function available() {
  return typeof speechSynthesis !== 'undefined';
}

function pickVoice(lang) {
  const want = lang.slice(0, 2);
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
