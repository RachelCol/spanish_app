import { db, requestPersistence } from './db.js';
import { grade, intervalLabel, gradeLetter, gradeRange, GRADES, isNew as isNewItem,
         AGAIN, HARD, GOOD, EASY } from './srs.js';
import { loadDeck, loadSentences, buildItems, DIRECTIONS, BUCKET_LABEL, TIER_ORDER,
         DEFAULT_SETTINGS, SESSION_SIZES } from './deck.js';
import { buildQueue, counts, gradeBreakdown } from './session.js';
import { initVoices, onVoicesReady, setAccent, ACCENTS, describeVoice, SAMPLE,
         differsByAccent, hasAccentPair, speakOtherAccent, otherAccent,
         available as canSpeak, speak, speakPair, stop as stopSpeech } from './speech.js';

const $ = sel => document.querySelector(sel);

const state = {
  deck: [],
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
        : 'Nothing left in this deck. Widen the filters under Deck to add more.';
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
}

// ---------- review ----------

function show(view) {
  ['home', 'review', 'done', 'progress'].forEach(v =>
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
  $('#prompt').textContent = item.card[dir.prompt];
  $('#answer').textContent = item.card[dir.answer];
  $('#meta').innerHTML =
    `<span class="pos">${item.card.pos}</span> · ${BUCKET_LABEL[item.card.bucket]}`;

  stopSpeech();
  $('#answer-row').classList.add('hidden');
  $('#meta').classList.add('hidden');
  $('#compare').classList.add('hidden');
  $('#accent-note').classList.add('hidden');
  $('#card-links').classList.add('hidden');
  $('#examples-btn').classList.add('hidden');
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
  const card = state.queue[state.index].card;
  $('#answer-row').classList.remove('hidden');
  $('#meta').classList.remove('hidden');

  // The sound shift is the lesson for pairs that are close but not identical,
  // so those get a back-to-back playback. Identical and unrelated pairs have
  // nothing to compare.
  const teachable = card.bucket === 'near' || card.bucket === 'shifted';
  $('#compare').classList.toggle('hidden', !(canSpeak() && teachable));

  // Called from a tap or keypress, which is what iOS requires.
  // Offered only on the ~1 in 5 words the accents actually pronounce
  // differently; everywhere else it would just play the same thing twice.
  // The accent difference is a footnote on the word, not a headline action,
  // so it sits with the part-of-speech line rather than beside "Hear both".
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

  loadSentences().then(all => {
    // The card may have moved on while the file was loading.
    if (state.queue[state.index] && state.queue[state.index].card.es === card.es) {
      $('#examples-btn').classList.toggle('hidden', !(all[card.es] || []).length);
    }
  });

  // Both sides, prompt first. Turning the card over is the moment the pair
  // exists as a pair, and hearing it in reading order is what makes the
  // sound difference land.
  if (state.settings.autoSpeak && canSpeak()) {
    const dir = DIRECTIONS[state.queue[state.index].direction];
    speakPair(card[dir.prompt], dir.prompt, card[dir.answer], dir.answer);
  }
  $('#reveal-row').classList.add('hidden');
  $('#grade-row').classList.remove('hidden');

  // Show what each button costs before it is pressed.
  const item = state.queue[state.index];
  [AGAIN, HARD, GOOD, EASY].forEach(g => {
    $(`#grade-row button[data-g="${g}"] small`).textContent = intervalLabel(item, g);
  });
}

// Bold whatever in the sentence came from this word. Matching on a prefix
// rather than the exact form is deliberate: `hermano` should light up
// `hermanos`, and `trabajar` should light up `trabajo`, without needing the
// lemmatizer at runtime.
function highlight(sentence, lemma) {
  const stem = lemma.slice(0, Math.max(4, lemma.length - 2)).toLowerCase();
  const frag = document.createDocumentFragment();
  for (const part of sentence.split(/(\s+)/)) {
    const bare = part.toLowerCase().replace(/[^a-záéíóúüñ]/gi, '');
    if (bare.length >= stem.length && bare.startsWith(stem)) {
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
  panel.replaceChildren(...rows.map(r => {
    const block = document.createElement('div');
    block.className = 'example';

    const es = document.createElement('p');
    es.className = 'example-es';
    es.append(highlight(r.es, card.es));
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
  }), credit());
  panel.classList.remove('hidden');
}

// CC BY 2.0 FR asks for attribution wherever the sentences are shown.
function credit() {
  const p = document.createElement('p');
  p.className = 'example-credit';
  const a = document.createElement('a');
  a.href = 'https://tatoeba.org';
  a.target = '_blank';
  a.rel = 'noopener noreferrer';
  a.textContent = 'Tatoeba';
  p.append('Sentences from ', a, ' · CC BY 2.0 FR');
  return p;
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

async function openProgress() {
  show('progress');

  const dist = gradeBreakdown(state.items);

  // Scale the letters against each other, not against New. Early on New
  // outnumbers everything by a hundred to one, and sharing a scale with it
  // flattens every bar you actually want to read.
  const letterMax = Math.max(1, ...GRADES.map(g => dist[g]));
  const rows = GRADES.map(g => bar(g, gradeRange(g), dist[g], letterMax, 'g-' + g.toLowerCase()));

  // New keeps its place in the chart but sits outside the scale -- drawn full
  // length and striped, so it reads as "all of these, not to scale" rather
  // than as a bar a hundred times longer than the rest.
  rows.push(bar('New', 'never reviewed', 1, 1, 'g-new', String(dist.New)));

  const learned = GRADES.reduce((s, g) => s + dist[g], 0);
  const note = document.createElement('p');
  note.className = 'muted small chart-note';
  note.textContent = learned
    ? `${learned} of ${learned + dist.New} cards started`
    : 'Nothing reviewed yet';
  $('#grade-chart').replaceChildren(...rows, note);

  renderForecast(state.items);

  renderDays(await db.allReviews());
}

// What is coming, rather than what has happened. Overdue collapses into the
// first column, because "how big is the hole I am in" is one number, not a
// history lesson.
function renderForecast(items, days = 30) {
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
  $('#forecast-chart').replaceChildren(...cols.map(c => {
    const col = document.createElement('div');
    col.className = 'day-col';
    const fill = document.createElement('div');
    fill.className = 'day-fill';
    fill.style.height = (100 * c.n / peak) + '%';
    if (!c.n) fill.classList.add('empty');
    if (c.i === 0 && overdue) fill.classList.add('overdue');
    const when = c.i === 0 ? 'today' : `in ${c.i} day${c.i === 1 ? '' : 's'}`;
    col.title = `${when} — ${c.n} due`;
    col.append(fill);
    return col;
  }));

  const total = cols.reduce((s, c) => s + c.n, 0);
  $('#forecast-summary').textContent = total || beyond
    ? `${total} due in the next ${days} days` +
      (overdue ? ` · ${overdue} overdue` : '') +
      (beyond ? ` · ${beyond} further out` : '')
    : 'Nothing scheduled yet.';
}

function renderDays(reviews, days = 30) {
  const byDay = new Map();
  for (const r of reviews) {
    const d = new Date(r.ts);
    d.setHours(0, 0, 0, 0);
    byDay.set(d.getTime(), (byDay.get(d.getTime()) || 0) + 1);
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const cols = [];
  for (let i = days - 1; i >= 0; i--) {
    const t = today.getTime() - i * 86400000;
    cols.push({ t, n: byDay.get(t) || 0 });
  }
  const peak = Math.max(1, ...cols.map(c => c.n));

  $('#day-chart').replaceChildren(...cols.map(c => {
    const col = document.createElement('div');
    col.className = 'day-col';
    const fill = document.createElement('div');
    fill.className = 'day-fill';
    fill.style.height = (100 * c.n / peak) + '%';
    if (!c.n) fill.classList.add('empty');
    col.title = new Date(c.t).toDateString() + ' — ' + c.n + ' reviews';
    col.append(fill);
    return col;
  }));

  const active = cols.filter(c => c.n).length;
  const total = cols.reduce((s, c) => s + c.n, 0);
  $('#day-summary').textContent = total
    ? `${total} reviews over ${active} day${active === 1 ? '' : 's'} · busiest ${peak}`
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
  if (stale) {
    warn.textContent = lastBackup
      ? `Last backed up ${days} days ago — export again under Backup.`
      : `${learned} cards in progress and no backup yet. Export under Backup.`;
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
  $('#grade-row').addEventListener('click', e => {
    const b = e.target.closest('button[data-g]');
    if (b) applyGrade(Number(b.dataset.g));
  });
  $('#say-prompt').addEventListener('click', () => {
    const item = state.queue[state.index];
    const dir = DIRECTIONS[item.direction];
    speak(item.card[dir.prompt], dir.prompt);
  });
  $('#say-answer').addEventListener('click', () => {
    const item = state.queue[state.index];
    const dir = DIRECTIONS[item.direction];
    speak(item.card[dir.answer], dir.answer);
  });
  $('#accents').addEventListener('click', () => {
    speakOtherAccent(state.queue[state.index].card.es);
  });
  $('#examples-btn').addEventListener('click', toggleExamples);
  $('#compare').addEventListener('click', () => {
    const item = state.queue[state.index];
    const dir = DIRECTIONS[item.direction];
    speakPair(item.card[dir.prompt], dir.prompt, item.card[dir.answer], dir.answer);
  });

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
