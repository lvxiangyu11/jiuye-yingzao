# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Compose catalog/thumbs into labelled contact sheets per category. Run: py -3.12 tools/compose_sheets.py"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / 'catalog'
R = [r for r in json.loads((OUT / 'report.json').read_text(encoding='utf-8')) if r['ok']]
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 22); small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 16)
TW, TH = 360, 260; CAP = 56; COLS = 6
NAMES = {'building': '单体', 'special': '特殊结构', 'compound': '组群', 'modern': '现代'}
for cat in ('building', 'special', 'compound', 'modern'):
    items = [r for r in R if r['category'] == cat]
    if cat == 'modern':
        items += [r for r in R if r['category'] == 'compound'][:0]
    rows = (len(items) + COLS - 1) // COLS
    sheet = Image.new('RGB', (COLS * TW, rows * (TH + CAP) + 60), (238, 236, 230)); d = ImageDraw.Draw(sheet)
    d.text((16, 14), f'九野营造 · {NAMES[cat]}（{len(items)} 个样例，LOD1）', fill=(30, 30, 30), font=font)
    for i, r in enumerate(items):
        x = (i % COLS) * TW; y = 60 + (i // COLS) * (TH + CAP)
        im = Image.open(OUT / r['thumb']).convert('RGB').resize((TW, TH)); sheet.paste(im, (x, y))
        d.text((x + 8, y + TH + 4), f"{r['label']}", fill=(20, 20, 20), font=small)
        d.text((x + 8, y + TH + 28), f"{r['style']} · 种子{r['seed']} · {r['tris']:,} 面", fill=(90, 90, 90), font=small)
    sheet.save(OUT / f'sheet_{cat}.png')
    print(cat, len(items))
