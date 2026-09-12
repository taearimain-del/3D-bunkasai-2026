// ============================================================
// 「現在の音響再生状況」ブロードキャストモジュール（2026-09-12新規作成）
// ============================================================
//
// 【背景】音響係が音響再生ツール一式（音響再生ツール.html／トロールの歌タイミングツール.html）
// で何かを再生しているとき、インターネット経由でどこからでも誰でも「今何が再生されていて
// どこまで進んでいるか」をリアルタイムで見られるようにしたい、というFort様の要望への対応。
// 閲覧側は shiryo.html（ホームページ最上部）が担当し、この配信を購読して表示する
// （生徒用/変更点.md 2026-09-12エントリ参照）。
//
// 【方式（2026-09-12・当初案からの方針転換）】
// 真のリアルタイム通信（WebSocket・Firebase SDKのリアルタイムリスナー等）は不要と判断した。
// 音声そのものは各端末でローカル再生されており、閲覧側は「最後に受け取ったスナップショット
// {isPlaying, currentTime, updatedAt}」から
//   表示用currentTime = currentTime + (isPlaying ? (Date.now() - updatedAt)/1000 : 0)
// で補完すれば体感上ほぼリアルタイムに見える。そのため、Firebase JS SDK（
// https://www.gstatic.com/firebasejs/...）は一切読み込まず、Realtime DatabaseのREST API
// （プレーンなHTTPS PUT）だけを使う軽量な設計にしている。閲覧側（shiryo.html）も同様に
// 定期ポーリング（GET）＋ローカル補間で表示する。
//
// 【使っているFirebaseプロジェクトについて】
// 新規に作成したものではない。shiryo.html（ホームページ）の「ご質問・気になる点」欄の
// 匿名コメント機能・アクセスカウンター機能が既に使っている既存プロジェクト（プロジェクトID:
// d-bunkasai）をそのまま再利用し、新しい「nowplaying」パスを1つ追加しているだけである。
// Firebaseのクライアント側の接続先（databaseURL）はそもそも公開情報であり秘密ではない
// （shiryo.html内に既に平文で存在する）。新規プロジェクト作成・APIキー発行は不要と判断した
// （詳細な経緯・Fort様に一度だけお願いしたい設定はFirebase設定手順.md参照）。
//
// 【安全設計】
// ・このファイル内のあらゆる失敗（Firebase未設定、ルール未整備、オフライン等）はすべて
//   try/catchで握りつぶし、呼び出し側（音の再生そのもの）には絶対に影響を与えない。
// ・書き込み頻度は1.5秒に1回程度へ間引く（無料枠を圧迫しないため）。ただし再生/一時停止/
//   曲切り替え/シークなど「意味のある変化」が起きた瞬間は間引かず即座に書き込む。
//   呼び出し側は間引きを一切意識せず、既存の定期更新ループ内で毎回 update() を
//   呼ぶだけでよい設計にしている。
// ・タブを閉じる／通信が切れた場合の「再生中のまま表示が残り続ける」対策：
//   REST方式のためFirebaseのonDisconnect()機能は使えない。代わりに
//   (a) ページを離れる瞬間（pagehide／visibilitychange）に「isPlaying:false」を
//       fetchのkeepalive:trueで送る（ベストエフォート、届かない場合もある）
//   (b) 閲覧側（shiryo.html）で「最終更新から8秒経過していたら停止扱いにする」
//       タイムアウト処理を実装済み（こちらが本命の保険）
//   の二重の対策としている。

(function () {
  // 既存プロジェクト（d-bunkasai）のRealtime Database。shiryo.html内のfirebaseConfigと同一。
  const DATABASE_URL = 'https://d-bunkasai-default-rtdb.asia-southeast1.firebasedatabase.app';
  const NOWPLAYING_URL = DATABASE_URL + '/nowplaying/current.json';

  const MIN_WRITE_INTERVAL_MS = 1500; // 通常時の最小書き込み間隔（無料枠対策の間引き）
  const SEEK_JUMP_THRESHOLD_SEC = 1.5; // これ以上currentTimeが飛んだら「シークされた」とみなし即書き込み

  let lastWriteAt = 0;
  let lastSent = null; // 直前に実際に書き込んだ内容（変化検知用）
  let writeInFlight = false;

  function shouldForceWrite(s) {
    if (!lastSent) return true;
    if (lastSent.toolId !== s.toolId) return true;
    if (lastSent.cueId !== s.cueId) return true;
    if (lastSent.isPlaying !== s.isPlaying) return true;
    if (Math.abs((lastSent.currentTime || 0) - (s.currentTime || 0)) > SEEK_JUMP_THRESHOLD_SEC) return true;
    return false;
  }

  function sendPut(payload, opts) {
    const keepalive = !!(opts && opts.keepalive);
    try {
      fetch(NOWPLAYING_URL, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        keepalive: keepalive,
      }).catch(() => {
        // ルール未整備・オフライン等は静かに無視（配信が無効になるだけ、再生は継続）
      }).finally(() => { writeInFlight = false; });
    } catch (e) {
      writeInFlight = false;
    }
  }

  // 呼び出し側（各ツールの既存の定期更新ループ）から、間引きを気にせず毎回呼んでよい。
  // 実際にFirebaseへ書き込むかどうかはこの関数の中で判断する。
  function update_(state) {
    try {
      const now = Date.now();
      const force = shouldForceWrite(state);
      if (!force && (now - lastWriteAt) < MIN_WRITE_INTERVAL_MS) return;
      if (writeInFlight && !force) return; // 前回の書き込みがまだ飛んでいる最中の通常ティックはスキップ

      lastWriteAt = now;
      lastSent = {
        toolId: state.toolId,
        cueId: state.cueId,
        isPlaying: state.isPlaying,
        currentTime: state.currentTime,
      };
      writeInFlight = true;
      sendPut({
        toolId: state.toolId || null,
        cueId: state.cueId || null,
        title: state.title || null,
        isPlaying: !!state.isPlaying,
        currentTime: typeof state.currentTime === 'number' ? state.currentTime : 0,
        duration: typeof state.duration === 'number' ? state.duration : 0,
        updatedAt: now,
      });
    } catch (e) {
      writeInFlight = false;
      // 想定外のエラーも含め、すべてここで握りつぶす（音声再生には絶対に影響させない）
    }
  }

  // ページを離れる瞬間、ベストエフォートで「再生していない」状態を送っておく
  // （閲覧側の8秒タイムアウトを待たずに済ませるための保険。届かなくても実害はない）。
  function sendStoppedOnLeave() {
    if (!lastSent || lastSent.isPlaying === false) return; // 元々止まっていたなら送る必要なし
    try {
      sendPut({
        toolId: lastSent.toolId || null,
        cueId: lastSent.cueId || null,
        isPlaying: false,
        currentTime: typeof lastSent.currentTime === 'number' ? lastSent.currentTime : 0,
        updatedAt: Date.now(),
      }, { keepalive: true });
    } catch (e) { /* ベストエフォートのため失敗は無視 */ }
  }
  try {
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') sendStoppedOnLeave();
    });
    window.addEventListener('pagehide', sendStoppedOnLeave);
  } catch (e) { /* 古い環境での予期しないエラーも無視 */ }

  window.NowPlayingBroadcast = { update: update_ };
})();
