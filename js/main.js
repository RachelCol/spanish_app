import { db, requestPersistence } from './db.js';
import { grade, intervalLabel, gradeLetter, gradeRange, GRADES, isNew as isNewItem,
         AGAIN, HARD, GOOD, EASY } from './srs.js';
import { loadDeck, loadSentences, loadConjugations, loadGender, buildItems, DIRECTIONS, BUCKET_LABEL, TIER_ORDER,
         POS_LABEL, posGroup, posGroups, DEFAULT_SETTINGS, SESSION_SIZES } from './deck.js';
import { buildQueue, counts, gradeBreakdown } from './session.js';
import { initSections } from './sections.js';
import { initVoices, onVoicesReady, setAccent, ACCENTS, describeVoice, SAMPLE, speakSteps,
         differsByAccent, hasAccentPair, speakOtherAccent, otherAccent,
         available as canSpeak, speak, speakSequence, stop as stopSpeech } from './speech.js';

const $ = sel => document.querySelector(sel);

const state = {
  deck: [],
  gender: {},
  items: [],
  settings: { ...DEFAULT_SETTINGS },
  queue: [],
  reviewsToday: 0,
  index: 0,
  revealed: false,
  graded: 0,
};

// ---------- boot ----------

const DAY = 86400000;
const DIRECTIONS_COUNT = Object.keys(DIRECTIONS).length;
const BACKUP_NAG_DAYS = 14;

function fatal(msg) {
  const el = document.querySelector('#fatal');
  el.textContent = msg;
  el.classList.remove('hidden');
  document.querySelector('#view-home').classList.add('hidden');
}

async function boot() {
  try {
    await start();
  } catch (err) {
    // A blocked upgrade never settles on its own, so it has to be reported
    // rather than left as a blank screen.
    fatal(err && err.message === 'DB_BLOCKED'
      ? 'This app is open in another tab or window running an older version. '
        + 'Close the others, then reload this page.'
      : 'Could not start: ' + (err && err.message ? err.message : err));
    throw err;
  }
}

async function start() {
  state.deck = await loadDeck();
  const saved = await db.getMeta('settings');
  if (saved) state.settings = { ...DEFAULT_SETTINGS, ...saved };
  await refresh();
  renderFilters();
  wire();
  // The grammar, drill and conversation sections are additive: they share the
  // view switcher and the conjugation tables and touch nothing else.
  loadConjugations()
    .then(conj => initSections(show, conj))
    .catch(() => {});

  loadGender().then(g => { state.gender = g; }).catch(() => {});

  initVoices();
  onVoicesReady(() => {
    setAccent(state.settings.accent);
    renderVoicePickers();
  });
  requestPersistence();
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
}

// Local midnight, not UTC -- a review at 11pm belongs to that evening.
function startOfToday() {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  return d.getTime();
}

async function refresh() {
  const [progress, today, lastBackup] = await Promise.all([
    db.allProgress(),
    db.reviewsSince(startOfToday()),
    db.getMeta('lastBackup'),
  ]);
  state.items = buildItems(state.deck, progress, state.settings);
  state.reviewsToday = today.length;

  const c = counts(state.items);
  $('#c-due').textContent = c.due;
  $('#c-new').textContent = c.new;
  $('#c-learned').textContent = c.learned;
  $('#reviews-today').textContent = state.reviewsToday;

  renderBackupState(lastBackup, c.learned);

  // Three different empty states that used to look identical. Filtering every
  // card out is a mistake to be told about, not a quiet "come back tomorrow".
  const queued = buildQueue(state.items, state.settings).length;
  $('#start').classList.toggle('hidden', queued === 0);
  $('#nothing-due').classList.toggle('hidden', queued !== 0);
  if (queued === 0) {
    $('#nothing-due').textContent = state.items.length === 0
      ? 'No cards match your Deck filters. Turn a frequency band, closeness or direction back on.'
      : state.settings.grades.length
        ? 'No cards in that grade yet. Clear the grade drill under Deck.'
        : 'Nothing due right now. Widen the filters under Deck to add more.';
  }
}

// ---------- filters ----------

function chip(label, sub, on, fn) {
  const b = document.createElement('button');
  b.className = 'chip';
  b.type = 'button';
  b.setAttribute('aria-pressed', String(on));
  b.innerHTML = sub ? `${label}<small>${sub}</small>` : label;
  b.addEventListener('click', async () => {
    const next = b.getAttribute('aria-pressed') !== 'true';
    b.setAttribute('aria-pressed', String(next));
    fn(next);
    await save();
  });
  return b;
}

function renderFilters() {
  const s = state.settings;
  const countBy = (field, val) => state.deck.filter(c => c[field] === val).length;

  const tiers = $('#f-tiers');
  tiers.replaceChildren(...TIER_ORDER.map(t =>
    chip(t.replace('_', ' '), countBy('tier', t), s.tiers.includes(t), on => toggle(s.tiers, t, on))));

  const buckets = $('#f-buckets');
  buckets.replaceChildren(...Object.keys(BUCKET_LABEL).map(b =>
    chip(BUCKET_LABEL[b], countBy('bucket', b), s.buckets.includes(b), on => toggle(s.buckets, b, on))));

  const pos = $('#f-pos');
  pos.replaceChildren(...Object.keys(POS_LABEL).map(p =>
    chip(POS_LABEL[p], state.deck.filter(c => posGroups(c).includes(p)).length,
         s.pos.includes(p), on => toggle(s.pos, p, on))));

  const dirs = $('#f-directions');
  dirs.replaceChildren(...Object.keys(DIRECTIONS).map(d =>
    chip(DIRECTIONS[d].label, DIRECTIONS[d].kind, s.directions.includes(d), on => toggle(s.directions, d, on))));

  const speech = $('#f-speech');
  if (canSpeak()) {
    speech.replaceChildren(chip('Say the Spanish on reveal', '', s.autoSpeak,
      on => { s.autoSpeak = on; }));
  } else {
    speech.textContent = 'This browser has no speech support.';
    speech.className = 'muted small';
  }

  const grades = $('#f-grades');
  grades.replaceChildren(...GRADES.map(g =>
    chip(g, gradeRange(g), s.grades.includes(g), on => toggle(s.grades, g, on))),
    chip('New', 'never seen', s.newOnly, on => { s.newOnly = on; }));

  const size = $('#f-size');
  size.replaceChildren(...SESSION_SIZES.map(n => {
    const o = document.createElement('option');
    o.value = n; o.textContent = n + ' cards'; o.selected = s.sessionSize === n;
    return o;
  }));
}

function renderVoicePickers() {
  const host = $('#voice-rows');
  if (!canSpeak()) { host.replaceChildren(); return; }

  const box = document.createElement('fieldset');
  const legend = document.createElement('legend');
  legend.textContent = 'Spanish accent';
  box.append(legend);

  const row = document.createElement('div');
  row.className = 'chips';
  for (const { locale, label } of ACCENTS) {
    const v = describeVoice(locale);
    if (!v) continue;
    row.append(chipButton(
      label,
      v.quality ? `${v.name} · ${v.quality}` : v.name,
      state.settings.accent === locale,
      async () => {
        state.settings.accent = locale;
        setAccent(locale);
        await db.setMeta('settings', state.settings);
        renderVoicePickers();
        speak(SAMPLE.es, 'es');
      }));
  }
  box.append(row);

  const it = describeVoice('it-IT');
  const note = document.createElement('p');
  note.className = 'muted small voice-note';
  note.textContent = it
    ? `Italian uses ${it.name}${it.quality ? ' (' + it.quality + ')' : ''}.`
    : 'No Italian voice is installed.';
  const play = document.createElement('button');
  play.type = 'button';
  play.className = 'say';
  play.textContent = '▶';
  play.setAttribute('aria-label', 'Preview the Italian voice');
  play.addEventListener('click', e => { e.preventDefault(); speak(SAMPLE.it, 'it'); });
  note.append(' ');
  note.append(play);

  host.replaceChildren(box, note);
}

// Like chip(), but the handler owns the pressed state rather than toggling it.
function chipButton(label, sub, pressed, onClick) {
  const b = document.createElement('button');
  b.className = 'chip';
  b.type = 'button';
  b.setAttribute('aria-pressed', String(pressed));
  b.innerHTML = sub ? `${label}<small>${sub}</small>` : label;
  b.addEventListener('click', e => { e.preventDefault(); onClick(); });
  return b;
}

function toggle(arr, val, on) {
  const i = arr.indexOf(val);
  if (on && i === -1) arr.push(val);
  if (!on && i !== -1) arr.splice(i, 1);
}

async function save() {
  await db.setMeta('settings', state.settings);
  await refresh();
  // The list is a view of the filters, so it has to follow them.
  if ($('#word-list-panel').open) renderWordList();
}

// ---------- the word list ----------
//
// Everything the current filters admit, in the order the deck introduces it:
// most frequent first, which is the order it will actually reach you in.
//
// Built only when the panel is opened. The unfiltered deck is several thousand
// rows, and there is no reason to hold them all in the document until asked.

const POS_SHORT = {
  n: 'Noun', vblex: 'Verb', adj: 'Adj', adv: 'Adv',
  pr: 'Prep', prn: 'Pron', cnj: 'Conj',
};

let listPlaying = false;

function uniqueCards() {
  const seen = new Set();
  const out = [];
  for (const item of state.items) {
    if (seen.has(item.card.es)) continue;
    seen.add(item.card.es);
    out.push(item.card);
  }
  return out.sort((a, b) => b.zipf - a.zipf);
}

// "casa - la casa" for a single sense; "(Noun) partito, partita; (Adj)
// tagliato" where the senses split by part of speech.
function glossOf(card) {
  if (card.by_pos) {
    return Object.entries(card.by_pos)
      .map(([group, words]) =>
        `(${POS_SHORT[group] || group}) ${words.join(', ')}`)
      .join('; ');
  }
  return card.senses.join(', ');
}

function renderWordList() {
  const cards = uniqueCards();
  $('#word-list-count').textContent =
    `${cards.length} word${cards.length === 1 ? '' : 's'}`;

  $('#word-list').replaceChildren(...cards.map((card, i) => {
    const row = document.createElement('div');
    row.className = 'word-row-item';
    row.dataset.index = i;

    const es = document.createElement('b');
    es.className = 'word-es';
    es.textContent = card.es;

    const dash = document.createElement('span');
    dash.className = 'word-dash';
    dash.textContent = ' - ';

    const it = document.createElement('span');
    it.className = 'word-it';
    it.textContent = glossOf(card);

    row.append(es, dash, it);
    row.addEventListener('click', () => speak(card.es, 'es'));
    return row;
  }));
  return cards;
}

// The Spanish word, then each gloss, then a longer breath before the next
// entry. Multiword glosses like "davanti a" are read whole.
function listScript(cards) {
  const steps = [];
  cards.forEach((card, index) => {
    steps.push({ text: card.es, lang: 'es', index, gap: 260 });
    const senses = card.by_pos
      ? Object.values(card.by_pos).flat()
      : card.senses;
    senses.forEach((sense, k) => {
      steps.push({
        text: sense, lang: 'it', index,
        gap: k === senses.length - 1 ? 900 : 220,
      });
    });
  });
  return steps;
}

function setListButton(playing) {
  listPlaying = playing;
  const b = $('#word-list-play');
  b.textContent = playing ? '❚❚ Pause' : '▶ Read the list';
  b.classList.toggle('playing', playing);
}

function highlightListRow(index) {
  const list = $('#word-list');
  const previous = list.querySelector('.word-row-item.speaking');
  if (previous) previous.classList.remove('speaking');
  if (index === null || index === undefined) return;
  const row = list.querySelector(`.word-row-item[data-index="${index}"]`);
  if (row) {
    row.classList.add('speaking');
    row.scrollIntoView({ block: 'nearest' });
  }
}

async function toggleListPlayback() {
  if (listPlaying) {
    stopSpeech();
    setListButton(false);
    highlightListRow(null);
    return;
  }
  const cards = uniqueCards();
  if (!cards.length) return;
  setListButton(true);
  await speakSteps(listScript(cards), {
    onStep: index => {
      if (index === null) { setListButton(false); highlightListRow(null); }
      else highlightListRow(index);
    },
  });
}

// ---------- review ----------

function show(view) {
  ['home', 'review', 'done', 'progress', 'conj', 'deck', 'settings',
   'grammar', 'basics', 'drill', 'prep', 'articles'].forEach(v =>
    $('#view-' + v).classList.toggle('hidden', v !== view));
}

function startSession() {
  state.queue = buildQueue(state.items, state.settings);
  state.index = 0;
  state.graded = 0;
  if (!state.queue.length) return;
  show('review');
  renderCard();
}

function renderCard() {
  const item = state.queue[state.index];
  const dir = DIRECTIONS[item.direction];
  state.revealed = false;

  $('#direction').textContent = dir.label;
  const promptWord = item.card[dir.prompt];
  $('#prompt').replaceChildren(
    withGender(promptWord,
               genderFor(state.gender, item.card, promptWord, dir.prompt),
               dir.prompt));
  // Every part of speech the word has, not just the one that won the vote:
  // calling `bajo` an adjective and nothing else is a quiet lie.
  const posText = posGroups(item.card)
    .map(g => (POS_LABEL[g] || g).toLowerCase().replace(/s$/, ''))
    .join(' · ');
  $('#meta').innerHTML =
    `<span class="pos">${posText}</span> · ${BUCKET_LABEL[item.card.bucket]}`;

  stopSpeech();
  $('#answers').classList.add('hidden');
  $('#answers').classList.remove('grouped');
  $('#answers').replaceChildren();
  $('#meta').classList.add('hidden');
  $('#accent-note').classList.add('hidden');
  $('#card-links').classList.add('hidden');
  $('#examples-btn').classList.add('hidden');
  $('#conj-btn').classList.add('hidden');
  $('#present-table').classList.add('hidden');
  $('#present-table').replaceChildren();
  $('#examples').classList.add('hidden');
  $('#examples').replaceChildren();
  $('#say-prompt').classList.toggle('hidden', !canSpeak());
  $('#reveal-row').classList.remove('hidden');
  $('#grade-row').classList.add('hidden');

  $('#remaining').textContent = (state.queue.length - state.index) + ' left';
  $('#progress-fill').style.width = (100 * state.index / state.queue.length) + '%';
}

function reveal() {
  if (state.revealed) return;
  state.revealed = true;
  const item = state.queue[state.index];
  const card = item.card;
  const dir = DIRECTIONS[item.direction];

  // Going to Italian, show every sense: where a Spanish word does not map
  // one-to-one, that is the useful information and one gloss would hide it.
  // Where the senses split by part of speech -- bajo is basso as an adjective
  // and sotto as a preposition -- they are grouped under it, because a flat
  // list makes `sí` read as "sè · sì" with no hint that one means yes and the
  // other is a pronoun.
  const toItalian = dir.answer === 'it';
  const groups = toItalian && card.by_pos ? card.by_pos : null;

  const speakable = (w, which) => {
    const row = document.createElement('div');
    row.className = 'word-row';
    const span = document.createElement('span');
    span.className = 'answer';
    span.replaceChildren(withGender(w, genderFor(state.gender, card, w, which), which));
    row.append(span);
    if (canSpeak()) {
      const play = document.createElement('button');
      play.type = 'button';
      play.className = 'say';
      play.textContent = '▶';
      play.setAttribute('aria-label', 'Hear ' + w);
      play.addEventListener('click', e => { e.preventDefault(); speak(w, which); });
      row.append(play);
    }
    return row;
  };

  if (groups) {
    const blocks = [];
    for (const [g, words] of Object.entries(groups)) {
      const label = document.createElement('div');
      label.className = 'sense-pos';
      label.textContent = POS_LABEL[g] ? POS_LABEL[g].toLowerCase().replace(/s$/, '') : g;
      blocks.push(label, ...words.map(w => speakable(w, 'it')));
    }
    $('#answers').replaceChildren(...blocks);
    $('#answers').classList.add('grouped');
  } else {
    const words = toItalian ? (card.senses || [card.it]) : [card.es];
    $('#answers').replaceChildren(...words.map(w => speakable(w, dir.answer)));
    $('#answers').classList.remove('grouped');
  }
  $('#answers').classList.remove('hidden');
  $('#meta').classList.remove('hidden');

  // A footnote on the word rather than a headline action, and only on the
  // ~1 in 5 words the two accents actually pronounce differently.
  const other = otherAccent();
  const showAccent = canSpeak() && hasAccentPair() && other && differsByAccent(card.es);
  if (showAccent) $('#accent-text').textContent = other.label + ' pronunciation differs';
  $('#accent-note').classList.toggle('hidden', !showAccent);

  // Always look up the Spanish: it is the language being learned, and every
  // one of these three has a Spanish-Italian mode.
  const w = encodeURIComponent(card.es);
  $('#link-wr').href  = `https://www.wordreference.com/esit/${w}`;
  $('#link-rev').href = `https://context.reverso.net/translation/spanish-italian/${w}`;
  $('#link-yg').href  = `https://youglish.com/pronounce/${w}/spanish`;
  $('#card-links').classList.remove('hidden');

  if (posGroups(card).includes('vblex')) {
    loadConjugations().then(all => {
      if (!state.queue[state.index] || state.queue[state.index].card.es !== card.es) return;
      const entry = all.verbs[card.es];
      $('#conj-btn').classList.toggle('hidden', !entry);
      renderPresentTable(entry);
    });
  }

  loadSentences().then(all => {
    // The card may have moved on while the file was loading.
    if (state.queue[state.index] && state.queue[state.index].card.es === card.es) {
      $('#examples-btn').classList.toggle('hidden', !(all[card.es] || []).length);
    }
  });

  // Only the Spanish. With several Italian senses on screen, reading them all
  // aloud is noise -- and the Italian is the side already known. Each sense
  // has its own button for the pairs that sound nearly identical.
  if (state.settings.autoSpeak && canSpeak()) speak(card.es, 'es');
  $('#reveal-row').classList.add('hidden');
  $('#grade-row').classList.remove('hidden');

  // Show what each button costs before it is pressed.
  [AGAIN, HARD, GOOD, EASY].forEach(g => {
    $(`#grade-row button[data-g="${g}"] small`).textContent = intervalLabel(item, g);
  });
}

// Bold whatever in the sentence came from this word. A prefix match handles
// the regular cases -- `hermano` lighting up `hermanos` -- without needing a
// lemmatizer in the browser. It cannot handle irregular verbs, where no prefix
// of `ver` appears in `vemos` or `vio`, so for verbs the conjugation table is
// consulted as well; those forms are already on the device.
function verbForms(card, conj) {
  const entry = conj && conj.verbs && conj.verbs[card.es];
  if (!entry) return null;
  const out = new Set();
  // Every tense, so an example sentence lights up whichever form it used.
  //
  // Only string entries. The record also carries `marks`, which is an array of
  // character ranges rather than of forms, and treating it as forms threw --
  // taking the Examples panel down with it on every verb that had any.
  for (const value of Object.values(entry)) {
    if (!Array.isArray(value)) continue;
    for (const form of value) {
      if (typeof form !== 'string') continue;
      // "he visto" and "voy a ver" carry the meaning in their last word; the
      // auxiliary would light up half the sentences on the card.
      const parts = form.split(/\s+/);
      out.add(parts[parts.length - 1].toLowerCase());
    }
  }
  return out;
}

function highlight(sentence, lemma, forms) {
  const stem = lemma.slice(0, Math.max(4, lemma.length - 2)).toLowerCase();
  const frag = document.createDocumentFragment();
  for (const part of sentence.split(/(\s+)/)) {
    const bare = part.toLowerCase().replace(/[^a-záéíóúüñ]/gi, '');
    if ((forms && forms.has(bare)) || (bare.length >= stem.length && bare.startsWith(stem))) {
      const b = document.createElement('b');
      b.textContent = part;
      frag.append(b);
    } else {
      frag.append(part);
    }
  }
  return frag;
}

async function toggleExamples() {
  const panel = $('#examples');
  if (!panel.classList.contains('hidden')) {
    panel.classList.add('hidden');
    return;
  }
  const card = state.queue[state.index].card;
  const rows = (await loadSentences())[card.es] || [];
  const forms = posGroups(card).includes('vblex') ? verbForms(card, await loadConjugations()) : null;
  panel.replaceChildren(...rows.map(r => {
    const block = document.createElement('div');
    block.className = 'example';

    const es = document.createElement('p');
    es.className = 'example-es';
    es.append(highlight(r.es, card.es, forms));
    if (canSpeak()) {
      const play = document.createElement('button');
      play.type = 'button';
      play.className = 'say';
      play.textContent = '▶';
      play.setAttribute('aria-label', 'Hear this sentence');
      play.addEventListener('click', e => { e.preventDefault(); speak(r.es, 'es', { rate: 0.85 }); });
      es.append(' ');
      es.append(play);
    }

    const it = document.createElement('p');
    it.className = 'example-it';
    it.textContent = r.it;

    block.append(es, it);
    return block;
  }));
  panel.classList.remove('hidden');
}

async function applyGrade(g) {
  if (!state.revealed) return;
  const item = state.queue[state.index];
  const { card, ...bare } = item;
  const wasNew = bare.reps === 0;
  const next = grade(bare, g);
  await db.putProgress(next);

  // wasNew is what makes the daily new-card budget countable after the fact;
  // reps has already moved on by the time anything reads this back.
  await db.logReview({
    ts: Date.now(), key: bare.key, cardId: bare.cardId,
    direction: bare.direction, bucket: bare.bucket,
    grade: g, wasNew, interval: next.interval,
  });
  state.reviewsToday++;
  state.graded++;

  // A lapsed card comes back at the end of this session rather than vanishing
  // until tomorrow -- that is the point of pressing Again.
  if (g === AGAIN) state.queue.push({ ...next, card });

  state.index++;
  if (state.index >= state.queue.length) return finish();
  renderCard();
}

async function finish() {
  stopSpeech();
  await refresh();
  $('#done-summary').textContent =
    `${state.graded} card${state.graded === 1 ? '' : 's'} reviewed.`;
  show('done');
}

// A noun shown with the article a speaker would use, and its gender spelled
// out after it. Both, deliberately: the article is what you need in order to
// say the word, and the letter is what tells you the truth when the article
// lies -- `el agua` is feminine, and only the letter says so.
function withGender(word, info, lang) {
  const frag = document.createDocumentFragment();
  if (!info) {
    frag.append(word);
    return frag;
  }
  const article = document.createElement('span');
  // l' binds tight to its word; every other article stands off from it.
  const elided = info.art.endsWith("'");
  article.className = 'gender-article' + (elided ? ' elided' : '');
  article.textContent = info.art;
  frag.append(article, word);

  const mark = document.createElement('i');
  mark.className = 'gender-mark';
  mark.textContent = info.g;
  frag.append(mark);
  return frag;
}

function genderFor(all, card, word, which) {
  const entry = all && all[card.es];
  if (!entry) return null;
  if (which === 'es') return word === card.es ? entry : null;
  return (entry.it || {})[word] || null;
}

// A button that reads a whole paradigm aloud, first person singular through
// third person plural. Sequential, with a beat between forms.
function playAllButton(forms, label) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'play-all';
  b.textContent = '▶';
  b.setAttribute('aria-label', label);
  b.addEventListener('click', e => {
    e.preventDefault();
    speakSequence(forms, 'es');
  });
  return b;
}

// The present tense on the card itself, in two columns. It replaces the
// "e→ie" note that used to sit here: the note described the change in
// shorthand, the paradigm shows it.
//
// The underlines mark stem changes and nothing else. An earlier version
// compared whole conjugated forms, which also caught irregular endings and
// did so inconsistently: `está` and `están` differ from a regular esta/estan
// by an accent and were marked, while `estáis` matches the regular -áis and
// was not. estar's stem never changes, so it is now unmarked throughout.
function renderPresentTable(entry) {
  const host = $('#present-table');
  if (!entry || !entry.present) { host.classList.add('hidden'); return; }

  const forms = entry.present;
  const marks = entry.marks || [];

  const grid = document.createElement('div');
  grid.className = 'present-grid';
  grid.append(...forms.map((form, i) => {
    const cell = document.createElement('span');
    cell.className = 'present-form';

    const spans = marks[i] || [];
    let last = 0;
    for (const [a, b] of spans) {
      if (a > last) cell.append(form.slice(last, a));
      const mark = document.createElement('u');
      mark.textContent = form.slice(a, b);
      cell.append(mark);
      last = b;
    }
    cell.append(form.slice(last));

    if (canSpeak()) {
      cell.classList.add('speakable');
      cell.addEventListener('click', () => speak(form, 'es'));
    }
    return cell;
  }));

  host.replaceChildren(grid);
  if (canSpeak()) host.append(playAllButton(forms, 'Hear the whole present tense'));
  host.classList.remove('hidden');
}

const MOODS = [
  {
    name: 'Indicative', open: true,
    tenses: [
      { key: 'present', en: 'Present', es: 'Presente',
        note: 'Current actions, facts and daily habits.',
        it: 'Matches the Italian presente directly.' },
      { key: 'imperfect', en: 'Imperfect', es: 'Pretérito imperfecto',
        note: 'Ongoing, repeated or background actions in the past.',
        it: 'The same job as the Italian imperfetto, and the same feel.' },
      { key: 'preterite', en: 'Preterite', es: 'Pretérito indefinido',
        note: 'Completed actions at a specific moment.',
        warn: 'This is where Italian\u2019s everyday past lands. "Ieri ho detto" ' +
              'is "ayer dije" — not the perfect below.' },
      { key: 'perfect', en: 'Present perfect', es: 'Pretérito perfecto',
        note: 'haber plus a past participle, for the recent past still connected to now.',
        warn: 'Identical in form to the passato prossimo, and much rarer in Latin ' +
              'America. When in doubt, use the preterite.' },
      { key: 'near', en: 'Near future', es: 'Ir + a + infinitivo',
        note: 'Plans, without needing the future tense — like "going to say".',
        it: 'Italian has no equivalent construction; it uses the present or the future.' },
      { key: 'future', en: 'Future', es: 'Futuro',
        note: 'What will happen — and, as in Italian, guesses about the present.',
        it: 'Matches the futuro semplice, including "will be" as supposition.' },
    ],
  },
  {
    name: 'Subjunctive', open: false,
    tenses: [
      { key: 'subjPresent', en: 'Present', es: 'Presente de subjuntivo',
        note: 'After doubt, desire, emotion and impersonal expressions.',
        it: 'The congiuntivo presente, and the triggers are largely the same.' },
      { key: 'subjImperfect', en: 'Imperfect', es: 'Pretérito imperfecto de subjuntivo',
        note: 'The past subjunctive, plus si-clauses and polite requests.',
        it: 'The congiuntivo imperfetto. A second form in -se exists and is interchangeable; ' +
            'Latin America prefers the -ra shown here.' },
    ],
  },
  {
    name: 'Imperative', open: false,
    tenses: [
      { key: 'impAffirm', en: 'Affirmative', es: 'Imperativo afirmativo',
        note: 'Commands. No yo form — you cannot order yourself about.',
        it: 'The usted and ustedes commands are borrowed from the subjunctive.' },
      { key: 'impNegative', en: 'Negative', es: 'Imperativo negativo',
        note: 'Every negative command is the subjunctive with "no" in front.',
        it: 'Italian does this differently: the negative tú command is the infinitive, ' +
            '"non dire".' },
    ],
  },
  {
    name: 'Conditional', open: false,
    tenses: [
      { key: 'conditional', en: 'Conditional', es: 'Condicional',
        note: 'Would-statements, hypotheticals and softened requests.',
        it: 'The condizionale, used the same way.' },
    ],
  },
];

const IMPERATIVE_KEYS = new Set(['impAffirm', 'impNegative']);

async function openConjugation() {
  const card = state.queue[state.index].card;
  const all = await loadConjugations();
  const data = all.verbs[card.es];
  if (!data) return;

  const pronouns = all.pronouns || [];
  const impPronouns = all.imperativePronouns || pronouns;

  $('#conj-title').textContent = card.es;
  const body = $('#conj-body');
  body.replaceChildren();

  for (const mood of MOODS) {
    const blocks = mood.tenses.filter(t => data[t.key]);
    if (!blocks.length) continue;

    // Indicative carries the tenses in daily use, so it opens; the rest are a
    // tap away rather than a long scroll past things you are not looking for.
    const section = document.createElement('details');
    section.className = 'mood';
    section.open = mood.open;

    const summary = document.createElement('summary');
    summary.textContent = mood.name;
    section.append(summary);

    for (const t of blocks) {
      const h = document.createElement('h3');
      h.className = 'section-label tense-head';
      h.textContent = t.en + ' · ' + t.es;
      if (canSpeak()) {
        h.append(playAllButton(data[t.key], `Hear the ${t.en.toLowerCase()} through`));
      }
      section.append(h);

      const note = document.createElement('p');
      note.className = 'muted small conj-note';
      note.textContent = t.note;
      section.append(note);

      if (t.warn) {
        const w = document.createElement('p');
        w.className = 'conj-warn';
        w.textContent = t.warn;
        section.append(w);
      } else if (t.it) {
        const i = document.createElement('p');
        i.className = 'conj-italian';
        i.textContent = t.it;
        section.append(i);
      }

      const labels = IMPERATIVE_KEYS.has(t.key) ? impPronouns : pronouns;
      const table = document.createElement('div');
      table.className = 'conj-table';
      data[t.key].forEach((form, i) => {
        const row = document.createElement('div');
        row.className = 'conj-row';

        const p = document.createElement('span');
        p.className = 'conj-pron';
        p.textContent = labels[i] || '';

        const cell = document.createElement('span');
        cell.className = 'conj-es';
        cell.textContent = form;
        if (canSpeak()) {
          cell.addEventListener('click', () => speak(form, 'es'));
          cell.classList.add('speakable');
        }

        row.append(p, cell);
        table.append(row);
      });
      section.append(table);
    }
    body.append(section);
  }

  show('conj');
  window.scrollTo(0, 0);
}

// ---------- progress ----------

const GRADE_ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'New'];

function bar(label, sub, value, max, cls, text) {
  const row = document.createElement('div');
  row.className = 'bar-row';
  const name = document.createElement('span');
  name.className = 'bar-label';
  name.textContent = label;
  const track = document.createElement('div');
  track.className = 'bar-track';
  const fill = document.createElement('div');
  fill.className = 'bar-fill ' + cls;
  fill.style.width = max ? (100 * value / max) + '%' : '0';
  track.append(fill);
  const n = document.createElement('span');
  n.className = 'bar-value';
  n.textContent = text !== undefined ? text : value;
  if (sub) name.title = sub;
  row.append(name, track, n);
  return row;
}

// Everything on this page can be read two ways: against the deck as it is
// currently filtered, or against the whole thing. Filtered is what you are
// working on; whole is what you have actually done, and a page that only ever
// showed the first would keep hiding progress the moment you narrowed a filter.
let progressScope = 'deck';

const EVERYTHING = {
  tiers: TIER_ORDER,
  buckets: Object.keys(BUCKET_LABEL),
  pos: Object.keys(POS_LABEL),
  directions: Object.keys(DIRECTIONS),
  grades: [],
  newOnly: false,
};

function scopedItems(progress) {
  return progressScope === 'deck'
    ? state.items
    : buildItems(state.deck, progress, EVERYTHING);
}

function scopedReviews(reviews, items) {
  if (progressScope !== 'deck') return reviews;
  const keys = new Set(items.map(i => i.key));
  return reviews.filter(r => keys.has(r.key));
}

async function openProgress() {
  show('progress');
  const [progress, reviews] = await Promise.all([db.allProgress(), db.allReviews()]);
  renderProgress(progress, reviews);
  window.scrollTo(0, 0);
}

function renderProgress(progress, reviews) {
  const items = scopedItems(progress);
  const seen = scopedReviews(reviews, items);

  $('#scope-toggle').replaceChildren(...[
    ['deck', 'This deck'], ['all', 'Everything'],
  ].map(([value, label]) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'chip';
    b.textContent = label;
    b.setAttribute('aria-pressed', String(progressScope === value));
    b.addEventListener('click', () => {
      progressScope = value;
      renderProgress(progress, reviews);
    });
    return b;
  }));

  renderStats(items, seen);
  renderGrades(items);
  renderDirections(seen);
  renderForecast(items);
  renderDays(seen);
  renderTrouble(progress, items);
}

// --- the headline numbers ---

function renderStats(items, reviews) {
  const dist = gradeBreakdown(items);
  const started = GRADES.reduce((s, g) => s + dist[g], 0);

  const today = startOfToday();
  const todayCount = reviews.filter(r => r.ts >= today).length;

  const graded = reviews.filter(r => typeof r.grade === 'number');
  const kept = graded.filter(r => r.grade !== AGAIN).length;
  const accuracy = graded.length ? Math.round(100 * kept / graded.length) : null;

  const stats = [
    [streakOf(reviews), 'day streak'],
    [todayCount, 'today'],
    [reviews.length, 'reviews'],
    [accuracy === null ? '–' : accuracy + '%', 'kept'],
    [started, 'started'],
  ];

  $('#stat-row').replaceChildren(...stats.map(([value, label]) => {
    const cell = document.createElement('div');
    cell.className = 'stat';
    const b = document.createElement('b');
    b.textContent = value;
    const s = document.createElement('span');
    s.textContent = label;
    cell.append(b, s);
    return cell;
  }));
}

// Consecutive days ending today or yesterday. Yesterday still counts, so the
// streak does not appear to break before the day is over.
function streakOf(reviews) {
  if (!reviews.length) return 0;
  const days = new Set();
  for (const r of reviews) {
    const d = new Date(r.ts);
    d.setHours(0, 0, 0, 0);
    days.add(d.getTime());
  }
  let cursor = startOfToday();
  if (!days.has(cursor)) {
    cursor -= DAY;
    if (!days.has(cursor)) return 0;
  }
  let n = 0;
  while (days.has(cursor)) { n++; cursor -= DAY; }
  return n;
}

// --- by grade ---

function renderGrades(items) {
  const dist = gradeBreakdown(items);
  const letterMax = Math.max(1, ...GRADES.map(g => dist[g]));
  const rows = GRADES.map(g =>
    bar(g, gradeRange(g), dist[g], letterMax, 'g-' + g.toLowerCase()));

  // New keeps its place but sits outside the scale, drawn full length and
  // striped: early on it outnumbers the rest by two orders of magnitude, and
  // sharing a scale with it flattens every bar worth reading.
  rows.push(bar('New', 'never reviewed', 1, 1, 'g-new', String(dist.New)));

  const learned = GRADES.reduce((s, g) => s + dist[g], 0);
  const note = document.createElement('p');
  note.className = 'muted small chart-note';
  note.textContent = learned
    ? `${learned} of ${learned + dist.New} cards started`
    : 'Nothing reviewed yet';
  $('#grade-chart').replaceChildren(...rows, note);
}

// --- recognition against production ---
//
// The one comparison this app exists to make. Reading Spanish and recalling
// the Italian is recognition; going the other way is production, and it should
// be harder. Seeing by how much is the useful part.

function renderDirections(reviews) {
  const rows = Object.entries(DIRECTIONS).map(([key, dir]) => {
    const mine = reviews.filter(r => r.direction === key && typeof r.grade === 'number');
    const kept = mine.filter(r => r.grade !== AGAIN).length;
    return {
      label: dir.label, kind: dir.kind, total: mine.length,
      pct: mine.length ? Math.round(100 * kept / mine.length) : null,
    };
  });

  $('#direction-chart').replaceChildren(...rows.map(r => {
    const row = document.createElement('div');
    row.className = 'bar-row';
    const name = document.createElement('span');
    name.className = 'bar-label';
    name.textContent = r.label;
    const track = document.createElement('div');
    track.className = 'bar-track';
    const fill = document.createElement('div');
    fill.className = 'bar-fill ' + (r.kind === 'production' ? 'g-b' : 'g-a');
    fill.style.width = (r.pct === null ? 0 : r.pct) + '%';
    track.append(fill);
    const value = document.createElement('span');
    value.className = 'bar-value';
    value.textContent = r.pct === null ? '–' : r.pct + '%';
    row.append(name, track, value);
    return row;
  }));

  const [recog, prod] = rows;
  $('#direction-note').textContent =
    recog.pct === null || prod.pct === null
      ? 'Not enough reviews in both directions yet.'
      : prod.pct < recog.pct
        ? `Production is ${recog.pct - prod.pct} points behind recognition, which is `
          + 'the usual way round.'
        : 'Production is holding up with recognition, which is unusual and good.';
}

// --- words that keep going wrong ---

function renderTrouble(progress, items) {
  const inScope = new Set(items.map(i => i.key));
  const byCard = new Map();
  for (const p of progress) {
    if (!p.lapses || !inScope.has(p.key)) continue;
    byCard.set(p.cardId, (byCard.get(p.cardId) || 0) + p.lapses);
  }
  const deck = new Map(state.deck.map(c => [c.es, c]));
  const worst = [...byCard.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([id, lapses]) => ({ card: deck.get(id), lapses }))
    .filter(r => r.card);

  $('#trouble-list').replaceChildren(...worst.map(({ card, lapses }) => {
    const row = document.createElement('div');
    row.className = 'trouble-row';
    const es = document.createElement('b');
    es.textContent = card.es;
    const it = document.createElement('span');
    it.className = 'trouble-it';
    it.textContent = card.senses.join(' · ');
    const n = document.createElement('span');
    n.className = 'trouble-count';
    n.textContent = lapses;
    row.append(es, it, n);
    return row;
  }));
  $('#trouble-note').textContent = worst.length
    ? 'Times you pressed Again. These are the ones worth a second look.'
    : 'Nothing has tripped you up yet.';
}

// What is coming, rather than what has happened. Overdue collapses into the
// first column, because "how big is the hole I am in" is one number, not a
// history lesson.
function renderForecast(items, days = 14) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const start = today.getTime();

  const cols = Array.from({ length: days }, (_, i) => ({ i, n: 0 }));
  let overdue = 0, beyond = 0;
  for (const it of items) {
    if (isNewItem(it)) continue;
    const d = Math.floor((it.due - start) / 86400000);
    if (d < 0) overdue++;
    else if (d < days) cols[d].n++;
    else beyond++;
  }
  cols[0].n += overdue;

  const peak = Math.max(1, ...cols.map(c => c.n));
  const readout = $('#forecast-readout');
  $('#forecast-chart').replaceChildren(...cols.map(c => {
    const date = new Date(start + c.i * 86400000);
    const when = c.i === 0 ? 'Today' : longDate(date);
    return barColumn({
      value: c.n, peak, readout,
      label: dayTick(date, c.i === 0),
      title: `${when} — ${c.n} due`
             + (c.i === 0 && overdue ? ` (${overdue} overdue)` : ''),
      cls: c.i === 0 && overdue ? 'overdue' : '',
    });
  }));
  readout.textContent = '';

  const total = cols.reduce((s, c) => s + c.n, 0);
  $('#forecast-summary').textContent = total || beyond
    ? `${total} due in the next ${days} days`
      + (overdue ? ` · ${overdue} overdue` : '')
      + (beyond ? ` · ${beyond} further out` : '')
    : 'Nothing scheduled yet.';
}

// One column: the count above it, the bar, and a label beneath. Tapping it
// writes the full date into the readout under the chart, since a title
// attribute is invisible on a phone and the tick can only hold a number.
function barColumn({ value, peak, label, title, cls, readout }) {
  const col = document.createElement('div');
  col.className = 'day-col';
  col.title = title;
  if (readout) {
    col.addEventListener('click', () => {
      readout.textContent = title;
      [...readout.parentElement.querySelectorAll('.day-col.picked')]
        .forEach(c => c.classList.remove('picked'));
      col.classList.add('picked');
    });
  }

  const count = document.createElement('span');
  count.className = 'day-count';
  count.textContent = value || '';
  col.append(count);

  const track = document.createElement('div');
  track.className = 'day-track';
  const fill = document.createElement('div');
  fill.className = 'day-fill' + (value ? '' : ' empty') + (cls ? ' ' + cls : '');
  fill.style.height = (100 * value / peak) + '%';
  track.append(fill);
  col.append(track);

  const tick = document.createElement('span');
  tick.className = 'day-tick';
  tick.textContent = label;
  col.append(tick);
  return col;
}

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function longDate(d) {
  return `${WEEKDAYS[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]}`;
}

// The tick under a column. Only the day number fits, so the month is added on
// the first of it and today is named outright.
function dayTick(d, isToday) {
  if (isToday) return 'today';
  if (d.getDate() === 1) return `${d.getDate()} ${MONTHS[d.getMonth()]}`;
  return String(d.getDate());
}

// Reviews per day, running left to right.
//
// The window starts at the first review rather than always a fixed number of
// days back. Anchoring it to today meant an empty chart with everything
// bunched against the right edge, growing leftwards as days passed, which
// reads backwards however the dates actually run.
function renderDays(reviews, maxDays = 14) {
  const byDay = new Map();
  let earliest = null;
  for (const r of reviews) {
    const d = new Date(r.ts);
    d.setHours(0, 0, 0, 0);
    const key = d.getTime();
    byDay.set(key, (byDay.get(key) || 0) + 1);
    if (earliest === null || key < earliest) earliest = key;
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const span = earliest === null
    ? 1
    : Math.floor((today.getTime() - earliest) / 86400000) + 1;
  const days = Math.max(1, Math.min(maxDays, span));

  const cols = [];
  for (let i = days - 1; i >= 0; i--) {
    const t = today.getTime() - i * 86400000;
    cols.push({ t, n: byDay.get(t) || 0 });
  }
  const peak = Math.max(1, ...cols.map(c => c.n));

  const readout = $('#day-readout');
  $('#day-chart').replaceChildren(...cols.map((c, i) => {
    const date = new Date(c.t);
    const last = i === cols.length - 1;
    return barColumn({
      value: c.n, peak, readout,
      label: dayTick(date, last),
      title: (last ? 'Today' : longDate(date))
             + ` — ${c.n} review${c.n === 1 ? '' : 's'}`,
    });
  }));
  readout.textContent = '';

  const active = cols.filter(c => c.n).length;
  const total = cols.reduce((s, c) => s + c.n, 0);
  const from = new Date(cols[0].t), to = new Date(cols[cols.length - 1].t);
  $('#day-summary').textContent = total
    ? `${longDate(from)} to ${longDate(to)} · ${total} reviews over `
      + `${active} day${active === 1 ? '' : 's'} · busiest ${peak}`
    : 'No reviews recorded yet.';
}

// Export is the only thing standing between an iOS storage eviction and
// starting over, and it only works if it actually gets done. Nagging is
// limited to when there is progress worth losing.
function renderBackupState(lastBackup, learned) {
  const warn = $('#backup-warning');
  const when = $('#backup-when');
  const days = lastBackup ? Math.floor((Date.now() - lastBackup) / DAY) : null;

  when.textContent = lastBackup
    ? `Last backup: ${days === 0 ? 'today' : days === 1 ? 'yesterday' : days + ' days ago'}.`
    : 'Never backed up.';

  const stale = learned > 0 && (lastBackup === undefined || days >= BACKUP_NAG_DAYS);
  warn.classList.toggle('hidden', !stale);
  // Short enough for one line. Export sits directly below now, so the banner
  // does not need to say where to find it.
  if (stale) {
    warn.textContent = lastBackup
      ? `Last backed up ${days} days ago`
      : `${learned} cards in progress and no backup yet`;
  }
}

// ---------- backup ----------

async function exportProgress() {
  const [progress, reviews] = await Promise.all([db.allProgress(), db.allReviews()]);
  const payload = {
    app: 'spanish_app',
    version: 2,
    exported: new Date().toISOString(),
    settings: state.settings,
    progress,
    reviews,
  };
  const blob = new Blob([JSON.stringify(payload, null, 1)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `spanish-progress-${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
  await db.setMeta('lastBackup', Date.now());
  await refresh();
  $('#backup-msg').textContent = `Exported ${progress.length} cards and ${reviews.length} reviews.`;
}

async function importProgress(file) {
  try {
    const data = JSON.parse(await file.text());
    if (data.app !== 'spanish_app' || !Array.isArray(data.progress)) {
      throw new Error('not a progress file');
    }
    await db.putMany(data.progress);
    if (Array.isArray(data.reviews)) await db.putReviews(data.reviews);
    if (data.settings) {
      state.settings = { ...DEFAULT_SETTINGS, ...data.settings };
      await db.setMeta('settings', state.settings);
      renderFilters();
    }
    await refresh();
    const n = Array.isArray(data.reviews) ? data.reviews.length : 0;
    $('#backup-msg').textContent =
      `Imported ${data.progress.length} cards` + (n ? ` and ${n} reviews.` : '.');
  } catch (err) {
    $('#backup-msg').textContent = 'Could not read that file: ' + err.message;
  }
}

// ---------- wiring ----------

function wire() {
  $('#start').addEventListener('click', startSession);
  $('#reveal').addEventListener('click', reveal);
  $('#quit').addEventListener('click', finish);
  $('#back-home').addEventListener('click', () => show('home'));
  $('#f-size').addEventListener('change', e => {
    state.settings.sessionSize = Number(e.target.value) || 15;
    save();
  });
  $('#open-progress').addEventListener('click', openProgress);
  $('#close-progress').addEventListener('click', () => show('home'));
  $('#open-deck').addEventListener('click', () => show('deck'));
  $('#close-deck').addEventListener('click', () => {
    if (listPlaying) { stopSpeech(); setListButton(false); }
    show('home');
  });
  $('#word-list-panel').addEventListener('toggle', e => {
    if (e.target.open) renderWordList();
    else if (listPlaying) { stopSpeech(); setListButton(false); }
  });
  $('#word-list-play').addEventListener('click', toggleListPlayback);
  $('#open-settings').addEventListener('click', () => show('settings'));
  $('#close-settings').addEventListener('click', () => show('home'));
  $('#grade-row').addEventListener('click', e => {
    const b = e.target.closest('button[data-g]');
    if (b) applyGrade(Number(b.dataset.g));
  });
  $('#say-prompt').addEventListener('click', () => {
    const item = state.queue[state.index];
    const dir = DIRECTIONS[item.direction];
    speak(item.card[dir.prompt], dir.prompt);
  });
  $('#accents').addEventListener('click', () => {
    speakOtherAccent(state.queue[state.index].card.es);
  });
  $('#examples-btn').addEventListener('click', toggleExamples);
  $('#conj-btn').addEventListener('click', openConjugation);
  $('#close-conj').addEventListener('click', () => show('review'));

  $('#export').addEventListener('click', exportProgress);
  $('#import-btn').addEventListener('click', () => $('#import').click());
  $('#import').addEventListener('change', e => {
    if (e.target.files[0]) importProgress(e.target.files[0]);
    e.target.value = '';
  });

  document.addEventListener('keydown', e => {
    if ($('#view-review').classList.contains('hidden')) return;
    if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); state.revealed ? applyGrade(GOOD) : reveal(); }
    else if (e.key >= '1' && e.key <= '4') applyGrade(Number(e.key) - 1);
    else if (e.key === 'Escape') finish();
  });
}

boot().catch(() => {});
