// Wiring for the grammar and drill sections.
//
// Everything here is additive. It shares the view switcher, the speech module
// and the conjugation tables with the flashcards, and touches nothing else, so
// a fault in this file cannot reach the deck, the scheduler or the history.

import { loadGrammar, renderIndex, renderLesson } from './grammar.js';
import {
  DRILL_TENSES, loadDrillVerbs, checkAnswer, buildVerbQuestions, speakerButton,
} from './drills.js';
import { speak, available as canSpeak } from './speech.js';

const $ = sel => document.querySelector(sel);
const VERB_QUESTIONS = 20;
const GAP_QUESTIONS = 15;
const NO_ARTICLE = '—';

let show;
let conjugations = null;

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

function backButton(fn, label) {
  const b = el('button', 'compare back-link', '← ' + label);
  b.type = 'button';
  b.addEventListener('click', fn);
  const wrap = el('div', 'compare-row');
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

function shuffle(a) {
  const out = a.slice();
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

// ---------- comparisons ----------

async function openGrammar() {
  const lessons = await loadGrammar();
  $('#grammar-title').textContent = 'Comparisons';
  const body = $('#grammar-body');
  body.replaceChildren(
    el('p', 'muted small section-intro',
       'What Italian gets wrong about Spanish, in rough order of how much '
       + 'trouble it causes.'),
    renderIndex(lessons, lesson => {
      $('#grammar-title').textContent = lesson.title;
      body.replaceChildren(renderLesson(lesson), backButton(openGrammar, 'All comparisons'));
      window.scrollTo(0, 0);
    }),
  );
  show('grammar');
  window.scrollTo(0, 0);
}

// ---------- basics ----------

let basicsCache = null;

async function loadBasics() {
  if (basicsCache) return basicsCache;
  const res = await fetch('data/basics.json');
  basicsCache = res.ok ? await res.json() : [];
  return basicsCache;
}

async function openBasics() {
  const sections = await loadBasics();
  $('#basics-title').textContent = 'Basics';
  const body = $('#basics-body');
  body.replaceChildren(
    el('p', 'muted small section-intro',
       'How Spanish works, in English. Not comparative — this is the machinery, '
       + 'for looking things up.'),
  );
  const list = el('div', 'lesson-list');
  sections.forEach((section, i) => {
    const row = el('button', 'lesson-row');
    row.type = 'button';
    row.append(el('span', 'lesson-num', String(i + 1)));
    const text = el('span', 'lesson-text');
    text.append(el('b', null, section.title),
                el('span', 'lesson-summary', section.summary));
    row.append(text);
    row.addEventListener('click', () => renderBasicsSection(section));
    list.append(row);
  });
  body.append(list);
  show('basics');
  window.scrollTo(0, 0);
}

function renderBasicsSection(section) {
  $('#basics-title').textContent = section.title;
  const body = $('#basics-body');
  body.replaceChildren();

  for (const para of section.body) {
    const p = el('p', 'lesson-para');
    para.split(/(\*\*[^*]+\*\*)/).forEach(chunk => {
      if (chunk.startsWith('**') && chunk.endsWith('**')) {
        p.append(el('b', null, chunk.slice(2, -2)));
      } else if (chunk) {
        p.append(chunk);
      }
    });
    body.append(p);
  }

  if (section.examples && section.examples.length) {
    const table = el('div', 'pair-table');
    for (const [es, en, note] of section.examples) {
      const row = el('div', 'pair-row');
      row.append(speakLine(es, 'es', 'pair-es'), el('span', 'pair-it', en));
      if (note) row.append(el('span', 'pair-note', note));
      table.append(row);
    }
    body.append(table);
  }

  if (section.prepSpanish) body.append(renderPrepReference(section));
  body.append(backButton(openBasics, 'All basics'));
  window.scrollTo(0, 0);
}

// Spanish first, since that is the direction you produce in, then the four
// Italian prepositions whose jobs get shared out.
function renderPrepReference(section) {
  const wrap = document.createDocumentFragment();

  const a = document.createElement('details');
  a.className = 'mood';
  a.append(el('summary', null, 'Spanish prepositions, and what they cover'));
  for (const p of section.prepSpanish) {
    a.append(el('h3', 'section-label', p.prep));
    a.append(el('p', 'muted small conj-note', p.gloss));
    a.append(el('p', 'conj-italian', 'Italian: ' + p.italian));
    const table = el('div', 'pair-table');
    for (const [label, es, it, note] of p.uses) {
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
  for (const p of section.prepItalian) {
    b.append(el('h3', 'section-label', p.prep));
    b.append(el('p', 'conj-warn', p.warning));
    const table = el('div', 'pair-table');
    for (const [label, target, it, es] of p.splits) {
      const row = el('div', 'pair-row split-row');
      const head = el('span', 'pair-note use-label');
      head.append(label + ' → ');
      head.append(el('b', 'split-target', target));
      row.append(head, speakLine(it, 'it', 'pair-it'), speakLine(es, 'es', 'pair-es'));
      table.append(row);
    }
    b.append(table);
  }
  wrap.append(b);
  return wrap;
}

// ---------- conjugation drill ----------

const drillState = { verbs: new Set(), tenses: new Set(['present']), run: null };

async function openDrill() {
  const verbs = await loadDrillVerbs();
  if (!drillState.verbs.size) verbs.slice(0, 10).forEach(v => drillState.verbs.add(v.es));

  $('#drill-title').textContent = 'Verb drill';
  const body = $('#drill-body');
  body.replaceChildren(
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

function startDrill() {
  if (!drillState.verbs.size || !drillState.tenses.size) return;
  const questions = buildVerbQuestions(
    conjugations, [...drillState.verbs], [...drillState.tenses],
    conjugations.pronouns, VERB_QUESTIONS);
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
  const paradigm = el('div', 'drill-paradigm hidden');
  body.append(feedback, paradigm);
  body.append(el('p', 'muted small centred', `${run.right} right · ${run.wrong} wrong`));

  const submit = () => {
    const verdict = checkAnswer(input.value, q.answer);
    if (verdict === 'wrong') run.wrong++; else run.right++;

    // The mark belongs on what you wrote, not on the answer. Seeing "✗ tiene"
    // reads as though the correct form were the mistake.
    const typed = input.value.trim() || '—';
    feedback.replaceChildren();
    feedback.className = 'drill-feedback ' + verdict;
    feedback.append(el('span', 'typed-answer',
                       (verdict === 'wrong' ? '✗ ' : '✓ ') + typed));

    // The right form, in green, whenever it is not exactly what was typed.
    if (verdict !== 'right') {
      const right = el('p', 'correct-answer');
      right.append(el('span', 'correct-word', q.answer));
      if (verdict === 'accents') right.append(el('span', 'correct-note', 'watch the accent'));
      const say = speakerButton(q.answer, 'es');
      if (say) right.append(say);
      feedback.after(right);
    } else {
      const say = speakerButton(q.answer, 'es');
      if (say) feedback.append(' ', say);
    }

    // The paradigm every time, right or wrong. Getting one right is a good
    // moment to see the other five, and it costs nothing to look.
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
  $('#drill-title').textContent = 'Drill complete';
  const body = $('#drill-body');
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

// ---------- gap-fill drills: prepositions and articles ----------
//
// One component, two banks. Every sentence is an attested Tatoeba pair with
// the word cut out of it, so the right answer is what a speaker actually said.

let bankCache = null;

async function loadBank() {
  if (bankCache) return bankCache;
  const res = await fetch('data/drill_bank.json');
  bankCache = res.ok ? await res.json() : { prepositions: [], articles: [] };
  return bankCache;
}

const gapRuns = {};

const GAP_CONFIG = {
  prepositions: {
    view: 'prep', title: 'Prepositions',
    intro: 'The Italian sentence, then the Spanish with the preposition removed. '
         + 'Sentences come from Tatoeba, not from anyone’s imagination.',
  },
  articles: {
    view: 'articles', title: 'Articles',
    intro: 'The Italian sentence, then the Spanish with the article removed. '
         + 'Sometimes the answer is that Spanish uses none — Italian says '
         + '"il mio libro", Spanish says "mi libro".',
  },
};

function openGap(kind) {
  return async () => {
    const bank = await loadBank();
    const cfg = GAP_CONFIG[kind];
    const items = bank[kind] || [];
    $(`#${cfg.view}-title`).textContent = cfg.title;
    const body = $(`#${cfg.view}-body`);
    body.replaceChildren(el('p', 'muted small section-intro', cfg.intro));

    const start = el('button', 'primary', 'Start');
    start.type = 'button';
    start.addEventListener('click', () => {
      gapRuns[kind] = {
        questions: shuffle(items).slice(0, GAP_QUESTIONS),
        index: 0, right: 0, wrong: 0,
      };
      renderGapQuestion(kind);
    });
    body.append(start,
                el('p', 'muted small centred', `${items.length} sentences in the bank`));
    show(cfg.view);
    window.scrollTo(0, 0);
  };
}

function renderGapQuestion(kind) {
  const cfg = GAP_CONFIG[kind];
  const run = gapRuns[kind];
  const q = run.questions[run.index];
  const body = $(`#${cfg.view}-body`);
  body.replaceChildren();
  $(`#${cfg.view}-title`).textContent = `${run.index + 1} of ${run.questions.length}`;

  const italian = el('div', 'gap-italian');
  italian.append(el('span', null, q.italian));
  const sayIt = speakerButton(q.italian, 'it');
  if (sayIt) italian.append(sayIt);
  body.append(italian);

  // The gap is drawn as a slot rather than left as underscores, so it reads as
  // something to be filled rather than as punctuation.
  const spanish = el('div', 'gap-spanish');
  q.gapped.split('___').forEach((chunk, i) => {
    if (i) spanish.append(el('span', 'gap-slot', '     '));
    spanish.append(chunk);
  });
  body.append(spanish);

  const choices = el('div', 'gap-choices');
  const feedback = el('p', 'drill-feedback');

  for (const option of q.options) {
    const b = el('button', 'gap-option', option);
    b.type = 'button';
    b.addEventListener('click', () => {
      if (choices.classList.contains('answered')) return;
      choices.classList.add('answered');

      const right = option === q.answer;
      if (right) run.right++; else run.wrong++;
      b.classList.add(right ? 'chosen-right' : 'chosen-wrong');
      if (!right) {
        [...choices.children].find(c => c.textContent === q.answer)
          ?.classList.add('is-answer');
      }

      feedback.className = 'drill-feedback ' + (right ? 'right' : 'wrong');
      feedback.replaceChildren(right ? '✓ Correct' : `✗ ${q.answer}`);

      // The whole sentence, so the gap is seen in place.
      const full = el('p', 'gap-full');
      full.append(q.full);
      const say = speakerButton(q.full, 'es');
      if (say) full.append(' ', say);
      body.append(full);

      const next = el('button', 'primary',
                      run.index + 1 < run.questions.length ? 'Next' : 'Finish');
      next.type = 'button';
      next.addEventListener('click', () => {
        run.index++;
        if (run.index < run.questions.length) renderGapQuestion(kind);
        else {
          $(`#${cfg.view}-title`).textContent = 'Done';
          body.replaceChildren(
            el('p', 'drill-score', `${run.right} of ${run.right + run.wrong}`),
            backButton(openGap(kind), cfg.title));
        }
      });
      body.append(next);
      next.focus();
    });
    choices.append(b);
  }
  body.append(choices, feedback);
  body.append(el('p', 'muted small centred', `${run.right} right · ${run.wrong} wrong`));
}

// ---------- wiring ----------

export function initSections(showView, conjugationData) {
  show = showView;
  conjugations = conjugationData;

  $('#open-grammar').addEventListener('click', openGrammar);
  $('#close-grammar').addEventListener('click', () => show('home'));
  $('#open-basics').addEventListener('click', openBasics);
  $('#close-basics').addEventListener('click', () => show('home'));
  $('#open-drill').addEventListener('click', openDrill);
  $('#close-drill').addEventListener('click', () => show('home'));
  $('#open-prep').addEventListener('click', openGap('prepositions'));
  $('#close-prep').addEventListener('click', () => show('home'));
  $('#open-articles').addEventListener('click', openGap('articles'));
  $('#close-articles').addEventListener('click', () => show('home'));
}
