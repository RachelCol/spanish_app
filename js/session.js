// Builds the review queue.
//
// Due cards come first and in due order, oldest first, because a card that has
// been waiting three days is closer to being forgotten than one due this
// morning. New cards are then mixed in up to the daily cap.

import { isNew, isDue } from './srs.js';

export function buildQueue(items, settings, now = Date.now()) {
  const due = items
    .filter(i => !isNew(i) && isDue(i, now))
    .sort((a, b) => a.due - b.due);

  const fresh = items
    .filter(isNew)
    .sort((a, b) => b.card.zipf - a.card.zipf)   // most frequent words first
    .slice(0, settings.newPerDay);

  // Interleave rather than front-loading either: a wall of new cards is
  // discouraging, and a wall of reviews delays anything new until the end.
  const queue = [];
  const ratio = fresh.length ? Math.max(1, Math.floor(due.length / fresh.length)) : Infinity;
  let d = 0, f = 0;
  while (d < due.length || f < fresh.length) {
    for (let k = 0; k < ratio && d < due.length; k++) queue.push(due[d++]);
    if (f < fresh.length) queue.push(fresh[f++]);
  }
  return queue.slice(0, settings.maxSession);
}

export function counts(items, now = Date.now()) {
  let dueCount = 0, newCount = 0, learned = 0;
  for (const i of items) {
    if (isNew(i)) newCount++;
    else {
      learned++;
      if (isDue(i, now)) dueCount++;
    }
  }
  return { due: dueCount, new: newCount, learned, total: items.length };
}
