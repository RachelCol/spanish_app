// SM-2, with one deliberate departure: the first interval depends on which
// bucket the card is in. A pair like `problema/problema` does not deserve the
// same introduction schedule as `dinero/soldi`, and we already know which is
// which, so the deck taxonomy earns its keep here rather than only in the UI.

export const AGAIN = 0, HARD = 1, GOOD = 2, EASY = 3;

const MIN_EASE = 1.3;
const MAX_EASE = 3.0;
const DAY = 86400000;

// Days until a card is first seen again after a passing grade.
const FIRST_INTERVAL = {
  identical: 4,
  near: 2,
  shifted: 1,
  distinct: 1,
};

export function newItem(key, cardId, direction, bucket) {
  return {
    key,
    cardId,
    direction,
    bucket,
    due: 0,          // 0 = never seen, treated as due now
    interval: 0,     // days
    ease: 2.5,
    reps: 0,
    lapses: 0,
    last: null,
  };
}

export function isNew(item) {
  return item.reps === 0;
}

export function isDue(item, now = Date.now()) {
  return item.due <= now;
}

// Returns a new item; does not mutate the input.
export function grade(item, g, now = Date.now()) {
  const next = { ...item, last: now };
  const first = FIRST_INTERVAL[item.bucket] ?? 1;

  if (g === AGAIN) {
    next.lapses += 1;
    next.reps += 1;
    next.ease = clamp(item.ease - 0.2);
    next.interval = 0;
    // Same session, after a short delay rather than a day.
    next.due = now + 60000;
    return next;
  }

  next.reps += 1;

  if (item.reps === 0 || item.interval === 0) {
    // Introduction. Hard shortens it, easy stretches it.
    next.interval = g === HARD ? Math.max(1, first - 1)
                  : g === EASY ? first * 2
                  : first;
  } else {
    const factor = g === HARD ? 1.2
                 : g === EASY ? item.ease * 1.3
                 : item.ease;
    next.interval = Math.max(1, Math.round(item.interval * factor));
  }

  next.ease = clamp(item.ease + (g === HARD ? -0.15 : g === EASY ? 0.15 : 0));
  next.due = now + next.interval * DAY;
  return next;
}

function clamp(e) {
  return Math.min(MAX_EASE, Math.max(MIN_EASE, Math.round(e * 100) / 100));
}

export function intervalLabel(item, g) {
  const next = grade(item, g);
  if (next.interval === 0) return '<1m';
  if (next.interval === 1) return '1d';
  if (next.interval < 30) return next.interval + 'd';
  if (next.interval < 365) return Math.round(next.interval / 30) + 'mo';
  return (next.interval / 365).toFixed(1) + 'y';
}
