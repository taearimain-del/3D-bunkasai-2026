#!/usr/bin/env bash
# 「現在の音響再生状況」配信機能 — Realtime Databaseルール設定スクリプト（任意・上級者向け）
#
# 【重要】このスクリプトを使わなくても、Firebase設定手順.md の「方法A：コンソールで
# 直接貼り付ける」の方が速く・確実です（ブラウザ操作のみ、3分程度）。
# このスクリプトは「ターミナル操作の方が慣れている」場合の代替手段（方法B）です。
#
# 【なぜ完全自動化（ログイン1回だけで全自動）にできないか】
# Firebase CLI（firebase-tools）には、Realtime Databaseの「現在のルール」を取得する
# 専用コマンドが存在しません（database:get はデータ取得用でルールは対象外）。そのため、
# 既存のルール（comments/kingdom/pageviews等）を壊さずnowplayingパスだけを安全に追加する
# には、一度だけ現在のルールをコンソールからコピーしてもらう必要があります（下記手順1）。
# これを省略して「ルール全体を新しいファイルで無条件に上書き」する自動化も技術的には
# 可能ですが、既存の内容を壊すリスクがあるため、あえて自動化せずここで人の目を挟む
# 設計にしています（詳細はFirebase設定手順.md参照）。
#
# 使い方：
#   1. Firebaseコンソール（Realtime Database → ルール タブ）
#      https://console.firebase.google.com/project/d-bunkasai/database/d-bunkasai-default-rtdb/rules
#      を開き、表示されているルールJSONを全選択してコピーし、このファイルと同じフォルダに
#      current-rules.json という名前で保存する
#   2. bash セットアップ.sh を実行する
#   3. 初回のみ、表示されるURLでGoogleアカウントにログインする
#   4. 「完了しました」と表示されれば、nowplayingパスの読み書き許可が追加されている
#
# 前提：パソコンにNode.js（nodeコマンド）がインストールされていること。

set -euo pipefail
cd "$(dirname "$0")"

PROJECT_ID="d-bunkasai"
RULES_FILE="current-rules.json"
MERGED_FILE=".nowplaying-rules-merged.json"

if [ ! -f "$RULES_FILE" ]; then
  echo "エラー：$RULES_FILE が見つかりません。"
  echo ""
  echo "次のURLを開き、表示されているルールJSONを全選択してコピーし、"
  echo "このフォルダに $RULES_FILE という名前で保存してから、もう一度実行してください："
  echo "  https://console.firebase.google.com/project/${PROJECT_ID}/database/${PROJECT_ID}-default-rtdb/rules"
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "エラー：Node.js（nodeコマンド）が見つかりません。"
  echo "https://nodejs.org/ からインストールしてから、もう一度実行してください。"
  echo "（このコマンドが使えるなら、代わりにFirebase設定手順.mdの「方法A」をお試しください）"
  exit 1
fi

if ! command -v firebase >/dev/null 2>&1; then
  echo "firebase-toolsが見つからないため、npmでインストールします…"
  npm install -g firebase-tools
fi

echo "現在のルールに nowplaying パスの読み書き許可を追加してマージします…"
node -e "
const fs = require('fs');
const current = JSON.parse(fs.readFileSync('${RULES_FILE}', 'utf8'));
current.rules = current.rules || {};
current.rules.nowplaying = {
  current: {
    '.read': true,
    '.write': true,
    '.validate': \"newData.hasChildren(['isPlaying', 'currentTime', 'updatedAt']) && newData.child('isPlaying').isBoolean() && newData.child('currentTime').isNumber() && newData.child('updatedAt').isNumber()\"
  }
};
fs.writeFileSync('${MERGED_FILE}', JSON.stringify(current, null, 2));
console.log('マージ結果を ${MERGED_FILE} に書き出しました。');
"

cat > firebase.json <<EOF
{
  "database": {
    "rules": "${MERGED_FILE}"
  }
}
EOF

node -e "
const fs = require('fs');
fs.writeFileSync('.firebaserc', JSON.stringify({ projects: { default: '${PROJECT_ID}' } }, null, 2));
"

echo "Firebaseへログインします（ブラウザが開きます。初回のみ）…"
firebase login

echo "マージ済みルールをデプロイします…"
firebase deploy --only database --project "${PROJECT_ID}"

echo ""
echo "完了しました。nowplayingパスの読み書きが許可されました。"
echo "動作確認：音響再生ツール.html で何か再生し、shiryo.html を別タブ（または別端末）で開いて、"
echo "「現在は再生されていません」の表示が実際の再生状況に変わることを確認してください"
echo "（反映まで数秒かかります）。"
