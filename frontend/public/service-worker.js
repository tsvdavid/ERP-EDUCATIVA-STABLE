const CACHE_NAME = 'eduka360-pwa-v5';

// SOLO cacheamos lo estrictamente necesario para que el navegador considere la app como PWA instalable.
// NO cacheamos JS ni CSS de Vite para evitar conflictos de "dispatcher null" en modo dev.
const MINIMAL_STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(MINIMAL_STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Estrategia de Red Pura (Network Only) para todo lo demás.
// Esto garantiza que NO haya conflictos de cache con React/Vite.
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Si es uno de nuestros activos mínimos, intentar cache-first
  if (MINIMAL_STATIC_ASSETS.includes(url.pathname)) {
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request);
      })
    );
    return;
  }

  // Para TODO lo demás (JS, CSS, API, etc.), ir SIEMPRE a la red.
  // Esto evita el error de "resolveDispatcher() is null".
  return; 
});
