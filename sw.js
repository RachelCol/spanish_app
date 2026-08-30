// Hand-written service worker -- no build step, no Workbox.
//
// Everything here is static and versioned by hand: bump CACHE when any listed
// file changes, or the old copy will be served indefinitely. That is the cost
// of skipping a build system, and it is a fair trade for a deck app.

const CACHE = 'spanish-app-v91';

const ASSETS = [
  '.',
  'index.html',
  'app.css',
  'manifest.webmanifest',
  'js/main.js',
  'js/db.js',
  'js/srs.js',
  'js/deck.js',
  'js/session.js',
  'js/speech.js',
  'js/grammar.js',
  'js/drills.js',
  'js/sections.js',
  'data/deck.json',
  'data/sentences.json',
  'data/conjugations.json',
  'data/grammar.json',
  'data/basics.json',
  'data/drill_verbs.json',
  'data/drill_bank.json',
  'data/gender.json',
  'data/prompts.json',
  'icons/icon-192.png',
  'icons/icon-512.png',
];

self.addEventListener('install', e => {
  // `cache: 'reload'` bypasses the browser's HTTP cache. Without it addAll is
  // free to take some files from cache and others from the network, which
  // installs a version that never existed -- new data against old code. That
  // is what put `vosotros dicen` above an empty `ellos`.
  const fresh = ASSETS.map(url => new Request(url, { cache: 'reload' }));
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(fresh))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Cache-first. The deck is static and the point is that a plane works.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  // Scoped to this cache by name. A bare caches.match() searches every cache
  // on the origin, and the lab build is a second app living alongside this
  // one -- close enough that a stray hit would be hard to diagnose.
  e.respondWith(
    caches.open(CACHE).then(c => c.match(e.request)).then(hit => hit || fetch(e.request).then(res => {
      if (res.ok && new URL(e.request.url).origin === location.origin) {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
      }
      return res;
    }).catch(() => caches.open(CACHE).then(c => c.match('index.html'))))
  );
});
