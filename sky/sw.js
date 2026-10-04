// 頭頂星空 service worker: works offline after the first visit.
const VERSION = 'v5-2026-10-04';
const CORE_CACHE = 'toudingxingkong-core-' + VERSION;
const FONT_CACHE = 'toudingxingkong-fonts';
const CORE = [
  './',
  './index.html',
  './astronomy.browser.min.js',
  './manifest.webmanifest',
  './icon-192.png',
  './icon-512.png',
  './apple-touch-icon.png',
  './favicon-32.png',
  './privacy.html',
  './licenses.html'
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CORE_CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith('toudingxingkong-') && k !== CORE_CACHE && k !== FONT_CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  if (url.origin === self.location.origin) {
    if (req.mode === 'navigate') {
      // network first so updates arrive; fall back to the cached copy when offline.
      // Only the app itself is stored as ./index.html (privacy.html / licenses.html keep their own entries).
      const isApp = /\/(index\.html)?$/.test(url.pathname);
      const key = isApp ? './index.html' : req;
      const cached = () => caches.match(key, { ignoreSearch: true }).then((hit) => hit || caches.match('./index.html'));
      // download the whole page before using it, and keep the cache update alive even when the cached copy is shown
      const net = fetch(req).then((res) => {
        if (!res.ok) return res;
        return res.arrayBuffer().then((buf) => {
          const fresh = new Response(buf, { status: res.status, statusText: res.statusText, headers: res.headers });
          return caches.open(CORE_CACHE).then((c) => c.put(key, fresh.clone())).then(() => fresh, () => fresh);
        });
      });
      event.waitUntil(net.catch(() => {}));
      event.respondWith(new Promise((resolve) => {
        let done = false;
        const use = (r) => { if (!done && r) { done = true; resolve(r); } };
        // weak signal (e.g. on a mountain): after 4 s show the cached copy; the new version is used next time
        const timer = setTimeout(() => cached().then(use), 4000);
        net
          // server error (e.g. GitHub Pages outage): show the cached copy instead of an error page
          .then((res) => (res.status >= 500 ? cached().then((hit) => hit || res) : res))
          .catch(() => cached().then((hit) => hit || Response.error()))
          .then((r) => { clearTimeout(timer); use(r); });
      }));
      return;
    }
    event.respondWith(
      caches.match(req).then((hit) => hit || fetch(req).then((res) => {
        if (res.ok) { const copy = res.clone(); caches.open(CORE_CACHE).then((c) => c.put(req, copy)); }
        return res;
      }))
    );
    return;
  }

  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    event.respondWith(
      caches.open(FONT_CACHE).then((cache) => cache.match(req).then((hit) => {
        const net = fetch(req).then((res) => { cache.put(req, res.clone()); return res; }).catch(() => hit);
        return hit || net;
      }))
    );
  }
});
