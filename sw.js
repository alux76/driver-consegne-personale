const CACHE_NAME = 'driver-dashboard-v1';

// Risorse da cache all'installazione
const urlsToCache = [
  '/',
  '/manifest_driver.json',
  '/static/icon-72.png',
  '/static/icon-96.png',
  '/static/icon-128.png',
  '/static/icon-144.png',
  '/static/icon-152.png',
  '/static/icon-192.png',
  '/static/icon-256.png',
  '/static/icon-512.png'
];

// Installazione service worker
self.addEventListener('install', event => {
  console.log('Service Worker: Installazione');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Cache aperta');
        return cache.addAll(urlsToCache);
      })
      .catch(err => console.log('Cache fallita:', err))
  );
  self.skipWaiting();
});

// Attivazione service worker
self.addEventListener('activate', event => {
  console.log('Service Worker: Attivato');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cache => {
          if (cache !== CACHE_NAME) {
            console.log('Service Worker: Cache vecchia rimossa', cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Fetch event con fallback offline
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request)
          .then(networkResponse => {
            if (!networkResponse || networkResponse.status !== 200) {
              return networkResponse;
            }
            return caches.open(CACHE_NAME).then(cache => {
              cache.put(event.request, networkResponse.clone());
              return networkResponse;
            });
          })
          .catch(() => {
            // Fallback offline
            return new Response('Offline - Porto Subito Driver', {
              status: 503,
              statusText: 'Service Unavailable',
              headers: new Headers({ 'Content-Type': 'text/plain' })
            });
          });
      })
  );
});