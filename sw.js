// Service worker: sajt radi i bez interneta, sa poslednjim učitanim vestima.
// Uvek prvo pita mrežu (da vesti budu sveže), a keš koristi samo kad mreže nema.
// Isti worker prima i push obaveštenja (OneSignal); ako se njihov kod ne učita, sajt i dalje radi.
try { importScripts("https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js"); } catch {}

const CACHE = "pratimo-v2";
const SHELL = ["./", "assets/stil.css?v=9", "assets/ikona-64.png?v=2", "assets/ikona-192.png?v=2", "manifest.webmanifest", "data/podaci.json"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  e.respondWith(
    fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req, { ignoreVary: true })
      .then(hit => hit || (req.mode === "navigate" ? caches.match("./") : Response.error())))
  );
});
