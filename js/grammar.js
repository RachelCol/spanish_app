// The grammar section: English explanations of what Italian gets wrong about
// Spanish. Self-contained -- it shares nothing with the flashcard code beyond
// the view-switching convention and the speech module.

import { speak, available as canSpeak } from './speech.js';

let cache = null;

export async function loadGrammar() {
  if (cache) return cache;
  const res = await fetch('data/grammar.json');
  cache = res.ok ? await res.json() : [];
  return cache;
}

function speakable(text, which, cls) {
  const el = document.createElement('span');
  el.className = cls;
  el.textContent = text;
  if (canSpeak()) {
    el.classList.add('speakable');
    el.addEventListener('click', () => speak(text, which));
  }
  return el;
}

// The index: one row per lesson, with its one-line summary.
export function renderIndex(lessons, onOpen) {
  const list = document.createElement('div');
  list.className = 'lesson-list';
  lessons.forEach((lesson, i) => {
    const row = document.createElement('button');
    row.type = 'button';
    row.className = 'lesson-row';

    const n = document.createElement('span');
    n.className = 'lesson-num';
    n.textContent = String(i + 1);

    const text = document.createElement('span');
    text.className = 'lesson-text';
    const t = document.createElement('b');
    t.textContent = lesson.title;
    const s = document.createElement('span');
    s.className = 'lesson-summary';
    s.textContent = lesson.summary;
    text.append(t, s);

    row.append(n, text);
    row.addEventListener('click', () => onOpen(lesson));
    list.append(row);
  });
  return list;
}

// **bold** marks the word being taught; *italic* marks a form that is wrong,
// which several lessons rely on to show what not to say. Without the second,
// `*soy ido*` rendered with its asterisks showing.
function inline(text) {
  const out = [];
  for (const chunk of text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/)) {
    if (!chunk) continue;
    if (chunk.startsWith('**') && chunk.endsWith('**')) {
      const b = document.createElement('b');
      b.textContent = chunk.slice(2, -2);
      out.push(b);
    } else if (chunk.startsWith('*') && chunk.endsWith('*') && chunk.length > 2) {
      const i = document.createElement('i');
      i.textContent = chunk.slice(1, -1);
      out.push(i);
    } else {
      out.push(chunk);
    }
  }
  return out;
}

export function renderLesson(lesson) {
  const frag = document.createDocumentFragment();

  for (const para of lesson.body) {
    const p = document.createElement('p');
    p.className = 'lesson-para';
    p.append(...inline(para));
    frag.append(p);
  }

  const table = document.createElement('div');
  table.className = 'pair-table';
  for (const [it, es, note] of lesson.pairs) {
    const row = document.createElement('div');
    row.className = 'pair-row';
    row.append(speakable(it, 'it', 'pair-it'), speakable(es, 'es', 'pair-es'));
    if (note) {
      const n = document.createElement('span');
      n.className = 'pair-note';
      n.textContent = note;
      row.append(n);
    }
    table.append(row);
  }
  frag.append(table);

  if (lesson.watch) {
    const w = document.createElement('p');
    w.className = 'conj-warn';
    w.append(...inline(lesson.watch));
    frag.append(w);
  }
  return frag;
}
