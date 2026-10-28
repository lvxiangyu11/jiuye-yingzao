# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Compose catalog/variants/<name>.json (from test_variants.py) into catalog/<name>.png. py -3.12 tools/sheet_from.py name [cols]"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
name = sys.argv[1]; cols = int(sys.argv[2]) if len(sys.argv) > 2 else 4
shots = json.loads((ROOT / 'catalog/variants' / f'{name}.json').read_text(encoding='utf-8'))
f = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 18); TW, TH = 480, 360
out = Image.new('RGB', (cols * TW, ((len(shots) + cols - 1) // cols) * (TH + 34)), (238, 236, 230)); d = ImageDraw.Draw(out)
for i, (p, cap, tris) in enumerate(shots):
    x = (i % cols) * TW; y = (i // cols) * (TH + 34)
    out.paste(Image.open(p).convert('RGB').resize((TW, TH)), (x, y)); d.text((x + 6, y + TH + 5), f'{cap} · {tris:,} 面', fill=(20, 20, 20), font=f)
out.save(ROOT / 'catalog' / f'{name}.png'); print(out.size)
