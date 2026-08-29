// Builds the review queue.
//
// Two phases. While cards are due today, three of them to every new card, so
// the backlog always shrinks faster than it grows. Once nothing is due that
// job is done, and it alternates new cards with whatever falls due soonest --
// working ahead rather than grinding.

import { isNew, isDue, gradeLetter } from './srs.js';

const DUE_PER_NEW = 3;

export function buildQueue(items, settings, now = Date.now()) {
  const size = settings.sessionSize;

  const fresh = items.filter(isNew)
    .sort((a, b) => b.card.zipf - a.card.zipf);          // most frequent first

  // Studying new cards deliberately: no ratio, no interleaving. `new` here
  // means never shown, not merely never graded -- looking at a card and
  // leaving it ungraded still counts as having met it.
  if (settings.newOnly) return fresh.filter(i => !i.firstSeen).slice(0, size);

  const seen = items.filter(i => !isNew(i));
  const due = seen.filter(i => isDue(i, now)).sort((a, b) => a.due - b.due);
  const upcoming = seen.filter(i => !isDue(i, now)).sort((a, b) => a.due - b.due);

  // Reviewing one grade at a time is a drill, not the daily queue: due first,
  // then whatever comes due soonest.
  if (settings.grades && settings.grades.length) {
    const want = new Set(settings.grades);
    const match = i => want.has(gradeLetter(i));
    return [...due.filter(match), ...upcoming.filter(match)].slice(0, size);
  }

  const out = [];
  let d = 0, f = 0, u = 0;

  // Phase one: clear the backlog, three due to every new.
  for (let step = 0; out.length < size && d < due.length; step++) {
    const takeNew = step % (DUE_PER_NEW + 1) === DUE_PER_NEW && f < fresh.length;
    out.push(takeNew ? fresh[f++] : due[d++]);
  }

  // Phase two: nothing overdue left, so alternate one for one.
  let takeNew = true;
  while (out.length < size) {
    if (takeNew && f < fresh.length) out.push(fresh[f++]);
    else if (u < upcoming.length) out.push(upcoming[u++]);
    else if (f < fresh.length) out.push(fresh[f++]);
    else break;
    takeNew = !takeNew;
  }
  return out;
}

export function counts(items, now = Date.now()) {
  let due = 0, fresh = 0, learned = 0;
  for (const i of items) {
    if (isNew(i)) fresh++;
    else {
      learned++;
      if (isDue(i, now)) due++;
    }
  }
  return { due, new: fresh, learned, total: items.length };
}

// Distribution across the letter bands, for the progress view. A null from
// gradeLetter means the card has never been reviewed.
export function gradeBreakdown(items) {
  const out = { New: 0, A: 0, B: 0, C: 0, D: 0, E: 0, F: 0 };
  for (const i of items) {
    const g = gradeLetter(i);
    out[g === null ? 'New' : g]++;
  }
  return out;
}
