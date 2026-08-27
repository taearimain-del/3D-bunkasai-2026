#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert 台本.md to styled HTML matching the original 10-page design."""
import re
import sys

CHAR_COLORS = {
    'アナ・エルサ': '#9035b0',
    'アナ': '#c0305a',
    'エルサ': '#2070b0',
    '子供アナ': '#d44d75',
    '夏アナ': '#c0305a',
    '冬アナ': '#7a1030',
    '子供エルサ': '#5095cc',
    '大人エルサ': '#2070b0',
    '夏アナ・エルサ（大人）': '#9035b0',
    '冬アナ・エルサ（大人）': '#9035b0',
    'ハンス': '#8a6030',
    'クリストフ': '#b86020',
    'オラフ': '#b09000',
    'スヴェン': '#9a6840',
    'ウェーゼルトン公爵': '#604898',
    'ウェーゼルトン': '#604898',
    'トロール': '#386838',
    'ナレーター': '#505050',
    '家来': '#6a4530',
    '司祭': '#6a4530',
    '家来 / 司祭役': '#6a4530',
}

CHAR_ORDER = ['子供アナ', '夏アナ', '冬アナ', '子供エルサ', '大人エルサ', 'ハンス', 'クリストフ', 'オラフ', 'スヴェン', 'ウェーゼルトン公爵', 'トロール']

# ===== DEFAULT THEME =====
CSS_DEFAULT = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');
* { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: A4; margin: 20mm 18mm 24mm 18mm; }
body {
  font-family: 'Noto Sans JP','Hiragino Kaku Gothic ProN','Yu Gothic','Meiryo',sans-serif;
  font-size: 10.5pt;
  line-height: 2.0;
  color: #1a1a1a;
  max-width: 780px;
  margin: 0 auto;
  padding: 20px 24px 30px;
  background: #fff;
}

/* ===== TITLE BLOCK ===== */
.title-block {
  text-align: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
}
.title-label {
  font-size: 9pt;
  letter-spacing: 0.3em;
  color: #888;
  margin-bottom: 8px;
}
.title-main {
  font-size: 40pt;
  font-weight: 700;
  color: #1a3a6a;
  letter-spacing: 0.05em;
  line-height: 1.2;
  margin: 6px 0 10px;
}
.title-sub {
  font-size: 10pt;
  color: #555;
  letter-spacing: 0.1em;
}
.title-divider {
  border: none;
  border-top: 3px double #aac;
  margin: 14px 0 20px;
}

/* ===== SECTION HEADINGS ===== */
h2 {
  font-size: 13.5pt;
  font-weight: 700;
  color: #2a2a2a;
  margin: 26px 0 10px;
  padding: 7px 12px;
  border-left: 5px solid #4a7cc0;
  border-top: 1px solid #c8d8ee;
  background: #f4f7fc;
  letter-spacing: 0.05em;
}
h3 {
  font-size: 11pt;
  font-weight: 700;
  color: #446;
  margin: 16px 0 6px;
  padding-left: 10px;
  border-left: 3px solid #99a;
}
hr {
  border: none;
  border-top: 1px solid #d8d8d8;
  margin: 22px 0;
}

/* ===== CAST TABLE ===== */
.char-legend {
  font-size: 9.5pt;
  margin: 8px 0 10px;
  line-height: 2.2;
}
.char-legend .dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 3px;
  vertical-align: middle;
  position: relative;
  top: -1px;
}
table.cast-table {
  border-collapse: collapse;
  width: 100%;
  font-size: 10pt;
  margin: 8px 0 6px;
}
table.cast-table th {
  background: #eef2f8;
  border: 1px solid #c0c8d8;
  padding: 6px 10px;
  font-weight: 700;
  text-align: left;
  color: #334;
}
table.cast-table td {
  border: 1px solid #c8ccd8;
  padding: 5px 10px;
  vertical-align: middle;
}
td.cast-slot-cell {
  min-width: 100px;
  background: #fafaf6;
  border-bottom: 2px solid #888 !important;
  padding-bottom: 3px !important;
}
p.cast-note {
  font-size: 9.5pt;
  color: #999;
  margin: 6px 0 0;
  font-style: italic;
}

/* ===== STAFF NOTES ===== */
.staff-notes {
  background: #f6f6f4;
  border: 1px solid #d8d4cc;
  border-radius: 4px;
  padding: 10px 14px;
  margin: 10px 0 14px;
}
.staff-notes ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.staff-notes li {
  font-size: 10pt;
  color: #333;
  padding: 2px 0;
  line-height: 1.9;
}
.staff-notes li::before {
  content: '▸';
  color: #888;
  margin-right: 7px;
  font-size: 9pt;
}

/* ===== ACT HEADER ===== */
.act-header {
  margin: 28px 0 12px;
  page-break-before: auto;
}
.act-title {
  font-size: 15pt;
  font-weight: 700;
  color: #1a3a6a;
  padding: 8px 14px;
  border-left: 5px solid #4a7cc0;
  border-top: 2px solid #4a7cc0;
  background: #f0f4fa;
  letter-spacing: 0.03em;
}
.act-meta {
  font-size: 9pt;
  color: #888;
  margin: 4px 0 2px 4px;
}
.act-chars {
  font-size: 10pt;
  font-weight: 700;
  color: #444;
  margin: 3px 0 10px 4px;
}

/* ===== DIALOG ===== */
p.dialog {
  margin: 4px 0;
  line-height: 1.9;
}
span.char-name {
  font-weight: 700;
}
p.stage-direction {
  color: #888;
  font-size: 10pt;
  font-style: italic;
  margin: 4px 0 4px 14px;
  padding-left: 10px;
  border-left: 2px solid #ddd;
  line-height: 1.8;
}

/* ===== NARRATOR ===== */
blockquote.narrator {
  background: #f5f5f2;
  border: 1px solid #d4d0c8;
  border-left: 4px solid #aaa;
  border-radius: 3px;
  padding: 8px 14px;
  margin: 10px 0;
  font-size: 10pt;
  color: #333;
  line-height: 1.9;
}

/* ===== CUES ===== */
p.cue {
  font-size: 11pt;
  font-weight: 700;
  padding: 6px 12px;
  margin: 8px 0;
  border-radius: 3px;
  line-height: 1.7;
}
p.light-cue {
  background: #fffbeb;
  border: 1px solid #f0cc70;
  border-left: 6px solid #e0a020;
  color: #5a3800;
}
p.music-cue {
  background: #f0f8f4;
  border: 1px solid #80c8a0;
  border-left: 6px solid #30a060;
  color: #174025;
}
p.time-cue {
  background: #f4f4f2;
  border: 1px solid #ccc;
  border-left: 6px solid #999;
  color: #555;
  font-weight: 400;
}
p.daidogu-cue {
  background: #fdf4e7;
  border: 1px solid #c8842a;
  border-left: 6px solid #a06010;
  color: #4a2800;
}
p.shodogu-cue {
  background: #f2eefd;
  border: 1px solid #9060c0;
  border-left: 6px solid #6040a0;
  color: #2a0a50;
}
p.onkyo-cue {
  background: #e6f6f5;
  border: 1px solid #3aaa9a;
  border-left: 6px solid #108070;
  color: #083830;
}
p.isho-cue {
  background: #fde8f0;
  border: 1px solid #d060a0;
  border-left: 6px solid #b04080;
  color: #4a0a28;
}
p.kantoku-cue {
  background: #eaecf4;
  border: 1px solid #4050b8;
  border-left: 6px solid #2030a0;
  color: #0a1040;
}

/* ===== VERSION BADGE ===== */
.version-badge {
  display: inline-block;
  font-size: 9.5pt;
  padding: 2px 12px;
  border-radius: 4px;
  margin-bottom: 8px;
  font-weight: 700;
  letter-spacing: 0.05em;
}
.badge-full   { background: #4a7cc0; color: #fff; }
.badge-yakusha { background: #6a3080; color: #fff; }

/* ===== FOOTER NOTE ===== */
.footer-note {
  font-size: 8.5pt;
  color: #999;
  text-align: center;
  margin-top: 30px;
  padding-top: 10px;
  border-top: 1px solid #ddd;
}

/* ===== YAKUWARI TITLE ===== */
.yakuwari-dept {
  font-size: 32pt;
  font-weight: 700;
  color: #1a3a6a;
  text-align: center;
  padding: 24px 0 10px;
  letter-spacing: 0.08em;
  line-height: 1.3;
}
"""

# ===== WASHI THEME（和紙書院・古典台本スタイル）=====
CSS_WASHI = """
* { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: A4; margin: 20mm 24mm 24mm 24mm; }
body {
  font-family: 'Hiragino Mincho ProN','Yu Mincho','MS Mincho',Georgia,serif;
  font-size: 10.5pt;
  line-height: 1.9;
  color: #1e0e00;
  max-width: 680px;
  margin: 0 auto;
  padding: 16px 0 30px;
  background: #fff;
}

/* タイトル：中央揃え・大文字 */
.title-block { text-align: center; margin-bottom: 28px; padding-bottom: 0; }
.title-label { font-size: 9pt; letter-spacing: 0.5em; color: #7a5a2a; margin-bottom: 14px; display: block; }
.title-main { font-size: 38pt; font-weight: 700; color: #5a1500; letter-spacing: 0.08em; line-height: 1.25; margin: 8px 0 12px; display: block; }
.title-sub { font-size: 10pt; color: #6a4820; letter-spacing: 0.2em; display: block; }
.title-divider {
  border: none;
  border-top: 1px solid #b0802a;
  margin: 18px 0 6px;
}
.title-divider + * { margin-top: 0; }

/* 見出し：下線のみ・中央 */
h2 {
  font-size: 12.5pt; font-weight: 700; color: #3a1000;
  margin: 30px 0 12px; padding: 0 0 8px 0;
  border-bottom: 2px solid #b0802a;
  background: none; letter-spacing: 0.1em;
  text-align: center;
}
h3 { font-size: 10.5pt; font-weight: 700; color: #5a3000; margin: 18px 0 8px; padding-left: 0; border-left: none; border-bottom: 1px dotted #c0a060; padding-bottom: 4px; }
hr { border: none; border-top: 1px solid #d0b880; margin: 24px 0; }

/* キャスト表 */
.char-legend { font-size: 9pt; margin: 8px 0 10px; line-height: 2.0; }
.char-legend .dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 3px; vertical-align: middle; position: relative; top: -1px; }
table.cast-table { border-collapse: collapse; width: 100%; font-size: 9.5pt; margin: 8px 0 6px; }
table.cast-table th { background: #ede0c0; border: 1px solid #c0a060; padding: 5px 9px; font-weight: 700; text-align: left; color: #2a1000; }
table.cast-table td { border: 1px solid #d4c4a0; padding: 4px 9px; vertical-align: middle; }
td.cast-slot-cell { min-width: 90px; background: #faf4e4; border-bottom: 2px solid #b0802a !important; }
p.cast-note { font-size: 9pt; color: #8a6840; margin: 6px 0 0; font-style: italic; }
.staff-notes { background: #faf2dc; border: 1px solid #d0b880; border-left: 4px solid #b0802a; padding: 10px 14px; margin: 10px 0 14px; }
.staff-notes ul { list-style: none; padding: 0; margin: 0; }
.staff-notes li { font-size: 9.5pt; color: #2a1800; padding: 2px 0; line-height: 2.0; }
.staff-notes li::before { content: '◆'; color: #b0802a; margin-right: 6px; font-size: 8pt; }

/* ACTヘッダー：中央揃え・大きな飾り枠 */
.act-header { margin: 36px 0 16px; page-break-before: auto; text-align: center; }
.act-title {
  font-size: 16pt; font-weight: 700; color: #5a1500;
  padding: 12px 20px;
  border-top: 3px double #b0802a;
  border-bottom: 3px double #b0802a;
  background: none;
  letter-spacing: 0.12em;
  display: inline-block;
}
.act-meta { font-size: 8.5pt; color: #8a6840; margin: 6px 0 4px; }
.act-chars { font-size: 9.5pt; font-weight: 600; color: #3a2010; margin: 4px 0 12px; }

/* セリフ */
p.dialog { margin: 6px 0 2px; line-height: 1.9; }
span.char-name { font-weight: 700; }
p.stage-direction {
  color: #7a5a38; font-size: 9.5pt; font-style: italic;
  margin: 6px 0 6px 1.5em; padding-left: 0;
  border-left: none;
  line-height: 1.9;
}

/* ナレーター */
blockquote.narrator {
  background: #f5ead0; border: 1px solid #d0b880;
  border-left: 4px solid #a07030;
  padding: 8px 16px; margin: 12px 0;
  font-size: 10pt; color: #1e0e00; line-height: 2.0;
}

/* キュー */
p.cue { font-size: 10pt; font-weight: 700; padding: 5px 10px; margin: 8px 0; border-radius: 2px; line-height: 1.7; }
p.light-cue { background: #fdf8e4; border: 1px solid #e0c060; border-left: 5px solid #c89020; color: #4a3000; }
p.music-cue { background: #f0f8f0; border: 1px solid #80c090; border-left: 5px solid #308050; color: #0e2a1a; }
p.time-cue { background: #f5f0e8; border: 1px solid #c0b080; border-left: 5px solid #907040; color: #3a2810; font-weight: 400; }
p.daidogu-cue { background: #fdf4e4; border: 1px solid #c07820; border-left: 5px solid #905010; color: #3a2000; }
p.shodogu-cue { background: #f4f0fc; border: 1px solid #8858b0; border-left: 5px solid #604090; color: #260848; }
p.onkyo-cue { background: #e8f6f4; border: 1px solid #38a090; border-left: 5px solid #107060; color: #062e28; }
p.isho-cue { background: #fce8ee; border: 1px solid #c05890; border-left: 5px solid #903070; color: #420824; }
p.kantoku-cue { background: #eceef6; border: 1px solid #3848b0; border-left: 5px solid #1e30a0; color: #080e3c; }

/* バッジ・フッター */
.version-badge { display: inline-block; font-size: 9pt; padding: 2px 10px; border-radius: 2px; margin-bottom: 8px; font-weight: 700; letter-spacing: 0.05em; }
.badge-full { background: #b0802a; color: #fcf8ee; }
.badge-yakusha { background: #7a3a10; color: #fcf8ee; }
.footer-note { font-size: 8pt; color: #9a7a50; text-align: center; margin-top: 32px; padding-top: 10px; border-top: 1px solid #d0b880; }
.yakuwari-dept { font-size: 30pt; font-weight: 700; color: #5a1500; text-align: center; padding: 22px 0 10px; letter-spacing: 0.12em; line-height: 1.4; }
"""

# ===== THEATER THEME（映画台本スタイル）=====
CSS_THEATER = """
* { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: A4; margin: 24mm 28mm 28mm 28mm; }
body {
  font-family: 'Hiragino Kaku Gothic ProN','Yu Gothic','Meiryo',Arial,sans-serif;
  font-size: 10pt;
  line-height: 1.9;
  color: #111;
  max-width: 660px;
  margin: 0 auto;
  padding: 16px 0 30px;
  background: #fff;
}

/* タイトル：モノクロ・ミニマル */
.title-block { text-align: center; margin-bottom: 32px; padding-bottom: 0; }
.title-label { font-size: 8pt; letter-spacing: 0.6em; color: #aaa; margin-bottom: 16px; display: block; text-transform: uppercase; }
.title-main { font-size: 36pt; font-weight: 900; color: #111; letter-spacing: 0.04em; line-height: 1.15; margin: 10px 0 14px; display: block; }
.title-sub { font-size: 9.5pt; color: #666; letter-spacing: 0.2em; display: block; }
.title-divider { border: none; border-top: 2px solid #111; margin: 20px 0 0; }

/* 見出し：太線のみ */
h2 {
  font-size: 9pt; font-weight: 700; color: #444;
  margin: 34px 0 14px; padding: 0 0 6px 0;
  border-bottom: 1px solid #ccc;
  background: none; letter-spacing: 0.2em;
  text-transform: uppercase;
}
h3 { font-size: 10pt; font-weight: 700; color: #222; margin: 20px 0 8px; padding-left: 0; border-left: none; border-bottom: 1px solid #eee; padding-bottom: 4px; letter-spacing: 0.1em; }
hr { border: none; border-top: 1px solid #e0e0e0; margin: 26px 0; }

/* キャスト表 */
.char-legend { font-size: 9pt; margin: 8px 0 10px; line-height: 2.0; }
.char-legend .dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 3px; vertical-align: middle; }
table.cast-table { border-collapse: collapse; width: 100%; font-size: 9.5pt; margin: 8px 0 6px; }
table.cast-table th { background: #f0f0f0; border: 1px solid #ccc; padding: 5px 9px; font-weight: 700; text-align: left; color: #111; }
table.cast-table td { border: 1px solid #ddd; padding: 4px 9px; vertical-align: middle; }
td.cast-slot-cell { min-width: 90px; background: #fafafa; border-bottom: 2px solid #222 !important; }
p.cast-note { font-size: 8.5pt; color: #999; margin: 6px 0 0; }
.staff-notes { background: #f8f8f8; border-left: 3px solid #222; padding: 10px 14px; margin: 10px 0 14px; }
.staff-notes ul { list-style: none; padding: 0; margin: 0; }
.staff-notes li { font-size: 9.5pt; color: #333; padding: 2px 0; line-height: 1.9; }
.staff-notes li::before { content: '—'; color: #888; margin-right: 8px; }

/* ACTヘッダー：横線 + 中央テキスト */
.act-header { margin: 40px 0 16px; page-break-before: auto; text-align: center; }
.act-title {
  font-size: 11pt; font-weight: 900; color: #111;
  padding: 0;
  background: none; border: none;
  letter-spacing: 0.25em;
  display: block;
  margin-bottom: 4px;
}
.act-header::before {
  content: '';
  display: block;
  border-top: 2px solid #111;
  margin-bottom: 10px;
}
.act-header::after {
  content: '';
  display: block;
  border-top: 1px solid #bbb;
  margin-top: 10px;
}
.act-meta { font-size: 8pt; color: #888; margin: 2px 0; letter-spacing: 0.1em; }
.act-chars { font-size: 9pt; color: #444; margin: 2px 0 0; }

/* セリフ：キャラ名を中央揃え大文字で独立 */
p.dialog { margin: 8px auto 2px; max-width: 500px; line-height: 1.9; }
span.char-name {
  display: block;
  text-align: center;
  font-weight: 900;
  font-size: 9.5pt;
  letter-spacing: 0.2em;
  margin-bottom: 2px;
}
p.stage-direction {
  color: #555; font-size: 9.5pt; font-style: italic;
  margin: 6px auto 6px;
  max-width: 520px;
  padding: 0 60px;
  border-left: none;
  line-height: 1.8;
}

/* ナレーター */
blockquote.narrator {
  background: #f8f8f8; border-left: 3px solid #888;
  padding: 8px 18px; margin: 12px auto;
  max-width: 540px;
  font-size: 9.5pt; color: #333; line-height: 1.9;
}

/* キュー */
p.cue { font-size: 9.5pt; font-weight: 700; padding: 4px 10px; margin: 6px 0; border-radius: 0; line-height: 1.7; }
p.light-cue { background: #fffbeb; border: 1px solid #e8c050; border-left: 4px solid #c89020; color: #4a3000; }
p.music-cue { background: #f0f8f0; border: 1px solid #70b880; border-left: 4px solid #287848; color: #0a2818; }
p.time-cue { background: #f6f6f6; border: 1px solid #bbb; border-left: 4px solid #888; color: #444; font-weight: 400; }
p.daidogu-cue { background: #fdf4e4; border: 1px solid #c07820; border-left: 4px solid #904810; color: #3a2000; }
p.shodogu-cue { background: #f2eeff; border: 1px solid #8858b0; border-left: 4px solid #583888; color: #240840; }
p.onkyo-cue { background: #e8f6f2; border: 1px solid #38a098; border-left: 4px solid #106860; color: #062820; }
p.isho-cue { background: #fce8f0; border: 1px solid #c85898; border-left: 4px solid #983068; color: #420820; }
p.kantoku-cue { background: #eeeff8; border: 1px solid #3848b0; border-left: 4px solid #1e30a0; color: #080e3a; }

/* バッジ・フッター */
.version-badge { display: inline-block; font-size: 8.5pt; padding: 2px 10px; border-radius: 2px; margin-bottom: 8px; font-weight: 700; letter-spacing: 0.08em; }
.badge-full { background: #111; color: #fff; }
.badge-yakusha { background: #555; color: #fff; }
.footer-note { font-size: 7.5pt; color: #aaa; text-align: center; margin-top: 32px; padding-top: 8px; border-top: 1px solid #e0e0e0; letter-spacing: 0.1em; }
.yakuwari-dept { font-size: 28pt; font-weight: 900; color: #111; text-align: center; padding: 22px 0 10px; letter-spacing: 0.15em; line-height: 1.3; }
"""

# ===== FROZEN THEME（アナ雪・ポップカラフル）=====
CSS_FROZEN = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');
* { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: A4; margin: 18mm 16mm 22mm 16mm; }
body {
  font-family: 'Noto Sans JP','Hiragino Kaku Gothic ProN','Yu Gothic',sans-serif;
  font-size: 10.5pt;
  line-height: 2.0;
  color: #0a1830;
  max-width: 800px;
  margin: 0 auto;
  padding: 16px 20px 30px;
  background: #eef6ff;
}

/* タイトル：グラデーション帯 */
.title-block {
  text-align: center; margin: -16px -20px 20px; padding: 22px 20px 18px;
  background: linear-gradient(135deg, #1a6ab8 0%, #2ab8d4 50%, #6ed8f0 100%);
  color: #fff;
}
.title-label { font-size: 9pt; letter-spacing: 0.3em; color: rgba(255,255,255,0.85); margin-bottom: 8px; display: block; }
.title-main { font-size: 34pt; font-weight: 700; color: #fff; letter-spacing: 0.06em; line-height: 1.25; margin: 6px 0 10px; display: block; text-shadow: 0 2px 8px rgba(0,60,120,0.4); }
.title-sub { font-size: 10pt; color: rgba(255,255,255,0.9); letter-spacing: 0.12em; display: block; }
.title-divider { display: none; }

/* 見出し：角丸カード */
h2 {
  font-size: 12pt; font-weight: 700; color: #0a3a6a;
  margin: 24px 0 10px; padding: 8px 14px;
  border-left: 4px solid #2a9fd0;
  border-radius: 0 8px 8px 0;
  background: linear-gradient(to right, #d0eaf8, #eef6ff);
  letter-spacing: 0.05em;
}
h3 { font-size: 10.5pt; font-weight: 700; color: #0a3a7a; margin: 16px 0 6px; padding-left: 10px; border-left: 3px solid #6ac8e8; }
hr { border: none; border-top: 1px solid #b8d8ee; margin: 20px 0; }

/* キャスト表 */
.char-legend { font-size: 9.5pt; margin: 8px 0 10px; line-height: 2.2; }
.char-legend .dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 3px; vertical-align: middle; }
table.cast-table { border-collapse: collapse; width: 100%; font-size: 10pt; margin: 8px 0 6px; border-radius: 8px; overflow: hidden; }
table.cast-table th { background: #2a9fd0; border: 1px solid #1a7aaa; padding: 6px 10px; font-weight: 700; text-align: left; color: #fff; }
table.cast-table td { border: 1px solid #b0d8ee; padding: 5px 10px; vertical-align: middle; background: #fff; }
td.cast-slot-cell { min-width: 100px; background: #f0faff; border-bottom: 2px solid #2a9fd0 !important; }
p.cast-note { font-size: 9pt; color: #5a90c0; margin: 6px 0 0; font-style: italic; }
.staff-notes { background: #d8f0fa; border: 1px solid #90c8e8; border-radius: 10px; padding: 10px 14px; margin: 10px 0 14px; }
.staff-notes ul { list-style: none; padding: 0; margin: 0; }
.staff-notes li { font-size: 10pt; color: #0a2840; padding: 2px 0; line-height: 2.0; }
.staff-notes li::before { content: '❄'; color: #2a9fd0; margin-right: 7px; font-size: 9pt; }

/* ACTヘッダー：全幅グラデーション帯 */
.act-header {
  margin: 28px -20px 14px;
  page-break-before: auto;
}
.act-title {
  font-size: 14pt; font-weight: 700; color: #fff;
  padding: 12px 20px;
  background: linear-gradient(to right, #1a6ab8, #2ab8d4);
  border: none;
  letter-spacing: 0.06em;
  display: block;
}
.act-meta { font-size: 8.5pt; color: #5a90c0; margin: 6px 0 2px 20px; }
.act-chars { font-size: 10pt; font-weight: 700; color: #0a2a5a; margin: 2px 0 10px 20px; }

/* セリフ */
p.dialog { margin: 4px 0; line-height: 2.0; }
span.char-name { font-weight: 700; }
p.stage-direction {
  color: #4a78a0; font-size: 9.5pt; font-style: italic;
  margin: 4px 0 4px 16px; padding-left: 10px;
  border-left: 2px solid #a0d0e8; line-height: 1.8;
}

/* ナレーター */
blockquote.narrator {
  background: #dff0fa; border: 1px solid #90c0e0;
  border-left: 4px solid #2a9fd0; border-radius: 8px;
  padding: 8px 16px; margin: 10px 0;
  font-size: 10pt; color: #0a2040; line-height: 2.0;
}

/* キュー */
p.cue { font-size: 10.5pt; font-weight: 700; padding: 6px 12px; margin: 8px 0; border-radius: 6px; line-height: 1.7; }
p.light-cue { background: #fffbeb; border: 1px solid #f0cc70; border-left: 5px solid #d89020; color: #4a3000; }
p.music-cue { background: #e8f8f0; border: 1px solid #78d0a0; border-left: 5px solid #28a868; color: #0a3020; }
p.time-cue { background: #e8f2f8; border: 1px solid #80b0d0; border-left: 5px solid #4070a8; color: #0a1838; font-weight: 400; }
p.daidogu-cue { background: #fdf4e4; border: 1px solid #c07820; border-left: 5px solid #905010; color: #3a2000; }
p.shodogu-cue { background: #f0eeff; border: 1px solid #8058b8; border-left: 5px solid #603898; color: #200848; }
p.onkyo-cue { background: #e4f8f4; border: 1px solid #38a898; border-left: 5px solid #106868; color: #062828; }
p.isho-cue { background: #fce8f2; border: 1px solid #c05898; border-left: 5px solid #983070; color: #420828; }
p.kantoku-cue { background: #eceeff; border: 1px solid #3048b8; border-left: 5px solid #1830a8; color: #080e3c; }

/* バッジ・フッター */
.version-badge { display: inline-block; font-size: 9.5pt; padding: 2px 12px; border-radius: 6px; margin-bottom: 8px; font-weight: 700; letter-spacing: 0.05em; }
.badge-full { background: #1a6ab8; color: #fff; }
.badge-yakusha { background: #4a70b0; color: #fff; }
.footer-note { font-size: 8.5pt; color: #5a9ab8; text-align: center; margin-top: 30px; padding-top: 10px; border-top: 1px solid #b0d8ee; }
.yakuwari-dept { font-size: 30pt; font-weight: 700; color: #0a3a7a; text-align: center; padding: 22px 0 10px; letter-spacing: 0.1em; line-height: 1.3; }
"""

# ===== TATEGAKI THEME（縦書き）=====
CSS_TATEGAKI = """
* { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: A4 landscape; margin: 18mm 20mm 22mm 20mm; }
html {
  writing-mode: vertical-rl;
}
body {
  font-family: 'Hiragino Mincho ProN','Yu Mincho','MS Mincho',Georgia,serif;
  font-size: 10.5pt;
  line-height: 2.4;
  color: #1a1a1a;
  background: #fff;
  padding: 0;
}

/* ===== 横書きに戻す要素（スタッフ注意書きは縦書きのまま）===== */
table.cast-table, .char-legend,
p.cue, p.light-cue, p.music-cue, p.time-cue,
p.daidogu-cue, p.shodogu-cue, p.onkyo-cue,
p.isho-cue, p.kantoku-cue,
.version-badge, .footer-note, p.cast-note,
.title-block, hr, .act-meta, .act-chars {
  writing-mode: horizontal-tb;
  display: block;
}

/* ===== タイトル ===== */
.title-block {
  text-align: center;
  padding: 10px 16px;
  margin-bottom: 12px;
  border-bottom: 3px double #4a7cc0;
}
.title-label { font-size: 9pt; letter-spacing: 0.3em; color: #888; display: block; }
.title-main { font-size: 22pt; font-weight: 700; color: #1a3a6a; letter-spacing: 0.15em; line-height: 1.6; margin: 6px 0; display: block; }
.title-sub { font-size: 9pt; color: #555; letter-spacing: 0.1em; display: block; }
.title-divider { display: none; }

/* ===== 見出し ===== */
h2 {
  font-size: 13pt; font-weight: 700; color: #1a3a6a;
  padding: 10px 6px;
  margin: 0 0 8px 16px;
  border-right: 5px solid #4a7cc0;
  background: linear-gradient(to left, #f0f4fa, #fff);
  letter-spacing: 0.08em;
}
h3 {
  font-size: 11pt; font-weight: 700; color: #446;
  padding: 6px 4px;
  margin: 0 0 6px 10px;
  border-right: 3px solid #99aacc;
}
hr { writing-mode: horizontal-tb; border: none; border-top: 1px solid #d0d0d0; margin: 12px 0; }

/* ===== ACTヘッダー ===== */
.act-header { margin: 8px 0 10px 20px; break-before: auto; }
.act-title {
  writing-mode: vertical-rl;
  font-size: 13pt; font-weight: 700; color: #1a3a6a;
  padding: 10px 7px;
  border-right: 5px solid #4a7cc0;
  border-top: 2px solid #4a7cc0;
  background: #f0f4fa;
  letter-spacing: 0.08em;
  display: block;
  margin-bottom: 6px;
}
.act-meta { font-size: 8.5pt; color: #888; margin: 3px 4px; }
.act-chars { font-size: 9.5pt; font-weight: 700; color: #444; margin: 0 4px 8px; }

/* ===== キャスト表 ===== */
table.cast-table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 6px 0; }
table.cast-table th { background: #eef2f8; border: 1px solid #c0c8d8; padding: 4px 7px; font-weight: 700; text-align: left; color: #334; }
table.cast-table td { border: 1px solid #c8ccd8; padding: 3px 7px; vertical-align: middle; }
td.cast-slot-cell { min-width: 70px; background: #fafaf6; border-bottom: 2px solid #888 !important; }
.char-legend { font-size: 9pt; margin: 6px 0 8px; line-height: 1.9; }
.char-legend .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 3px; vertical-align: middle; }
p.cast-note { font-size: 9pt; color: #999; margin: 4px 0; font-style: italic; }

/* ===== スタッフ注意書き（縦書き強制）===== */
.staff-notes { writing-mode: vertical-rl; background: #f6f6f4; border: 1px solid #d0ccc4; border-radius: 3px; padding: 8px 12px; margin: 0 0 8px 10px; }
.staff-notes ul { writing-mode: vertical-rl; list-style: none; padding: 0; margin: 0; }
.staff-notes li { writing-mode: vertical-rl; font-size: 9.5pt; color: #333; padding: 2px 0; line-height: 1.8; }
.staff-notes li::before { content: '▸'; color: #888; margin-right: 6px; font-size: 8.5pt; }

/* ===== セリフ・ト書き ===== */
p.dialog { margin: 0 3px 5px; line-height: 2.4; }
span.char-name { font-weight: 700; }
p.stage-direction {
  color: #777; font-size: 9.5pt; font-style: italic;
  margin: 0 3px 5px 10px;
  padding-right: 8px;
  border-right: 2px solid #ddd;
  line-height: 2.0;
}

/* ===== ナレーター ===== */
blockquote.narrator {
  background: #f5f4f0;
  border-right: 4px solid #aaa;
  border-top: 1px solid #d4d0c8;
  border-bottom: 1px solid #d4d0c8;
  padding: 7px 12px;
  margin: 0 0 8px 8px;
  font-size: 10pt; color: #333; line-height: 2.2;
}

/* ===== キュー（コンパクト縦書き内横組み）===== */
p.cue {
  font-size: 9pt; font-weight: 700;
  padding: 3px 8px;
  margin: 2px 0 6px 6px;
  border-radius: 3px;
  line-height: 1.6;
  display: block;
}
p.light-cue { background: #fffbeb; border: 1px solid #e8c050; border-left: 4px solid #e0a020; color: #5a3800; }
p.music-cue { background: #f0f8f4; border: 1px solid #70c090; border-left: 4px solid #30a060; color: #174025; }
p.time-cue { background: #f4f4f2; border: 1px solid #ccc; border-left: 4px solid #999; color: #555; font-weight: 400; }
p.daidogu-cue { background: #fdf4e7; border: 1px solid #c07820; border-left: 4px solid #a06010; color: #4a2800; }
p.shodogu-cue { background: #f2eefd; border: 1px solid #8050b8; border-left: 4px solid #6040a0; color: #2a0a50; }
p.onkyo-cue { background: #e6f6f5; border: 1px solid #30a09a; border-left: 4px solid #108070; color: #083830; }
p.isho-cue { background: #fde8f0; border: 1px solid #c04898; border-left: 4px solid #a03878; color: #4a0a28; }
p.kantoku-cue { background: #eaecf4; border: 1px solid #3848b0; border-left: 4px solid #2030a0; color: #0a1040; }

/* ===== バッジ・フッター ===== */
.version-badge { display: inline-block; font-size: 9pt; padding: 2px 9px; border-radius: 4px; margin-bottom: 6px; font-weight: 700; }
.badge-full { background: #4a7cc0; color: #fff; }
.badge-yakusha { background: #6a3080; color: #fff; }
.footer-note { font-size: 8pt; color: #999; text-align: center; margin-top: 16px; padding-top: 6px; border-top: 1px solid #ddd; }
.yakuwari-dept { writing-mode: horizontal-tb; font-size: 22pt; font-weight: 700; color: #1a3a6a; text-align: center; padding: 16px 0 6px; letter-spacing: 0.1em; }
"""

# ===== PRO THEME（劇団四季・宝塚風プロ台本スタイル）=====
CSS_PRO = """
* { box-sizing: border-box; margin: 0; padding: 0; }
@page { size: A4 landscape; margin: 18mm 22mm 22mm 22mm; }
html {
  writing-mode: vertical-rl;
}
body {
  font-family: 'Hiragino Mincho ProN','Yu Mincho','MS Mincho',serif;
  font-size: 11pt;
  line-height: 2.8;
  color: #0a0a0a;
  background: #fefef8;
}

/* 役名：黒ゴシック体で統一（カラーを上書き）*/
span.char-name {
  color: #0a0a0a !important;
  font-family: 'Hiragino Kaku Gothic ProN','Yu Gothic','Meiryo',sans-serif;
  font-weight: 700;
  font-size: 9.5pt;
}

/* ===== 横書きに戻す要素（キャスト表・キューのみ）===== */
table.cast-table, .char-legend, p.cast-note,
.version-badge, .footer-note,
.act-meta, .act-chars,
.title-block, hr,
p.cue, p.light-cue, p.music-cue, p.time-cue,
p.daidogu-cue, p.shodogu-cue, p.onkyo-cue,
p.isho-cue, p.kantoku-cue {
  writing-mode: horizontal-tb;
  display: block;
}

/* ===== タイトル（横書き帯）===== */
.title-block {
  text-align: center;
  padding: 14px 20px;
  margin-bottom: 10px;
  border-bottom: 3px solid #0a0a0a;
  border-top: 3px solid #0a0a0a;
}
.title-label {
  font-size: 8.5pt; letter-spacing: 0.5em; color: #555;
  display: block; margin-bottom: 6px;
  font-family: 'Hiragino Kaku Gothic ProN','Yu Gothic','Meiryo',sans-serif;
}
.title-main {
  font-size: 24pt; font-weight: 700; color: #0a0a0a;
  letter-spacing: 0.25em; display: block; line-height: 1.4;
}
.title-sub {
  font-size: 9pt; color: #555; letter-spacing: 0.15em;
  display: block; margin-top: 5px;
  font-family: 'Hiragino Kaku Gothic ProN','Yu Gothic','Meiryo',sans-serif;
}
.title-divider { display: none; }

/* ===== 見出し ===== */
h2 {
  font-size: 12pt; font-weight: 700; color: #0a0a0a;
  padding: 10px 5px; margin: 0 0 8px 14px;
  border-right: 4px solid #0a0a0a;
  background: none; letter-spacing: 0.1em;
}
h3 {
  font-size: 10.5pt; font-weight: 700; color: #222;
  padding: 6px 4px; margin: 0 0 6px 8px;
  border-right: 2px solid #555;
}
hr { writing-mode: horizontal-tb; border: none; border-top: 1px solid #888; margin: 10px 0; }

/* ===== ACTヘッダー ===== */
.act-header { margin: 6px 0 10px 18px; }
.act-title {
  writing-mode: vertical-rl;
  font-size: 13pt; font-weight: 700; color: #0a0a0a;
  padding: 12px 5px;
  border-right: 4px solid #0a0a0a;
  border-top: 1px solid #0a0a0a;
  letter-spacing: 0.14em; display: block; margin-bottom: 5px;
  background: none;
}
.act-meta { font-size: 8pt; color: #666; margin: 3px 4px; }
.act-chars { font-size: 9pt; color: #333; font-weight: 700; margin: 0 4px 8px; }

/* ===== キャスト表 ===== */
table.cast-table { border-collapse: collapse; width: 100%; font-size: 9pt; }
table.cast-table th { background: #e0e0e0; border: 1px solid #888; padding: 4px 8px; font-weight: 700; color: #0a0a0a; }
table.cast-table td { border: 1px solid #bbb; padding: 3px 8px; vertical-align: middle; color: #0a0a0a; }
td.cast-slot-cell { min-width: 70px; border-bottom: 2px solid #0a0a0a !important; }
.char-legend { font-size: 8.5pt; margin: 5px 0 8px; line-height: 1.8; }
.char-legend .dot { display: inline-block; width: 7px; height: 7px; border-radius: 0; margin-right: 3px; vertical-align: middle; background: #444 !important; }
.char-legend span { color: #0a0a0a !important; }
p.cast-note { font-size: 8.5pt; color: #666; margin: 4px 0; }

/* ===== スタッフ注意書き（縦書き）===== */
.staff-notes { background: #f5f5f0; border-right: 3px solid #555; padding: 8px 10px; margin: 0 0 8px 8px; }
.staff-notes ul { list-style: none; padding: 0; margin: 0; }
.staff-notes li { font-size: 9.5pt; color: #1a1a1a; padding: 2px 0; line-height: 2.4; }
.staff-notes li::before { content: '◆'; color: #555; margin-right: 4px; font-size: 8pt; }

/* ===== セリフ・ト書き ===== */
p.dialog { margin: 0 2px 6px; line-height: 2.8; }
p.stage-direction {
  color: #444; font-size: 9pt; font-style: normal;
  margin: 0 2px 5px 8px; padding-right: 6px;
  border-right: 1px solid #bbb; line-height: 2.4;
}

/* ===== ナレーター ===== */
blockquote.narrator {
  border-right: 3px solid #555;
  border-top: 1px solid #ccc; border-bottom: 1px solid #ccc;
  padding: 6px 10px; margin: 0 0 8px 6px;
  font-size: 10pt; color: #1a1a1a; line-height: 2.6;
  background: #f8f8f4;
}

/* ===== キュー（横書き小ボックス）===== */
p.cue { font-size: 8.5pt; font-weight: 700; padding: 2px 7px; margin: 2px 0 4px 5px; border-radius: 1px; line-height: 1.5; }
p.light-cue { background: #fffbe8; border: 1px solid #c09010; border-left: 3px solid #907000; color: #382600; }
p.music-cue { background: #eef6ee; border: 1px solid #508050; border-left: 3px solid #207040; color: #082010; }
p.time-cue { background: #f2f2f2; border: 1px solid #999; border-left: 3px solid #666; color: #444; font-weight: 400; }
p.daidogu-cue { background: #fdf0e0; border: 1px solid #a05808; border-left: 3px solid #784008; color: #301600; }
p.shodogu-cue { background: #f0eeff; border: 1px solid #6848a0; border-left: 3px solid #483080; color: #1a0838; }
p.onkyo-cue { background: #e4f4f4; border: 1px solid #288888; border-left: 3px solid #106060; color: #042828; }
p.isho-cue { background: #fce8f0; border: 1px solid #a04888; border-left: 3px solid #883070; color: #380626; }
p.kantoku-cue { background: #eceef6; border: 1px solid #2838a0; border-left: 3px solid #182898; color: #060c38; }

/* ===== バッジ・フッター ===== */
.version-badge { display: inline-block; font-size: 8pt; padding: 1px 8px; border: 1px solid #444; margin-bottom: 6px; font-weight: 700; border-radius: 1px; }
.badge-full { background: #0a0a0a; color: #fafaf8; }
.badge-yakusha { background: #333; color: #fafaf8; }
.footer-note { font-size: 7.5pt; color: #888; text-align: center; margin-top: 12px; padding-top: 6px; border-top: 1px solid #ccc; }
.yakuwari-dept { writing-mode: horizontal-tb; font-size: 20pt; font-weight: 700; color: #0a0a0a; text-align: center; padding: 14px 0 6px; letter-spacing: 0.12em; line-height: 1.4; }
"""

THEMES = {
    'default': CSS_DEFAULT,
    'washi':   CSS_WASHI,
    'theater': CSS_THEATER,
    'frozen':  CSS_FROZEN,
    'tategaki': CSS_TATEGAKI,
    'pro':     CSS_PRO,
}

# ===== 共通：コードブロック（```）・インラインSVG図（```svg）用スタイル =====
# すべてのテーマに追記する（--yakuwari で使う舞台構成.md の SVG 図を正しく表示するため）
CSS_CODE_SVG = """
/* ===== H4 ===== */
h4 {
  font-size: 10.5pt;
  font-weight: 700;
  color: #555;
  margin: 14px 0 6px;
  padding: 3px 0 3px 8px;
  border-left: 3px solid #bbb;
}
/* ===== CODE BLOCK / SVG FIGURE ===== */
pre {
  background: #f5f6f8;
  border: 1px solid #d4d8e0;
  border-radius: 4px;
  padding: 10px 14px;
  margin: 12px 0;
  overflow-x: auto;
}
pre code {
  font-family: 'Consolas','SFMono-Regular','Menlo','Courier New',monospace;
  font-size: 9pt;
  line-height: 1.55;
  color: #2a2a2a;
  white-space: pre;
}
svg {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 14px auto;
  writing-mode: horizontal-tb;
}
figure.svg-figure {
  margin: 14px 0 20px;
  text-align: center;
  page-break-inside: avoid;
  break-inside: avoid;
  writing-mode: horizontal-tb;
}
figure.svg-figure figcaption {
  font-size: 9pt;
  color: #777;
  margin-top: 4px;
  letter-spacing: 0.03em;
}
"""
THEMES = {name: css + CSS_CODE_SVG for name, css in THEMES.items()}


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def render_char_name(name):
    color = CHAR_COLORS.get(name, '#333')
    return f'<span class="char-name" style="color:{color}">{esc(name)}</span>'

def render_inline(text):
    parts = re.split(r'(\*\*[^*]+?\*\*)', text)
    out = []
    for part in parts:
        if part.startswith('**') and part.endswith('**') and len(part) > 4:
            inner = part[2:-2]
            if inner in CHAR_COLORS:
                out.append(render_char_name(inner))
            else:
                out.append(f'<strong>{esc(inner)}</strong>')
        else:
            sub = re.split(r'(\*[^*]+?\*)', part)
            for s in sub:
                if s.startswith('*') and s.endswith('*') and len(s) > 2:
                    out.append(f'<em>{esc(s[1:-1])}</em>')
                else:
                    out.append(esc(s))
    return ''.join(out)

def process_dialog(stripped):
    m = re.match(r'^\*\*([^*]+)\*\*(.+)$', stripped)
    if not m:
        return None
    char_name, rest = m.group(1), m.group(2)
    if not rest.startswith('「'):
        return None
    return f'<p class="dialog">{render_char_name(char_name)}{esc(rest)}</p>'

def render_table(rows, in_cast_table=False):
    if len(rows) < 3:
        return ''
    html = ['<table class="cast-table">']
    h_cells = [c.strip() for c in rows[0].split('|') if c.strip()]
    html.append('<thead><tr>' + ''.join(f'<th>{esc(c)}</th>' for c in h_cells) + '</tr></thead><tbody>')
    for row in rows[2:]:
        cells = [c.strip() for c in row.split('|')]
        if cells and cells[0] == '': cells = cells[1:]
        if cells and cells[-1] == '': cells = cells[:-1]
        html.append('<tr>')
        for j, cell in enumerate(cells):
            if j == 0 and in_cast_table:
                # Color the role name
                color = CHAR_COLORS.get(cell, '#222')
                html.append(f'<td style="color:{color};font-weight:bold">{esc(cell)}</td>')
            elif j in (1, 2) and cell in ('-', '—', ''):
                html.append('<td class="cast-slot-cell"></td>')
            else:
                html.append(f'<td>{render_inline(cell)}</td>')
        html.append('</tr>')
    html.append('</tbody></table>')
    return '\n'.join(html)

def build_char_legend():
    parts = []
    for name in CHAR_ORDER:
        color = CHAR_COLORS[name]
        parts.append(
            f'<span class="dot" style="background:{color}"></span>'
            f'<span style="color:{color};font-weight:bold;margin-right:14px">{esc(name)}</span>'
        )
    return f'<div class="char-legend">{"".join(parts)}</div>'

def convert(md_content, yakusha=False, staff=False, yakuwari=False):
    lines = md_content.split('\n')
    out = []
    i = 0
    in_staff_section = False
    in_staff_notes = False
    staff_note_items = []
    table_rows = []
    footer_text = None

    def flush_table():
        nonlocal table_rows
        if table_rows:
            # Check if this is the cast table (has | 役名 | header)
            is_cast = '役名' in table_rows[0] if table_rows else False
            if is_cast:
                out.append(build_char_legend())
            out.append(render_table(table_rows, in_cast_table=is_cast))
            table_rows = []

    def flush_staff_notes():
        nonlocal staff_note_items, in_staff_notes
        if staff_note_items:
            items_html = ''.join(f'<li>{render_inline(item)}</li>' for item in staff_note_items)
            out.append(f'<div class="staff-notes"><ul>{items_html}</ul></div>')
            staff_note_items = []
        in_staff_notes = False

    while i < len(lines):
        stripped = lines[i].strip()

        # Staff section skip for yakusha
        if in_staff_section:
            if stripped == '---':
                in_staff_section = False
                out.append('<hr>')
            i += 1
            continue

        # Empty line
        if not stripped:
            flush_table()
            flush_staff_notes()
            i += 1
            continue

        # Fenced code block (``` ... ```)
        # - ```svg : emit the block as raw HTML (unescaped) so inline SVG renders
        # - ``` / ```lang : fall back to <pre><code> monospaced block (escaped)
        if stripped.startswith('```'):
            flush_table()
            flush_staff_notes()
            lang = stripped[3:].strip().lower()
            i += 1
            block_lines = []
            while i < len(lines) and not lines[i].lstrip().startswith('```'):
                block_lines.append(lines[i])
                i += 1
            if i < len(lines):  # skip the closing fence
                i += 1
            if lang == 'svg':
                out.append('\n'.join(block_lines))
            else:
                code = '\n'.join(block_lines)
                out.append(f'<pre><code>{esc(code)}</code></pre>')
            continue

        # Table rows
        if stripped.startswith('|'):
            flush_staff_notes()
            table_rows.append(stripped)
            i += 1
            continue
        else:
            flush_table()

        # H1 → title block
        if re.match(r'^# [^#]', stripped):
            text = stripped[2:]
            if yakuwari:
                out.append(f'<div class="yakuwari-dept">{esc(text)}</div>')
            # else: title is handled in build_html
            i += 1
            continue

        # H2 (## ACT ... or ## キャスト... or ## 演出...)
        if re.match(r'^## [^#]', stripped):
            flush_staff_notes()
            text = stripped[3:]

            # Staff section
            if '演出・スタッフ' in text:
                if yakusha:
                    in_staff_section = True
                    i += 1
                    continue
                else:
                    # Render as h2, next lines as staff notes box
                    out.append(f'<h2>{render_inline(text)}</h2>')
                    in_staff_notes = True
                    i += 1
                    continue

            # ACT heading
            m_act = re.match(r'^ACT\s+(\d+)[　\s]*(.*)$', text)
            if m_act:
                act_num = m_act.group(1)
                act_title = m_act.group(2)
                out.append(f'<div class="act-header"><div class="act-title">ACT {esc(act_num)}　{render_inline(act_title)}</div>')
                # Look ahead for timing and cast lines
                i += 1
                while i < len(lines):
                    next_s = lines[i].strip()
                    if not next_s:
                        i += 1
                        continue
                    if next_s.startswith('**（') and next_s.endswith('）**'):
                        timing = next_s[3:-3]
                        out.append(f'<div class="act-meta">{esc(timing)}</div>')
                        i += 1
                    elif next_s.startswith('**【登場人物】'):
                        chars = next_s.replace('**', '')
                        out.append(f'<div class="act-chars">{esc(chars)}</div>')
                        i += 1
                    else:
                        break
                out.append('</div>')
                continue
            else:
                out.append(f'<h2>{render_inline(text)}</h2>')
                i += 1
                continue

        # H4
        if re.match(r'^#### ', stripped):
            flush_staff_notes()
            out.append(f'<h4>{render_inline(stripped[5:])}</h4>')
            i += 1
            continue

        # H3
        if re.match(r'^### ', stripped):
            flush_staff_notes()
            out.append(f'<h3>{render_inline(stripped[4:])}</h3>')
            i += 1
            continue

        # Staff notes list items
        if in_staff_notes and stripped.startswith('- '):
            staff_note_items.append(stripped[2:])
            i += 1
            continue

        # Regular list items (outside staff notes)
        if stripped.startswith('- ') and not in_staff_notes:
            items = []
            while i < len(lines) and lines[i].strip().startswith('- '):
                items.append(lines[i].strip()[2:])
                i += 1
            html_items = ''.join(f'<li>{render_inline(item)}</li>' for item in items)
            out.append(f'<ul>{html_items}</ul>')
            continue

        # HR
        if stripped == '---':
            flush_staff_notes()
            out.append('<hr>')
            i += 1
            continue

        # Blockquote (narrator)
        if stripped.startswith('>'):
            flush_staff_notes()
            block = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                bl = lines[i].strip()[1:].strip()
                block.append(bl)
                i += 1
            rendered = '<br>'.join(render_inline(bl) for bl in block if bl)
            out.append(f'<blockquote class="narrator">{rendered}</blockquote>')
            continue

        # Light cue
        if stripped.startswith('💡'):
            flush_staff_notes()
            if not yakusha:
                rest = stripped[len('💡'):].strip()
                out.append(f'<p class="cue light-cue">💡 {render_inline(rest)}</p>')
            i += 1
            continue

        # Music cue
        if stripped.startswith('🎵'):
            flush_staff_notes()
            rest = stripped[len('🎵'):].strip()
            out.append(f'<p class="cue music-cue">🎵 {render_inline(rest)}</p>')
            i += 1
            continue

        # Time cue
        if stripped.startswith('⏱'):
            flush_staff_notes()
            if not yakusha:
                rest = stripped[len('⏱'):].strip()
                out.append(f'<p class="cue time-cue">⏱ {esc(rest)}</p>')
            i += 1
            continue

        # 大道具 cue
        if stripped.startswith('🎨'):
            flush_staff_notes()
            if not yakusha:
                rest = stripped[len('🎨'):].strip()
                out.append(f'<p class="cue daidogu-cue">🎨 {render_inline(rest)}</p>')
            i += 1
            continue

        # 小道具 cue
        if stripped.startswith('📦'):
            flush_staff_notes()
            if not yakusha:
                rest = stripped[len('📦'):].strip()
                out.append(f'<p class="cue shodogu-cue">📦 {render_inline(rest)}</p>')
            i += 1
            continue

        # 音響 cue
        if stripped.startswith('🔊'):
            flush_staff_notes()
            if not yakusha:
                rest = stripped[len('🔊'):].strip()
                out.append(f'<p class="cue onkyo-cue">🔊 {render_inline(rest)}</p>')
            i += 1
            continue

        # 衣装 cue
        if stripped.startswith('👗'):
            flush_staff_notes()
            if not yakusha:
                rest = stripped[len('👗'):].strip()
                out.append(f'<p class="cue isho-cue">👗 {render_inline(rest)}</p>')
            i += 1
            continue

        # 舞台監督 cue
        if stripped.startswith('🎬'):
            flush_staff_notes()
            if not yakusha:
                rest = stripped[len('🎬'):].strip()
                out.append(f'<p class="cue kantoku-cue">🎬 {render_inline(rest)}</p>')
            i += 1
            continue

        # Stage direction
        m = re.match(r'^\*（(.+)）\*$', stripped)
        if m:
            flush_staff_notes()
            out.append(f'<p class="stage-direction">（{esc(m.group(1))}）</p>')
            i += 1
            continue

        # Dialog
        d = process_dialog(stripped)
        if d:
            flush_staff_notes()
            out.append(d)
            i += 1
            continue

        # Cast note ※
        if stripped.startswith('※'):
            flush_staff_notes()
            out.append(f'<p class="cast-note">{esc(stripped)}</p>')
            i += 1
            continue

        # 【登場人物】 lines outside ACT blocks
        if stripped.startswith('**【登場人物】'):
            flush_staff_notes()
            out.append(f'<p class="act-chars">{render_inline(stripped)}</p>')
            i += 1
            continue

        # Footer note (last line after final ---)
        if stripped and not stripped.startswith('#') and not stripped.startswith('*') and not stripped.startswith('>'):
            # Check if it looks like a footer (not a dialog, not a cue)
            if '演出の詳細はリハーサルで随時調整' in stripped:
                footer_text = stripped
                i += 1
                continue

        # Generic paragraph
        flush_staff_notes()
        out.append(f'<p>{render_inline(stripped)}</p>')
        i += 1

    flush_table()
    flush_staff_notes()

    if footer_text:
        out.append(f'<div class="footer-note">{esc(footer_text)}</div>')

    return '\n'.join(out)

def build_html(body_html, yakusha=False, staff=False, yakuwari=False, theme='default'):
    css = THEMES.get(theme, CSS_DEFAULT)

    if yakuwari:
        return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>役割書</title>
<style>{css}</style>
</head>
<body>
{body_html}
</body>
</html>'''

    if yakusha:
        badge = '【役者用】'
        badge_cls = 'badge-yakusha'
        title_suffix = '役者用'
    else:
        badge = '【完全版】'
        badge_cls = 'badge-full'
        title_suffix = '完全版'

    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>台本：アナと雪の女王 {esc(title_suffix)}</title>
<style>{css}</style>
</head>
<body>
<span class="version-badge {badge_cls}">{badge}</span>
<div class="title-block">
  <div class="title-label">文 化 祭　舞 台 公 演　台 本</div>
  <div class="title-main">アナと雪の女王</div>
  <div class="title-sub">上演時間：約40分 ／ クラス：3年D組</div>
</div>
<hr class="title-divider">
{body_html}
</body>
</html>'''

if __name__ == '__main__':
    yakusha = '--yakusha' in sys.argv
    yakuwari = '--yakuwari' in sys.argv

    # --theme <name> 指定
    theme = 'washi'
    if '--theme' in sys.argv:
        idx = sys.argv.index('--theme')
        if idx + 1 < len(sys.argv):
            theme = sys.argv[idx + 1]

    args = [a for a in sys.argv[1:] if not a.startswith('--') and a not in THEMES.values()]
    # Remove theme name from args if it appears after --theme
    if '--theme' in sys.argv:
        idx = sys.argv.index('--theme')
        theme_name = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else 'default'
        args = [a for a in args if a != theme_name]

    if len(args) < 2:
        print('Usage: python md_to_html.py [--yakusha|--yakuwari] [--theme washi|theater|frozen|tategaki] input.md output.html')
        sys.exit(1)
    with open(args[0], encoding='utf-8') as f:
        md = f.read()
    body = convert(md, yakusha=yakusha, yakuwari=yakuwari)
    html_out = build_html(body, yakusha=yakusha, yakuwari=yakuwari, theme=theme)
    with open(args[1], 'w', encoding='utf-8') as f:
        f.write(html_out)
    print(f'Written {len(html_out)} chars -> {args[1]} [theme: {theme}]')
