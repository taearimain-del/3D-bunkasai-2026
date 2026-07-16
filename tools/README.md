# tools/

このプロジェクト用の小さな補助スクリプト置き場。

## html_to_pdf.js（Linux環境でのPDF再生成）

`other/`配下のHTML資料（配役表・企画書・役割書・台本など）から、`生徒用/pdf/`配下のPDFを生成する。

これまでPDF化は `プロジェクト概要.md` に書かれている `/build-pdfs` コマンド（ユーザーのWindows環境の`C:\Users\Fort_\md_to_html.py`）で行っていたが、あの手順は「md→html」の変換のみで、実際のPDF化（印刷）はユーザーのWindows環境で別途行われていた。Claude Code on the webなどLinux環境のセッションではその手段が使えないため、Playwright同梱のChromiumで代替する本スクリプトを追加した（2026-07-16）。

### 前提

- Node.jsとPlaywright（Chromium）がインストール済みであること。Claude Code on the webの標準環境には最初から入っている（`PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`）。
- `npm root -g` で見つかる場所にPlaywrightがなければ動かない。ローカルPCで使う場合は `npm install -g playwright && npx playwright install chromium` 等が必要。

### 使い方

リポジトリのルートで実行する。

```bash
# 登録済みの全資料をまとめて再生成
node tools/html_to_pdf.js --all

# 特定の資料だけ再生成（<入力html>:<出力pdf> の形式で複数指定可）
node tools/html_to_pdf.js other/配役表.html:生徒用/pdf/配役表.pdf
```

### 注意

- 各HTMLの`@page`（サイズ・余白）CSSをそのまま使う（`preferCSSPageSize: true`）。ページ数やレイアウトが崩れていないか、生成後に目視確認すること。
- `--all`で使う資料一覧はスクリプト内`ALL_DOCS`に直書きしてある。新しい資料（新しい役割書など）を追加したら、ここにも追記すること。
- PDFを上書きする前に、プロジェクトの基本ルール（`CLAUDE.md`）どおり `過去版/` へのアーカイブを忘れないこと（このスクリプト自体はアーカイブを行わない）。
- md→htmlの変換自体（内容編集）は引き続きユーザーのWindows環境の`md_to_html.py`、またはClaudeによる`other/*.html`の手動編集で行う。このスクリプトはhtml→pdfの最終工程のみを担当する。
