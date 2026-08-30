// 音響再生ツール（アナと雪の女王）用 Service Worker
// 目的：本体HTML（音響再生ツール.html）は数十KB程度の小さなファイルで、実際の
// 音源（mp3/wav）は個別ファイルとして相対パス参照している。Service Workerは
// このHTML本体と各音源ファイルをそれぞれ個別にCache Storageへ保存することで、
// 一度Wi-Fi環境で開けば以後はオフラインでもアプリのように動作するようにする。
//
// 【2026-08-30 19:48変更・キャッシュ戦略の全面刷新】
// 従来はCache First戦略（キャッシュがあれば無条件にそれを返す）を採用しており、
// コンテンツを更新するたびにCACHE_NAMEのバージョン番号を手動で上げない限り、
// 古いキャッシュが配信され続ける設計だった。この「上げ忘れ」が本日だけで2回発生し
// （19:03台の刷新作業・19:36のiPhoneバグ修正の各直後）、本番運用者から「手動の
// バージョン管理に頼らず、更新したら自動的に反映される仕組みにしてほしい」との
// 明確な要望があったため、コンテンツの性質に応じて戦略を使い分ける方式に変更した。
//
//   1) 音響再生ツール.html／manifest.json（頻繁に更新され、常に最新であるべきもの）
//      → Network First（タイムアウト付き、下記NETWORK_TIMEOUT_MS）。
//        まずネットワークから取得し、成功すればその内容でキャッシュを更新しつつ
//        そのまま返す（＝常に最新版）。ネットワークがタイムアウト・失敗した場合の
//        みキャッシュへフォールバックする（オフライン時の保険）。
//   2) 音源ファイル（mp3/wav）・アイコン画像（滅多に変わらないもの）
//      → Stale-While-Revalidate。キャッシュがあればまず即座にそれを返して
//        体感速度・オフライン耐性を保ちつつ、裏側で並行してネットワークから
//        最新版を取得しキャッシュを更新する（次回アクセスから反映される）。
//        キャッシュが無ければ通常通りネットワークから取得し、取得できたら
//        キャッシュに保存してから返す。
//
// これによりCACHE_NAME自体は固定名でよくなった（バージョン番号を「上げる」運用に
// 依存しない）。ただしPRECACHE_URLSの一覧（新しい音源の追加等）を変更した場合は、
// install時の一括プリキャッシュに反映させるためバージョンを上げる運用は残して
// よいが、上げ忘れても新ファイルへの初回アクセス時にStale-While-Revalidateの
// 「キャッシュ無ければ取得して保存」経路で結局キャッシュされるため、致命的な
// 問題にはならない。
//
// 注意：音源ファイルの中にはサイズが大きいものもあり、モバイル端末
// （特にiOS Safariのストレージ容量制限）でキャッシュに失敗する可能性がある。
// このファイルは全体を try-catch / Promise.catch で保護し、キャッシュ処理が
// 失敗しても通常のオンライン読み込み（ネットワーク経由での表示）に一切影響しない
// よう設計している（エラーで機能停止しない）。
//
// 【今後の音源追加・差し替え時の必須手順（2026-08-30〜）】
//   (1) 実ファイルを 生徒用/音響ツール/ フォルダに置く
//   (2) 音響再生ツール.htmlのCUES定義に file フィールドで参照する
//       （data フィールドでのBase64埋め込みはもう不要。著作権上の理由がある場合を除く）
//   (3) 下記PRECACHE_URLSにそのファイルを追加する
//       （CACHE_NAMEのバージョンアップはもう必須ではない。上げ忘れても
//        Stale-While-Revalidateにより初回アクセス時に結局キャッシュされる）
const CACHE_NAME = 'sound-tool-cache-v1';
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

// Network First戦略のタイムアウト（ミリ秒）。本番中に電波が悪い場所でツールを
// 開く可能性を考慮し、待たせすぎない範囲でネットワークを優先する。
const NETWORK_TIMEOUT_MS = 2500;

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
            // 大きいファイルのキャッシュ失敗（容量制限等）はここで静かに無視。
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

// このリクエストがNetwork First対象（HTML本体・manifest.json）かどうかを判定する。
// ・ページ本体へのナビゲーション（アドレスバー入力・再読み込み等）は request.mode
//   が'navigate'になるため、それも含めて常に最新化したいのでtrue扱いにする。
// ・それ以外はURLの末尾ファイル名で判定する。
function isNetworkFirstRequest(request) {
  try {
    if (request.mode === 'navigate') return true;
    const url = new URL(request.url);
    return url.pathname.endsWith('音響再生ツール.html') || url.pathname.endsWith('manifest.json');
  } catch (e) {
    return false;
  }
}

function timeoutRejection(ms) {
  return new Promise((_, reject) => {
    setTimeout(() => reject(new Error('sw: network timeout')), ms);
  });
}

// Network First（タイムアウト付き）：まずネットワークを試し、成功すればキャッシュを
// 更新しつつその内容を返す。タイムアウト・失敗時のみキャッシュへフォールバックする。
// キャッシュにも無ければエラーをそのまま伝播させる（通常のfetchエラーと同じ扱い）。
async function networkFirst(request) {
  try {
    const networkResponse = await Promise.race([
      fetch(request),
      timeoutRejection(NETWORK_TIMEOUT_MS)
    ]);
    if (networkResponse && networkResponse.ok) {
      try {
        const cache = await caches.open(CACHE_NAME);
        cache.put(request, networkResponse.clone()).catch(() => {});
      } catch (e) {
        // キャッシュへの保存に失敗しても表示には影響させない
      }
    }
    return networkResponse;
  } catch (e) {
    // タイムアウト、またはオフライン等でネットワーク取得に失敗した場合のみ
    // キャッシュへフォールバックする（オフライン時の保険）。
    try {
      const cached = await caches.match(request);
      if (cached) return cached;
    } catch (e2) {
      // キャッシュ参照自体に失敗した場合は下でエラーを伝播させる
    }
    throw e;
  }
}

// Stale-While-Revalidate：キャッシュがあれば即座にそれを返しつつ、裏側で並行して
// ネットワークから最新版を取得しキャッシュを更新する（次回アクセスから反映）。
// キャッシュが無ければ通常通りネットワークから取得し、成功すればキャッシュに保存
// してから返す。
async function staleWhileRevalidate(request) {
  let cached;
  try {
    cached = await caches.match(request);
  } catch (e) {
    // キャッシュ参照に失敗した場合はネットワークのみで進める
  }

  // 裏側の更新処理（レスポンスを返す処理とは独立して進める。失敗しても無視）。
  const revalidate = (async () => {
    try {
      const networkResponse = await fetch(request);
      if (networkResponse && networkResponse.ok) {
        try {
          const cache = await caches.open(CACHE_NAME);
          cache.put(request, networkResponse.clone()).catch(() => {});
        } catch (e) {
          // キャッシュへの保存に失敗しても無視
        }
      }
      return networkResponse;
    } catch (e) {
      return null;
    }
  })();

  if (cached) {
    // revalidateの完了を待たずに、まずキャッシュ済みの内容を即座に返す。
    revalidate.catch(() => {});
    return cached;
  }

  const networkResponse = await revalidate;
  if (networkResponse) return networkResponse;
  // キャッシュにもネットワークにも無い場合は通常のfetchエラーとして伝播させる
  throw new Error('sw: network and cache both unavailable');
}

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    (async () => {
      if (isNetworkFirstRequest(event.request)) {
        return networkFirst(event.request);
      }
      return staleWhileRevalidate(event.request);
    })()
  );
});
