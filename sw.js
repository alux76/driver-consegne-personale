self.addEventListener('install', function(event) {
    console.log('Service Worker installato');
    self.skipWaiting();
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        fetch(event.request).catch(function() {
            return new Response('Offline', {
                status: 503,
                statusText: 'Service Unavailable'
            });
        })
    );
});