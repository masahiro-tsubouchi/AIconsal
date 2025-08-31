// Minimal service worker to avoid 404 in production and enable basic lifecycle
// This does not cache any assets; it's a no-op SW.

self.addEventListener('install', (event) => {
  // Activate the new SW immediately
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  // Take control of uncontrolled clients right away
  event.waitUntil(self.clients.claim());
});

// Optional: If needed, you can add fetch handling here.
// Leaving it empty means the SW won't intercept network requests.
