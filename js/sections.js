// Wiring for the grammar, drill, preposition and conversation sections.
//
// Everything here is additive. It shares the view-switching helper and the
// speech module with the flashcards and touches nothing else, so a fault in
// this file cannot reach the deck, the scheduler or the review history.

import { loadGrammar, renderIndex, renderLesson } from './grammar.js';
import {
  DRILL_TENSES, loadDrillVerbs, loadExtras, checkAnswer,
  buildVerbQuestions, buildPrepositionQuestions, speakerButton,
} from './drills.js';
import { speak, available as canSpeak } from './speech.js';

const $ = sel => document.querySelector(sel);
const QUESTIONS_PER_RUN = 20;

let show;                       // injected: the app's view switcher
let conjugations = null;        // shared with the flashcards, read-only

// ---------- small builders ----------

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

function chipRow(items, selected, onToggle) {
  const row = el('div', 'chips');
  for (const { value, label, sub } of items) {
    const b = el('button', 'chip');
    b.type = 'button';
    b.setAttribute('aria-pressed', String(selected.has(value)));
    b.innerHTML = sub ? `${label}<small>${sub}</small>` : label;
    b.addEventListener('click', () => {
      const on = b.getAttribute('aria-pressed') !== 'true';
      b.setAttribute('aria-pressed', String(on));
      onToggle(value, on);
    });
    row.append(b);
  }
  return row;
}

// ---------- grammar ----------

async function openGrammar() {
  const lessons = await loadGrammar();
  $('#grammar-title').textContent = 'Grammar';
  const body = $('#grammar-body');
  body.replaceChildren(
    el('p', 'muted small section-intro',
       'What Italian gets wrong about Spanish, in rough order of how much '
       + 'trouble it causes.'),
    renderIndex(lessons, lesson => {
      $('#grammar-title').textContent = lesson.title;
      body.replaceChildren(renderLesson(lesson), backButton(openGrammar, 'All lessons'));
      window.scrollTo(0, 0);
    }),
  );
  show('grammar');
  window.scrollTo(0, 0);
}

function backButton(fn, label) {
  const b = el('button', 'compare back-link', '← ' + label);
  b.type = 'button';
  b.addEventListener('click', fn);
  const wrap = el('div', 'compare-row');
  wrap.append(b);
  return wrap;
}

// ---------- conjugation drill ----------

const drillState = { verbs: new Set(), tenses: new Set(['present']), run: null };

async function openDrill() {
  const verbs = await loadDrillVerbs();
  if (!drillState.verbs.size) verbs.slice(0, 10).forEach(v => drillState.verbs.add(v.es));

  $('#drill-title').textContent = 'Conjugation drill';
  const body = $('#drill-body');
  body.replaceChildren();

  body.append(
    el('p', 'muted small section-intro',
       'Type the form. Accents count, but a missing one is treated as a typo '
       + 'and told to you rather than marked wrong.'),
  );

  const tenseSet = el('fieldset');
  tenseSet.append(el('legend', null, 'Tenses'));
  tenseSet.append(chipRow(
    DRILL_TENSES.map(t => ({ value: t.key, label: t.label })),
    drillState.tenses,
    (v, on) => on ? drillState.tenses.add(v) : drillState.tenses.delete(v)));
  body.append(tenseSet);

  const verbSet = el('fieldset');
  verbSet.append(el('legend', null, `Verbs (${verbs.length} most common)`));

  const all = el('div', 'row-buttons');
  const selectAll = el('button', null, 'Select all');
  selectAll.type = 'button';
  selectAll.addEventListener('click', () => {
    verbs.forEach(v => drillState.verbs.add(v.es));
    openDrill();
  });
  const clear = el('button', null, 'Clear');
  clear.type = 'button';
  clear.addEventListener('click', () => { drillState.verbs.clear(); openDrill(); });
  all.append(selectAll, clear);
  verbSet.append(all);

  verbSet.append(chipRow(
    verbs.map(v => ({ value: v.es, label: v.es })),
    drillState.verbs,
    (v, on) => on ? drillState.verbs.add(v) : drillState.verbs.delete(v)));
  body.append(verbSet);

  const start = el('button', 'primary', 'Start drill');
  start.type = 'button';
  start.addEventListener('click', startDrill);
  body.append(start);

  show('drill');
  window.scrollTo(0, 0);
}

async function startDrill() {
  if (!drillState.verbs.size || !drillState.tenses.size) return;
  const pronouns = conjugations.pronouns;
  const questions = buildVerbQuestions(
    conjugations,
    [...drillState.verbs],
    [...drillState.tenses],
    pronouns,
    QUESTIONS_PER_RUN);
  if (!questions.length) return;

  drillState.run = { questions, index: 0, right: 0, wrong: 0 };
  renderQuestion();
}

function renderQuestion() {
  const run = drillState.run;
  const q = run.questions[run.index];
  const body = $('#drill-body');
  body.replaceChildren();

  $('#drill-title').textContent = `${run.index + 1} of ${run.questions.length}`;

  const label = DRILL_TENSES.find(t => t.key === q.tense);
  const prompt = el('div', 'drill-prompt');
  prompt.append(el('b', 'drill-verb', q.verb));
  prompt.append(el('span', 'drill-meta', `${label ? label.label : q.tense} · ${q.person}`));
  body.append(prompt);

  const form = el('form', 'drill-form');
  const input = el('input', 'drill-input');
  input.type = 'text';
  input.autocapitalize = 'none';
  input.autocomplete = 'off';
  input.spellcheck = false;
  input.setAttribute('aria-label', 'Your answer');
  const go = el('button', 'drill-submit', 'Check');
  go.type = 'submit';
  form.append(input, go);
  body.append(form);

  const feedback = el('p', 'drill-feedback');
  body.append(feedback);
  const paradigm = el('div', 'drill-paradigm hidden');
  body.append(paradigm);

  const score = el('p', 'muted small centred',
                   `${run.right} right · ${run.wrong} wrong`);
  body.append(score);

  const submit = () => {
    const verdict = checkAnswer(input.value, q.answer);
    if (verdict === 'wrong') run.wrong++; else run.right++;

    feedback.replaceChildren();
    feedback.className = 'drill-feedback ' + verdict;
    if (verdict === 'right') {
      feedback.append('✓ ' + q.answer);
    } else if (verdict === 'accents') {
      feedback.append(`✓ ${q.answer} — watch the accent`);
    } else {
      feedback.append(`✗ ${q.answer}`);
    }
    const say = speakerButton(q.answer, 'es');
    if (say) feedback.append(' ', say);

    // Getting one wrong is the moment the rest of the paradigm is worth
    // seeing: the form you missed makes more sense beside the five you did
    // not, and the pattern is what carries to the next verb.
    if (verdict !== 'right') {
      const forms = conjugations.verbs[q.verb][q.tense] || [];
      paradigm.replaceChildren(
        el('div', 'paradigm-label', `${q.verb} · ${label ? label.label : q.tense}`));
      forms.forEach((f, i) => {
        const row = el('div', 'paradigm-row' + (f === q.answer ? ' this-one' : ''));
        row.append(el('span', 'paradigm-pron', conjugations.pronouns[i] || ''),
                   el('span', 'paradigm-form', f));
        paradigm.append(row);
      });
      paradigm.classList.remove('hidden');
    }

    form.replaceChildren(input);
    input.disabled = true;
    const next = el('button', 'primary',
                    run.index + 1 < run.questions.length ? 'Next' : 'Finish');
    next.type = 'button';
    next.addEventListener('click', () => {
      run.index++;
      if (run.index < run.questions.length) renderQuestion();
      else finishDrill();
    });
    body.append(next);
    next.focus();
  };

  form.addEventListener('submit', e => { e.preventDefault(); submit(); });
  input.focus();
}

function finishDrill() {
  const run = drillState.run;
  const total = run.right + run.wrong;
  const body = $('#drill-body');
  $('#drill-title').textContent = 'Drill complete';
  body.replaceChildren(
    el('p', 'drill-score', `${run.right} of ${total}`),
    el('p', 'muted small centred',
       total ? `${Math.round(100 * run.right / total)}% correct` : ''),
  );
  const again = el('button', 'primary', 'Drill again');
  again.type = 'button';
  again.addEventListener('click', startDrill);
  body.append(again, backButton(openDrill, 'Change verbs or tenses'));
}

// ---------- preposition drill ----------

const prepState = { direction: 'it>es', run: null };

async function openPrep() {
  const { prepositions } = await loadExtras();
  $('#prep-title').textContent = 'Prepositions';
  const body = $('#prep-body');
  body.replaceChildren(
    el('p', 'muted small section-intro',
       'Where Italian and Spanish disagree most. Type the whole sentence; '
       + 'the preposition is the part being tested, but the rest has to hold '
       + 'together too.'),
  );

  const set = el('fieldset');
  set.append(el('legend', null, 'Direction'));
  const dirs = [
    { value: 'it>es', label: 'Italian → Spanish', sub: 'production' },
    { value: 'es>it', label: 'Spanish → Italian', sub: 'recognition' },
  ];
  set.append(chipRow(dirs, new Set([prepState.direction]), (v, on) => {
    if (on) { prepState.direction = v; openPrep(); }
  }));
  body.append(set);

  const start = el('button', 'primary', 'Start');
  start.type = 'button';
  start.addEventListener('click', () => {
    prepState.run = {
      questions: buildPrepositionQuestions(prepositions, prepState.direction, 15),
      index: 0, right: 0, wrong: 0,
    };
    renderPrepQuestion();
  });
  body.append(start, el('p', 'muted small centred',
                        `${prepositions.length} sentence pairs`));

  const { prepSpanish, prepItalian } = await loadExtras();
  body.append(renderPrepReference(prepSpanish || [], prepItalian || []));

  show('prep');
  window.scrollTo(0, 0);
}

// The reference. Spanish first, since that is the direction you produce in,
// then the four Italian prepositions that actually cause the trouble.
function renderPrepReference(spanish, italian) {
  const wrap = document.createDocumentFragment();

  const a = document.createElement('details');
  a.className = 'mood';
  a.append(el('summary', null, 'Spanish prepositions, and what they cover'));
  for (const p of spanish) {
    const h = el('h3', 'section-label', p.prep);
    a.append(h);
    a.append(el('p', 'muted small conj-note', p.gloss));
    a.append(el('p', 'conj-italian', 'Italian: ' + p.italian));
    const table = el('div', 'pair-table');
    for (const use of p.uses) {
      const [label, es, it, note] = use;
      const row = el('div', 'pair-row');
      row.append(el('span', 'pair-note use-label', label));
      row.append(speakLine(es, 'es', 'pair-es'), speakLine(it, 'it', 'pair-it'));
      if (note) row.append(el('span', 'pair-note', note));
      table.append(row);
    }
    a.append(table);
  }
  wrap.append(a);

  const b = document.createElement('details');
  b.className = 'mood';
  b.append(el('summary', null, 'Italian prepositions, and where each one goes'));
  for (const p of italian) {
    b.append(el('h3', 'section-label', p.prep));
    b.append(el('p', 'conj-warn', p.warning));
    const table = el('div', 'pair-table');
    for (const [label, target, it, es] of p.splits) {
      const row = el('div', 'pair-row split-row');
      const head = el('span', 'pair-note use-label');
      head.append(label + ' → ');
      head.append(el('b', 'split-target', target));
      row.append(head);
      row.append(speakLine(it, 'it', 'pair-it'), speakLine(es, 'es', 'pair-es'));
      table.append(row);
    }
    b.append(table);
  }
  wrap.append(b);
  return wrap;
}

function speakLine(text, which, cls) {
  const e = el('span', cls, text);
  if (canSpeak()) {
    e.classList.add('speakable');
    e.addEventListener('click', () => speak(text, which));
  }
  return e;
}

function renderPrepQuestion() {
  const run = prepState.run;
  const q = run.questions[run.index];
  const body = $('#prep-body');
  body.replaceChildren();
  $('#prep-title').textContent = `${run.index + 1} of ${run.questions.length}`;

  const prompt = el('div', 'prep-prompt');
  prompt.append(el('span', 'prep-sentence', q.prompt));
  const say = speakerButton(q.prompt, q.promptLang);
  if (say) prompt.append(say);
  body.append(prompt);

  const form = el('form', 'drill-form');
  const input = el('input', 'drill-input');
  input.type = 'text';
  input.autocapitalize = 'none';
  input.autocomplete = 'off';
  input.spellcheck = false;
  const go = el('button', 'drill-submit', 'Check');
  go.type = 'submit';
  form.append(input, go);
  body.append(form);

  const feedback = el('p', 'drill-feedback');
  body.append(feedback);

  const submit = () => {
    const verdict = checkAnswer(input.value, q.answer);
    if (verdict === 'wrong') run.wrong++; else run.right++;
    feedback.className = 'drill-feedback ' + verdict;
    feedback.replaceChildren(
      (verdict === 'wrong' ? '✗ ' : '✓ ') + q.answer);
    const s = speakerButton(q.answer, q.answerLang);
    if (s) feedback.append(' ', s);
    if (q.note) body.append(el('p', 'muted small centred', q.note));

    input.disabled = true;
    const next = el('button', 'primary',
                    run.index + 1 < run.questions.length ? 'Next' : 'Finish');
    next.type = 'button';
    next.addEventListener('click', () => {
      run.index++;
      if (run.index < run.questions.length) renderPrepQuestion();
      else {
        $('#prep-title').textContent = 'Done';
        body.replaceChildren(
          el('p', 'drill-score', `${run.right} of ${run.right + run.wrong}`),
          backButton(openPrep, 'Prepositions'));
      }
    });
    body.append(next);
    next.focus();
  };
  form.addEventListener('submit', e => { e.preventDefault(); submit(); });
  input.focus();
}

// ---------- conversations ----------

async function openConversations() {
  const { conversations } = await loadExtras();
  $('#convo-title').textContent = 'Conversations';
  const body = $('#convo-body');
  body.replaceChildren(
    el('p', 'muted small section-intro',
       'Short everyday exchanges, written rather than taken from a corpus. '
       + 'Latin American Spanish, with the Italian underneath.'),
  );

  const list = el('div', 'lesson-list');
  for (const c of conversations) {
    const row = el('button', 'lesson-row');
    row.type = 'button';
    const text = el('span', 'lesson-text');
    text.append(el('b', null, c.title), el('span', 'lesson-summary', c.note));
    row.append(text);
    row.addEventListener('click', () => renderConversation(c));
    list.append(row);
  }
  body.append(list);
  show('convo');
  window.scrollTo(0, 0);
}

function renderConversation(c) {
  $('#convo-title').textContent = c.title;
  const body = $('#convo-body');
  body.replaceChildren();

  if (c.note) body.append(el('p', 'conj-italian', c.note));

  const wrap = el('div', 'convo');
  c.lines.forEach(([es, it, en], i) => {
    const line = el('div', 'convo-line' + (i % 2 ? ' right' : ''));
    const top = el('div', 'convo-es');
    top.append(el('span', null, es));
    const say = speakerButton(es, 'es');
    if (say) top.append(say);
    line.append(top, el('div', 'convo-it', it), el('div', 'convo-en', en));
    wrap.append(line);
  });
  body.append(wrap);

  if (canSpeak()) {
    const all = el('button', 'compare', 'Play the Spanish through');
    all.type = 'button';
    all.addEventListener('click', async () => {
      for (const [es] of c.lines) {
        await speak(es, 'es', { rate: 0.9 });
        await new Promise(r => setTimeout(r, 320));
      }
    });
    const row = el('div', 'compare-row');
    row.append(all);
    body.append(row);
  }
  body.append(backButton(openConversations, 'All conversations'));
  window.scrollTo(0, 0);
}

// ---------- wiring ----------

export function initSections(showView, conjugationData) {
  show = showView;
  conjugations = conjugationData;

  $('#open-grammar').addEventListener('click', openGrammar);
  $('#close-grammar').addEventListener('click', () => show('home'));
  $('#open-drill').addEventListener('click', openDrill);
  $('#close-drill').addEventListener('click', () => show('home'));
  $('#open-prep').addEventListener('click', openPrep);
  $('#close-prep').addEventListener('click', () => show('home'));
  $('#open-convo').addEventListener('click', openConversations);
  $('#close-convo').addEventListener('click', () => show('home'));
}
