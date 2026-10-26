/* Service worker: o check-in da receção e a app do sócio abrem mesmo sem rede.
 * - Páginas de /gestao e /app: rede primeiro, cópia em cache se falhar.
 * - Ficheiros estáticos do Next.js (/_next/static): cache primeiro (têm hash no nome).
 * - A API nunca é guardada em cache (a fila offline do check-in trata disso). */
const CACHE = "ginasio-v1";

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((chaves) => Promise.all(chaves.filter((c) => c !== CACHE).map((c) => caches.delete(c))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin || url.pathname.startsWith("/api/")) return;

  if (url.pathname.startsWith("/_next/static/")) {
    event.respondWith(
      caches.match(request).then(
        (guardado) =>
          guardado ||
          fetch(request).then((res) => {
            const copia = res.clone();
            caches.open(CACHE).then((c) => c.put(request, copia));
            return res;
          }),
      ),
    );
    return;
  }

  const area = url.pathname.startsWith("/gestao") || url.pathname.startsWith("/app");
  if (area && request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((res) => {
          if (res.ok) {
            const copia = res.clone();
            caches.open(CACHE).then((c) => c.put(request, copia));
          }
          return res;
        })
        .catch(() => caches.match(request).then((r) => r || caches.match("/gestao/checkin"))),
    );
  }
});
