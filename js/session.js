// Builds the review queue.
//
// The day's plan is every card due today with twenty new cards spread evenly
// through it. That ratio is the point: with sixty due you meet a new card
// every fourth card, with twenty due you alternate. Either way finishing the
// plan clears the backlog, so the due pile cannot quietly outrun you.
//
// Once the plan is done, further reviewing alternates new cards with whatever
// falls due soonest. Working ahead beats grinding, and it keeps some variety
// in a session that would otherwise be all new words.

import { isNew, isDue, gradeLetter } from './srs.js';

export const NEW_PER_DAY = 20;

// Spreads two lists evenly in proportion to their lengths, rather than
// alternating -- 60 due and 20 new should come out 3:1, not 1:1 then a tail.
function interleave(a, b) {
  const out = [];
  const total = a.length + b.length;
  let i = 0, j = 0;
  for (let n = 0; n < total; n++) {
    const aShare = a.length ? i / a.length : 1;
    const bShare = b.length ? j / b.length : 1;
    if (j < b.length && (i >= a.length || bShare <= aShare)) out.push(b[j++]);
    else out.push(a[i++]);
  }
  return out;
}

function alternate(a, b) {
  const out = [];
  for (let n = 0; n < a.length + b.length; n++) {
    const pick = n % 2 === 0 ? a : b;
    const other = n % 2 === 0 ? b : a;
    if (pick.length) out.push(pick.shift());
    else if (other.length) out.push(other.shift());
  }
  return out;
}

export function buildQueue(items, settings, now = Date.now(), newToday = 0) {
  const size = settings.sessionSize;

  const fresh = items.filter(isNew)
    .sort((a, b) => b.card.zipf - a.card.zipf);          // most frequent first

  // Studying new cards deliberately: no ratio, no cap.
  if (settings.newOnly) return fresh.slice(0, size);

  const seen = items.filter(i => !isNew(i));
  const due = seen.filter(i => isDue(i, now)).sort((a, b) => a.due - b.due);
  const upcoming = seen.filter(i => !isDue(i, now)).sort((a, b) => a.due - b.due);

  // Reviewing one grade at a time is a drill, not the daily plan: due first,
  // then whatever comes due soonest.
  if (settings.grades && settings.grades.length) {
    const want = new Set(settings.grades);
    const match = i => want.has(gradeLetter(i));
    return [...due.filter(match), ...upcoming.filter(match)].slice(0, size);
  }

  const budget = Math.max(0, NEW_PER_DAY - newToday);
  const plan = interleave(due, fresh.slice(0, budget));
  if (plan.length >= size) return plan.slice(0, size);

  // Past the plan: half new, half nearest-due.
  const tail = alternate(fresh.slice(budget), [...upcoming]);
  return [...plan, ...tail].slice(0, size);
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

// Distribution across the letter bands, for the progress view. `null` from
// gradeLetter means the card has never been reviewed.
export function gradeBreakdown(items) {
  const out = { New: 0, A: 0, B: 0, C: 0, D: 0, E: 0, F: 0 };
  for (const i of items) {
    const g = gradeLetter(i);
    out[g === null ? 'New' : g]++;
  }
  return out;
}
