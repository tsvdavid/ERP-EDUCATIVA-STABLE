const CACHE_NAME = 'eduka360-cache-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png'
];

// Rutas que NUNCA deben cachearse (Seguridad y Dinamismo)
const EXCLUDED_PATHS = [
  '/admin',
  '/api',
  '/login',
  '/logout',
  '/accounts',
  '/django-static' // Si usas el admin de django directamente
];

// 1. Instalación: Cachear activos básicos del shell
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Instalando y precacheando activos estáticos');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// 2. Activación: Limpieza de caches antiguos
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activado');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Borrando cache antiguo:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// 3. Intercepción de peticiones (Fetch)
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Regla de Seguridad 1: Solo interceptar peticiones del mismo origen
  if (url.origin !== self.location.origin) return;

  // Regla de Seguridad 2: Excluir rutas sensibles de cualquier cache
  if (EXCLUDED_PATHS.some(path => url.pathname.startsWith(path))) {
    // console.log('[Service Worker] Bypass cache para ruta protegida:', url.pathname);
    return;
  }

  // Regla de Seguridad 3: Solo cachear métodos GET
  if (event.request.method !== 'GET') return;

  // Estrategia para HTML (Navegación): Network First
  // Esto asegura que si hay sesión o cambios, se vean de inmediato.
  if (event.request.mode === 'navigate' || event.request.headers.get('accept').includes('text/html')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Si la respuesta es exitosa, guardarla en cache para offline
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
          }
          return response;
        })
        .catch(() => {
          // Si falla (offline), intentar servir desde cache
          return caches.match(event.request);
        })
    );
    return;
  }

  // Estrategia para Activos Estáticos (JS, CSS, Imágenes): Cache First
  const isStaticAsset = /\.(js|css|png|jpg|jpeg|svg|gif|woff2?)$/.test(url.pathname);
  if (isStaticAsset) {
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request).then((networkResponse) => {
          if (networkResponse.ok) {
            const copy = networkResponse.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
          }
          return networkResponse;
        });
      })
    );
    return;
  }

  // Por defecto: Network only para todo lo demás (APIs, etc.)
});
