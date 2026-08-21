import { db, requestPersistence } from './db.js';
import { grade, intervalLabel, AGAIN, HARD, GOOD, EASY } from './srs.js';
import { loadDeck, buildItems, DIRECTIONS, BUCKET_LABEL, TIER_ORDER, DEFAULT_SETTINGS } from './deck.js';
import { buildQueue, counts } from './session.js';
import { initVoices, onVoicesReady, listVoices, setVoice, isNovelty, SAMPLE,
         available as canSpeak, speak, compare, stop as stopSpeech } from './speech.js';

const $ = sel => document.querySelector(sel);

const state = {
  deck: [],
  items: [],
  settings: { ...DEFAULT_SETTINGS },
  queue: [],
  index: 0,
  revealed: false,
  graded: 0,
};

// ---------- boot ----------

async function boot() {
  state.deck = await loadDeck();
  const saved = await db.getMeta('settings');
  if (saved) state.settings = { ...DEFAULT_SETTINGS, ...saved };
  await refresh();
  renderFilters();
  wire();
  initVoices();
  onVoicesReady(() => {
    setVoice('es', state.settings.voiceEs);
    setVoice('it', state.settings.voiceIt);
    renderVoicePickers();
  });
  requestPersistence();
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
}

async function refresh() {
  const progress = await db.allProgress();
  state.items = buildItems(state.deck, progress, state.settings);
  const c = counts(state.items);
  $('#c-due').textContent = c.due;
  $('#c-new').textContent = Math.min(c.new, state.settings.newPerDay);
  $('#c-learned').textContent = c.learned;
  const empty = c.due === 0 && c.new === 0;
  $('#start').classList.toggle('hidden', empty);
  $('#nothing-due').classList.toggle('hidden', !empty);
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

  $('#f-new').value = s.newPerDay;
}

function renderVoicePickers() {
  const host = $('#voice-rows');
  if (!canSpeak()) { host.replaceChildren(); return; }

  const rows = [
    { which: 'es', label: 'Spanish voice', key: 'voiceEs' },
    { which: 'it', label: 'Italian voice', key: 'voiceIt' },
  ].map(({ which, label, key }) => {
    const groups = listVoices(which);
    if (!groups.length) return null;

    const row = document.createElement('label');
    row.className = 'row voice-row';
    row.append(label);

    const sel = document.createElement('select');
    for (const [lang, list] of groups) {
      const g = document.createElement('optgroup');
      g.label = lang;
      for (const v of list) {
        const o = document.createElement('option');
        o.value = v.name;
        o.textContent = isNovelty(v) ? v.name + ' (novelty)' : v.name;
        o.selected = state.settings[key] === v.name;
        g.append(o);
      }
      sel.append(g);
    }
    // Nothing stored yet: show what the automatic pick would be.
    if (!state.settings[key]) {
      const auto = document.createElement('option');
      auto.value = '';
      auto.textContent = 'Automatic';
      auto.selected = true;
      sel.prepend(auto);
    }

    sel.addEventListener('change', async () => {
      state.settings[key] = sel.value || null;
      setVoice(which, sel.value || null);
      await db.setMeta('settings', state.settings);
      speak(SAMPLE[which], which);
    });

    const play = document.createElement('button');
    play.type = 'button';
    play.className = 'say';
    play.textContent = '▶';
    play.setAttribute('aria-label', 'Preview ' + label);
    play.addEventListener('click', e => { e.preventDefault(); speak(SAMPLE[which], which); });

    const wrap = document.createElement('span');
    wrap.className = 'voice-control';
    wrap.append(sel, play);
    row.append(wrap);
    return row;
  }).filter(Boolean);

  host.replaceChildren(...rows);
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
  ['home', 'review', 'done'].forEach(v =>
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
  if (state.settings.autoSpeak && canSpeak()) speak(card.es, 'es');
  $('#reveal-row').classList.add('hidden');
  $('#grade-row').classList.remove('hidden');

  // Show what each button costs before it is pressed.
  const item = state.queue[state.index];
  [AGAIN, HARD, GOOD, EASY].forEach(g => {
    $(`#grade-row button[data-g="${g}"] small`).textContent = intervalLabel(item, g);
  });
}

async function applyGrade(g) {
  if (!state.revealed) return;
  const item = state.queue[state.index];
  const { card, ...bare } = item;
  const next = grade(bare, g);
  await db.putProgress(next);
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

// ---------- backup ----------

async function exportProgress() {
  const progress = await db.allProgress();
  const payload = {
    app: 'spanish_app',
    version: 1,
    exported: new Date().toISOString(),
    settings: state.settings,
    progress,
  };
  const blob = new Blob([JSON.stringify(payload, null, 1)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `spanish-progress-${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
  $('#backup-msg').textContent = `Exported ${progress.length} items.`;
}

async function importProgress(file) {
  try {
    const data = JSON.parse(await file.text());
    if (data.app !== 'spanish_app' || !Array.isArray(data.progress)) {
      throw new Error('not a progress file');
    }
    await db.putMany(data.progress);
    if (data.settings) {
      state.settings = { ...DEFAULT_SETTINGS, ...data.settings };
      await db.setMeta('settings', state.settings);
      renderFilters();
    }
    await refresh();
    $('#backup-msg').textContent = `Imported ${data.progress.length} items.`;
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
  $('#f-new').addEventListener('change', e => {
    state.settings.newPerDay = Math.max(0, Number(e.target.value) || 0);
    save();
  });
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
  $('#compare').addEventListener('click', () => {
    const card = state.queue[state.index].card;
    compare(card.it, card.es);
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

boot();
