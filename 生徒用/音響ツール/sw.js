// 音響再生ツール（アナと雪の女王）用 Service Worker
// 目的：音源Base64を内蔵した約63MBの単一HTMLファイルをオフラインでも開けるようにする。
//
// 注意：63MBという大きなファイルをCache Storageに保存しようとすると、モバイル端末
// （特にiOS Safariのストレージ容量制限）でキャッシュに失敗する可能性がある。
// このファイルは全体を try-catch / Promise.catch で保護し、キャッシュ処理が
// 失敗しても通常のオンライン読み込み（ネットワーク経由での表示）に一切影響しない
// よう設計している（エラーで機能停止しない）。

const CACHE_NAME = 'sound-tool-cache-v1';
const PRECACHE_URLS = [
  './音響再生ツール.html',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-512-maskable.png',
  './icons/apple-touch-icon.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      try {
        const cache = await caches.open(CACHE_NAME);
        // addAllは1件でも失敗すると全体が失敗するため、1件ずつput（失敗しても続行）
        for (const url of PRECACHE_URLS) {
          try {
            const res = await fetch(url);
            if (res && res.ok) {
              await cache.put(url, res);
            }
          } catch (e) {
            // 63MBファイルのキャッシュ失敗（容量制限等）はここで静かに無視。
            // 次回アクセス時にfetchイベント側で再度キャッシュを試みる。
          }
        }
      } catch (e) {
        // caches.open自体が使えない環境でもinstallは正常終了させる
      }
      // 新しいService Workerをすぐ有効化する
      try { await self.skipWaiting(); } catch (e) {}
    })()
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      try {
        const names = await caches.keys();
        await Promise.all(
          names
            .filter((name) => name !== CACHE_NAME)
            .map((name) => caches.delete(name).catch(() => {}))
        );
      } catch (e) {
        // キャッシュ一覧取得に失敗しても無視
      }
      try { await self.clients.claim(); } catch (e) {}
    })()
  );
});

// Cache First 戦略：キャッシュにあればそれを返し、無ければネットワークから取得して
// 可能ならキャッシュに保存する（保存失敗は無視してレスポンスはそのまま返す）。
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    (async () => {
      try {
        const cached = await caches.match(event.request);
        if (cached) return cached;
      } catch (e) {
        // キャッシュ参照に失敗した場合はそのままネットワークへフォールバック
      }

      try {
        const networkResponse = await fetch(event.request);
        try {
          if (networkResponse && networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            // 63MBファイルなどの保存失敗（容量制限）はcatchで握りつぶし、
            // レスポンス自体は正常にページへ返す。
            cache.put(event.request, networkResponse.clone()).catch(() => {});
          }
        } catch (e) {
          // キャッシュへの保存に失敗しても表示には影響させない
        }
        return networkResponse;
      } catch (e) {
        // オフラインかつキャッシュにも無い場合はここで失敗が伝播する（想定内の挙動）
        throw e;
      }
    })()
  );
});
