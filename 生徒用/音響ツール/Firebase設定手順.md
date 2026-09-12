# 「現在の音響再生状況」配信機能 — Fort様に一度だけお願いしたい設定（2026-09-12）

## 結論から

**新しいFirebaseプロジェクトを作る必要はありません。npm・CLIのインストールも、基本的には不要です。**

この機能（音響係が今何を再生しているかを、インターネット経由で誰でもリアルタイムに見られるようにする）は、
`shiryo.html`（ホームページ）の「ご質問・気になる点」欄の匿名コメント・アクセスカウンター機能が
**既に使っている既存のFirebaseプロジェクト（プロジェクトID: `d-bunkasai`）**をそのまま再利用する設計にしました。
新しく作ったのは、そのプロジェクトの中の `nowplaying` という1つのデータパスだけです。

Fort様にお願いしたいことは、実質**次の「方法A」1つだけ**です。ブラウザでの操作のみ、3分もかからないはずです。

（この設計に至った経緯・検討したがボツにした案は、末尾の「検討の経緯」を参照してください）

---

## 方法A：Firebaseコンソールで1回だけ設定する（推奨・これだけでOK）

1. ブラウザで https://console.firebase.google.com/project/d-bunkasai/database/d-bunkasai-default-rtdb/rules
   を開く（このプロジェクトを作成・管理しているGoogleアカウントでログインしてください）。
2. 表示されているルール（JSON）の一番外側、`"rules": { ... }` の中に、以下の `"nowplaying"` のブロックを
   **既存の内容を消さずに** 追加してください（`comments`や`kingdom`など、既にある項目の隣に並べて追加するイメージです）。

   ```json
   "nowplaying": {
     "current": {
       ".read": true,
       ".write": true,
       ".validate": "newData.hasChildren(['isPlaying', 'currentTime', 'updatedAt']) && newData.child('isPlaying').isBoolean() && newData.child('currentTime').isNumber() && newData.child('updatedAt').isNumber()"
     }
   }
   ```

   例えば、追加前が

   ```json
   {
     "rules": {
       "comments": { ... },
       "kingdom": { ... },
       "pageviews": { ... }
     }
   }
   ```

   のような形であれば、追加後は

   ```json
   {
     "rules": {
       "comments": { ... },
       "kingdom": { ... },
       "pageviews": { ... },
       "nowplaying": {
         "current": {
           ".read": true,
           ".write": true,
           ".validate": "newData.hasChildren(['isPlaying', 'currentTime', 'updatedAt']) && newData.child('isPlaying').isBoolean() && newData.child('currentTime').isNumber() && newData.child('updatedAt').isNumber()"
         }
       }
     }
   }
   ```

   のようになります（カンマの付け忘れに注意してください。既存のブロックの最後に `,` を1つ足してから
   `"nowplaying"` を追加する形になります）。

3. 右上の「公開」ボタンを押す。以上です。

### `.validate` の部分について（任意・省略しても動きます）

`.validate` の行は「誰かが変な形のデータを送り込んで壊すのを防ぐ、ごく簡単なバリデーション」です。
必須ではありません。手打ちでの追加ミスが心配な場合は、シンプルに以下のように `.read`/`.write` だけでも
機能します（既存の`comments`等も恐らく同程度のシンプルなルールのはずです）：

```json
"nowplaying": {
  "current": {
    ".read": true,
    ".write": true
  }
}
```

### 動作確認方法

設定後、以下で確認できます：
1. `生徒用/音響ツール/音響再生ツール.html` を開き、何か曲を再生する
2. 別のタブ（またはスマホ等の別端末）で `shiryo.html` を開く
3. ページ最上部のバナーが「現在は再生されていません」から、再生中の曲名・progress barの表示に変わることを確認する

反映まで数秒（ポーリング間隔2秒程度）かかるのは仕様です。しばらく待っても変わらない場合は、
ブラウザの開発者ツール（F12）のConsoleタブでエラーが出ていないか確認するか、そのまま音響係・
一般閲覧の動作には影響しないので急ぎでなければそのままお知らせください。

---

## 方法B：ターミナル（CLI）で設定したい場合（任意・上級者向け・方法Aの代替）

方法Aの方が確実で速いですが、「ブラウザのコンソール画面よりターミナル操作の方が慣れている」という場合向けに、
半自動化スクリプトを `生徒用/音響ツール/セットアップ.sh` として用意しました。

**なぜ完全自動化（ログイン1回だけで全自動）にできなかったか**：Firebase CLI（`firebase-tools`）には、
Realtime Databaseの「今のルール」を取得する専用コマンドが存在しません（`firebase database:get`は
データの読み取り用で、ルールは対象外です）。そのため、既存のルール（`comments`・`kingdom`・`pageviews`等）を
壊さずに`nowplaying`だけを安全に追加するには、**現在のルールを一度だけ人の目でコンソールからコピーしてもらう**
必要があります（下記手順1）。これを省略して「ルール全体を新しいファイルで上書き」する自動化も技術的には
可能ですが、もし既存のルールの内容を私（Claude）が正確に把握できていなかった場合、`comments`等の
既存機能を壊すリスクがあるため、あえて自動化しませんでした（安全のための意図的な判断です）。

使い方：
1. https://console.firebase.google.com/project/d-bunkasai/database/d-bunkasai-default-rtdb/rules
   を開き、表示されているルールJSONを全選択してコピーし、`生徒用/音響ツール/current-rules.json`
   という名前で保存する
2. ターミナルで次を実行する：
   ```bash
   cd 生徒用/音響ツール
   bash セットアップ.sh
   ```
3. 初回のみ、ブラウザでFirebaseへのログイン画面が開くのでGoogleアカウントでログインする
4. 「完了しました」のメッセージが出れば設定完了（動作確認方法は方法Aと同じ）

前提として、パソコンに Node.js（`node`コマンド）がインストールされている必要があります
（`firebase-tools`自体はスクリプトが自動でインストールを試みます）。

---

## 検討の経緯（読まなくても支障ありません・記録のため）

- 当初「Firebaseを新規に使ってよい」という前提で新規プロジェクト作成を想定していましたが、実装に着手する中で
  `shiryo.html`が既にFirebaseプロジェクト`d-bunkasai`を使っていることに気づき、新規作成は不要と判断しました。
- その後「Firebase作るのが面倒、自動化できないか」という指示を受け、(1)このリポジトリに
  Netlify/Vercel/Cloudflare Pages/Workers等のサーバーレス機能付きホスティングが既に無いか確認しましたが、
  リポジトリには`.github/workflows/pages-deploy.yml`によるGitHub Pages配信のみが存在し、サーバーレス関数を
  使える基盤は無いことを確認しました（`プロジェクト概要.md`にも「GitHub PagesはCloudflare Pages/Netlifyの
  ような`_headers`機構に対応していない」という記述があり、過去に検討のうえGitHub Pages一本での運用と
  明確に決定済みであることが分かりました）。そのため(2)Firebase CLIでの自動化を試みましたが、
  上記の理由（ルール取得コマンドの不在）により、ルール設定の部分だけは安全のため人の手を1ステップ残す
  設計にしています。
- なお、後から「Cloudflareで運用しているはず」という趣旨の確認もありましたが、このリポジトリ
  （3D-bunkasai-2026）にはCloudflare関連の設定は一切見つかりませんでした。おそらく別プロジェクト
  （Fort様の別リポジトリ`claude-workspace`ではNetlifyを使用、との記載あり）との混同と思われます。
  念のためこの点はPR・完了報告でも明記しています。実際にこのリポジトリ用のCloudflareアカウント・
  プロジェクトが存在する場合は、お手数ですがその情報（アカウント名・プロジェクト名等）をご教示いただければ、
  設計を移行することも可能です。
