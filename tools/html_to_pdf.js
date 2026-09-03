#!/usr/bin/env node
'use strict';
// このプロジェクトのHTML資料をPDF化するツール（Linux環境用）。
// Windows専用のmd_to_html.pyはHTML生成のみを担当しており、PDF化の工程は
// これまでユーザーのWindows環境で別途行われていた。このLinux環境（Claude Code
// on the web等）にはPlaywright同梱のChromiumが用意されているため、
// page.pdf()でHTMLから直接PDFを生成する。
//
// 使い方:
//   node tools/html_to_pdf.js --all
//     -> ALL_DOCSに登録された全資料を一括再生成
//   node tools/html_to_pdf.js <入力.html>:<出力.pdf> [...]
//     -> 指定した組だけを再生成

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function loadPlaywright() {
  try {
    return require('playwright');
  } catch {
    // グローバルインストールのplaywrightをNODE_PATH未設定でも見つけられるようにする
    const globalRoot = execSync('npm root -g').toString().trim();
    module.paths.push(globalRoot);
    return require('playwright');
  }
}

function findFallbackChromium() {
  const base = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';
  if (!fs.existsSync(base)) return null;
  const dirs = fs
    .readdirSync(base)
    .filter((d) => /^chromium-\d+$/.test(d))
    .sort();
  if (dirs.length === 0) return null;
  const exe = path.join(base, dirs[dirs.length - 1], 'chrome-linux', 'chrome');
  return fs.existsSync(exe) ? exe : null;
}

const REPO_ROOT = path.resolve(__dirname, '..');

// other/配下のHTML（正）と、生成先の生徒用PDFの対応表。
// 新しい資料を追加したらここにも追記すること。
const ALL_DOCS = [
  ['other/配役表.html', '生徒用/pdf/配役表.pdf'],
  ['other/配役表_ナレーター用.html', '生徒用/pdf/配役表_ナレーター用.pdf'],
  ['other/企画書.html', '生徒用/pdf/企画書.pdf'],
  ['other/舞台構成.html', '生徒用/pdf/舞台構成.pdf'],
  ['other/台本/台本_アナと雪の女王.html', '生徒用/pdf/台本/台本_アナと雪の女王.pdf'],
  ['other/台本/台本_アナと雪の女王_役者用.html', '生徒用/pdf/台本/台本_アナと雪の女王_役者用.pdf'],
  ['other/役割書/役割書_キャスト.html', '生徒用/pdf/役割書/役割書_キャスト.pdf'],
  ['other/役割書/役割書_大道具係.html', '生徒用/pdf/役割書/役割書_大道具係.pdf'],
  ['other/役割書/役割書_小道具係.html', '生徒用/pdf/役割書/役割書_小道具係.pdf'],
  ['other/役割書/役割書_照明係.html', '生徒用/pdf/役割書/役割書_照明係.pdf'],
  ['other/役割書/役割書_舞台監督.html', '生徒用/pdf/役割書/役割書_舞台監督.pdf'],
  ['other/役割書/役割書_音響係.html', '生徒用/pdf/役割書/役割書_音響係.pdf'],
];

function parseArgs(argv) {
  if (argv.includes('--all')) return ALL_DOCS;
  if (argv.length === 0) {
    console.error('使い方: node tools/html_to_pdf.js --all');
    console.error('    または: node tools/html_to_pdf.js <入力.html>:<出力.pdf> [...]');
    process.exit(1);
  }
  return argv.map((pair) => {
    const idx = pair.lastIndexOf(':');
    if (idx === -1) {
      throw new Error(`不正な指定: ${pair}（<入力.html>:<出力.pdf> の形式で指定すること）`);
    }
    return [pair.slice(0, idx), pair.slice(idx + 1)];
  });
}

(async () => {
  const { chromium } = loadPlaywright();
  const pairs = parseArgs(process.argv.slice(2));

  let browser;
  try {
    browser = await chromium.launch();
  } catch (e) {
    const exe = findFallbackChromium();
    if (!exe) throw e;
    browser = await chromium.launch({ executablePath: exe });
  }

  let okCount = 0;
  for (const [inputRel, outputRel] of pairs) {
    const input = path.resolve(REPO_ROOT, inputRel);
    const output = path.resolve(REPO_ROOT, outputRel);
    if (!fs.existsSync(input)) {
      console.error(`SKIP（見つかりません）: ${inputRel}`);
      continue;
    }
    fs.mkdirSync(path.dirname(output), { recursive: true });
    const page = await browser.newPage();
    await page.goto('file://' + input, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.pdf({ path: output, printBackground: true, preferCSSPageSize: true });
    await page.close();
    console.log(`OK: ${inputRel} -> ${outputRel}`);
    okCount += 1;
  }
  await browser.close();
  console.log(`完了: ${okCount}/${pairs.length}件`);
})().catch((err) => {
  console.error('失敗:', err);
  process.exit(1);
});
