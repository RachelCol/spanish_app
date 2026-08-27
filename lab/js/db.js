// IndexedDB, not localStorage. Two reasons: the quota is far larger, and it
// can be marked persistent, which matters because iOS will evict
// script-writable storage from a home-screen app that goes unused. Losing SRS
// state is the one failure this app can't recover from, so export/import in
// settings.js is the real backstop.

const DB_NAME = 'spanish_app_lab';
const DB_VERSION = 2;

let dbp = null;

function open() {
  if (dbp) return dbp;
  dbp = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains('progress')) {
        db.createObjectStore('progress', { keyPath: 'key' });
      }
      if (!db.objectStoreNames.contains('meta')) {
        db.createObjectStore('meta', { keyPath: 'key' });
      }
      // One row per grade pressed, ever. The progress view needs history, and
      // history cannot be reconstructed after the fact -- an aggregate says
      // where a card is now, never how it got there.
      if (!db.objectStoreNames.contains('reviews')) {
        const s = db.createObjectStore('reviews', { keyPath: 'id', autoIncrement: true });
        s.createIndex('ts', 'ts');
      }
    };
    // Another tab holding an older version blocks the upgrade, and the open
    // request then never settles -- which looks like a blank, broken app.
    req.onblocked = () => reject(new Error('DB_BLOCKED'));
    req.onsuccess = () => {
      const db = req.result;
      // Symmetrically: if a newer tab wants to upgrade, get out of its way
      // rather than being the tab that blocks it.
      db.onversionchange = () => db.close();
      resolve(db);
    };
    req.onerror = () => reject(req.error);
  });
  return dbp;
}

function tx(store, mode, fn) {
  return open().then(db => new Promise((resolve, reject) => {
    const t = db.transaction(store, mode);
    const s = t.objectStore(store);
    const out = fn(s);
    t.oncomplete = () => resolve(out && out.result !== undefined ? out.result : out);
    t.onerror = () => reject(t.error);
  }));
}

export const db = {
  allProgress() {
    return tx('progress', 'readonly', s => s.getAll());
  },
  putProgress(rec) {
    return tx('progress', 'readwrite', s => s.put(rec));
  },
  putMany(recs) {
    return tx('progress', 'readwrite', s => { recs.forEach(r => s.put(r)); });
  },
  clearProgress() {
    return tx('progress', 'readwrite', s => s.clear());
  },
  logReview(rec) {
    return tx('reviews', 'readwrite', s => s.add(rec));
  },
  allReviews() {
    return tx('reviews', 'readonly', s => s.getAll());
  },
  reviewsSince(ts) {
    return tx('reviews', 'readonly', s => s.index('ts').getAll(IDBKeyRange.lowerBound(ts)));
  },
  putReviews(rows) {
    return tx('reviews', 'readwrite', s => { rows.forEach(r => s.put(r)); });
  },
  clearReviews() {
    return tx('reviews', 'readwrite', s => s.clear());
  },
  getMeta(key) {
    return tx('meta', 'readonly', s => s.get(key)).then(r => (r ? r.value : undefined));
  },
  setMeta(key, value) {
    return tx('meta', 'readwrite', s => s.put({ key, value }));
  },
};

// Ask the browser not to evict us. Chrome grants this silently for installed
// apps; Safari ignores it. Best-effort, so failure is not an error.
export async function requestPersistence() {
  try {
    if (navigator.storage && navigator.storage.persist) {
      return await navigator.storage.persist();
    }
  } catch (_) { /* not supported */ }
  return false;
}
