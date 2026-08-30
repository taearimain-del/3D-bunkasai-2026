// 音響再生ツール（アナと雪の女王）用 Service Worker
// 目的：本体HTML（音響再生ツール.html）は数十KB程度の小さなファイルで、実際の
// 音源（mp3/wav）は個別ファイルとして相対パス参照している。Service Workerは
// このHTML本体と各音源ファイルをそれぞれ個別にCache Storageへ保存することで、
// 一度Wi-Fi環境で開けば以後はオフラインでもアプリのように動作するようにする。
//
// 【2026-08-30変更】従来はBase64エンコードした音源データをHTML内に直接埋め込み、
// 単一の約77MBの巨大HTMLファイルをまるごとキャッシュする設計だった（63MB→77MBまで
// 音源追加のたびに肥大化）。iOS Safariは大きすぎるレスポンスのキャッシュに失敗
// しやすく、本体のダウンロード・パースにも時間がかかっていたため、Base64埋め込みを
// やめてHTML本体を軽量化し、音源ファイルはPRECACHE_URLSで個別にキャッシュする方式へ
// 変更した（詳細は`生徒用/変更点.md`2026-08-30参照）。
// 【2026-08-30追記】当初id:'05'（あこがれの夏）のみBase64埋め込みデータと実ファイル
// の内容が不一致だったため保留していたが、ユーザー確認の結果Base64埋め込み側が
// 正式版と判明。実ファイルをBase64側の内容に差し替えたうえで、id:'05'も他17件と
// 同様に実ファイル参照方式へ切り替えた。これにより全音源が実ファイル参照化され、
// HTML本体はBase64データを一切含まない軽量ファイルとなった。
//
// 注意：音源ファイルの中にはサイズが大きいものもあり、モバイル端末
// （特にiOS Safariのストレージ容量制限）でキャッシュに失敗する可能性がある。
// このファイルは全体を try-catch / Promise.catch で保護し、キャッシュ処理が
// 失敗しても通常のオンライン読み込み（ネットワーク経由での表示）に一切影響しない
// よう設計している（エラーで機能停止しない）。

// 重要：音響再生ツール.html／manifest.json／アイコン／音源ファイルを追加・更新する
// たびに、このCACHE_NAMEの末尾バージョンを必ず上げること（例 v8→v9）。
// Cache First戦略のため、名前を変えない限り古いキャッシュが配信され続け、
// 本番端末に新しいデザイン・修正・音源が反映されない（2026-07-08に実際に発生）。
//
// 【今後の音源追加・差し替え時の必須手順（2026-08-30〜）】
//   (1) 実ファイルを 生徒用/音響ツール/ フォルダに置く
//   (2) 音響再生ツール.htmlのCUES定義に file フィールドで参照する
//       （data フィールドでのBase64埋め込みはもう不要。著作権上の理由がある場合を除く）
//   (3) 下記PRECACHE_URLSにそのファイルを追加し、CACHE_NAMEをバージョンアップする
const CACHE_NAME = 'sound-tool-cache-v11';
const PRECACHE_URLS = [
  './音響再生ツール.html',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-512-maskable.png',
  './icons/apple-touch-icon.png',
  // 実音源ファイル（2026-08-30、Base64埋め込みから個別ファイル参照方式へ移行）
  './イントロ.mp3',
  './雪だるまつくろう.mp3',
  './生まれてはじめて.mp3',
  './とびら開けて.mp3',
  './ありのままの.mp3',
  './ありのままの_key-1.mp3',
  './ありのままの_key-2.mp3',
  './あこがれの夏.mp3',
  './生まれてはじめてリプライズ.mp3',
  './愛さえあれば.mp3',
  './Epilogue_From_FrozenScore.mp3',
  './魔法①.mp3',
  './魔法②.wav',
  './アナに魔法があたって倒れるとき.mp3',
  './魔法④.wav',
  './アナの魔法が解けるとき.wav',
  './お城にいるときとかオラフが二回目に初めて出てくるときとか.wav',
  './氷の上歩いている.mp3'
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
