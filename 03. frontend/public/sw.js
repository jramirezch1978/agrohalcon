// AllpaShift service worker: la app funciona sin internet.
// - Navegación: red primero, si falla usa index.html en caché.
// - Archivos estáticos (JS, CSS, fuentes, íconos): caché primero.
// - API y mapas: siempre red (la última recomendación se guarda en el dispositivo).
// - Al instalarse guarda TODO el build (precache.json lo genera vite.config.ts): cualquier pantalla abre sin internet.
const CACHE = 'allpashift-v3'
const BASE = ['./', './index.html', './manifest.webmanifest', './favicon.svg']

/** Lista de archivos del build; si falta (modo dev), solo la base. Un archivo que falla no impide instalar. */
async function precachear(c) {
  await c.addAll(BASE)
  try {
    const r = await fetch('./precache.json', { cache: 'no-store' })
    if (!r.ok) return
    const archivos = await r.json()
    await Promise.allSettled(archivos.map((f) => c.add(f)))
  } catch {
    /* sin lista: se guardan al usarse, como antes */
  }
}

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then(precachear).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (e) => {
  const req = e.request
  if (req.method !== 'GET') return
  const url = new URL(req.url)
  if (url.origin !== location.origin) return // API, mapas y buscador: sin caché aquí

  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req)
        .then((res) => {
          const copia = res.clone()
          caches.open(CACHE).then((c) => c.put('./index.html', copia))
          return res
        })
        .catch(() => caches.match('./index.html')),
    )
    return
  }

  e.respondWith(
    caches.match(req).then(
      (hit) =>
        hit ||
        fetch(req).then((res) => {
          if (res.ok) {
            const copia = res.clone()
            caches.open(CACHE).then((c) => c.put(req, copia))
          }
          return res
        }),
    ),
  )
})
