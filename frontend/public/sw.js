// Service Worker untuk Portal SA
// Cache-first untuk halaman statis, network-first untuk API (Requirement 12.2)
// Offline queue sync (Requirement 12.5)

const CACHE_NAME = "portal-sa-v1";
const OFFLINE_QUEUE_KEY = "portal-sa-offline-queue";

// Halaman statis yang di-cache saat install
const STATIC_ASSETS = [
  "/",
  "/manifest.json",
];

// ============================================
// Event: Install — cache aset statis
// ============================================
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  // Langsung aktifkan service worker baru
  self.skipWaiting();
});

// ============================================
// Event: Activate — bersihkan cache lama
// ============================================
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  // Ambil kontrol semua client
  self.clients.claim();
});

// ============================================
// Event: Fetch — routing strategy
// ============================================
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests untuk cache (POST/PUT/PATCH ditangani oleh offline queue di client)
  if (request.method !== "GET") {
    return;
  }

  // Network-first untuk API calls
  if (url.pathname.startsWith("/api")) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Cache-first untuk static assets (CSS, JS, images, fonts)
  if (isStaticAsset(url.pathname)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Network-first untuk halaman navigasi (agar selalu fresh)
  if (request.mode === "navigate") {
    event.respondWith(networkFirstWithCache(request));
    return;
  }

  // Default: cache-first
  event.respondWith(cacheFirst(request));
});

// ============================================
// Event: Background Sync — sync offline queue (Requirement 12.5)
// ============================================
self.addEventListener("sync", (event) => {
  if (event.tag === "sync-offline-submissions") {
    event.waitUntil(syncOfflineSubmissions());
  }
});

// ============================================
// Strategy: Cache First
// ============================================
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    return offlineFallback();
  }
}

// ============================================
// Strategy: Network First
// ============================================
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    return response;
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    return new Response(
      JSON.stringify({
        status: "error",
        message: "Offline — tidak dapat terhubung ke server",
        data: null,
      }),
      {
        status: 503,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
}

// ============================================
// Strategy: Network First with Cache Update (untuk halaman navigasi)
// ============================================
async function networkFirstWithCache(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    return offlineFallback();
  }
}

// ============================================
// Helpers
// ============================================

// Cek apakah URL adalah static asset
function isStaticAsset(pathname) {
  const staticExtensions = [
    ".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".woff", ".woff2", ".ttf", ".eot", ".ico",
  ];
  return staticExtensions.some((ext) => pathname.endsWith(ext));
}

// Response fallback saat offline
function offlineFallback() {
  return new Response(
    `<!DOCTYPE html>
    <html lang="id">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <title>Portal SA — Offline</title>
      <style>
        body { font-family: 'Open Sans', system-ui, sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background: #fafafa; color: #171717; }
        .container { text-align: center; padding: 2rem; }
        h1 { font-size: 1.5rem; margin-bottom: 0.5rem; }
        p { color: #525252; }
        .icon { font-size: 3rem; margin-bottom: 1rem; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="icon">📡</div>
        <h1>Anda sedang offline</h1>
        <p>Halaman ini belum tersedia di cache. Periksa koneksi internet Anda dan coba lagi.</p>
      </div>
    </body>
    </html>`,
    {
      status: 503,
      headers: { "Content-Type": "text/html; charset=utf-8" },
    }
  );
}

// ============================================
// Offline Queue Sync
// ============================================
async function syncOfflineSubmissions() {
  // Sync dilakukan di client-side (lib/offline-queue.ts)
  // Service Worker hanya sebagai trigger via Background Sync API
  // Notify clients agar mereka menjalankan sync
  const clients = await self.clients.matchAll({ type: "window" });
  for (const client of clients) {
    client.postMessage({ type: "SYNC_OFFLINE_QUEUE" });
  }
}
