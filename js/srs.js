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

// --- letter grades -------------------------------------------------------
//
// Grade by scheduling distance rather than by past accuracy. The interval is
// the scheduler's own estimate of how long this will stay known, so it answers
// "how well do I know this now" -- whereas a lapse count answers "how much
// trouble did this give me", which is a different question and keeps punishing
// a word long after it has been learned.

export const GRADES = ['A', 'B', 'C', 'D', 'E', 'F'];

const BANDS = [
  ['A', 90, Infinity],
  ['B', 31, 90],
  ['C', 11, 31],
  ['D', 4, 11],
  ['E', 1, 4],
  ['F', 0, 1],
];

export function gradeLetter(item) {
  if (isNew(item)) return null;          // Not Yet Learned
  const d = item.interval;
  for (const [letter, lo, hi] of BANDS) {
    if (d >= lo && d < hi) return letter;
  }
  return 'F';
}

export function gradeRange(letter) {
  const b = BANDS.find(x => x[0] === letter);
  if (!b) return '';
  if (b[2] === Infinity) return '90d+';
  return b[1] === 0 ? 'under 1d' : `${b[1]}\u2013${b[2]}d`;
}
