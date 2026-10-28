# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Blender: generate a list of building types and render a contact sheet.
blender -b --factory-startup --python tools/test_buildings.py -- type:style ... (default: a mixed sample)"""
import sys, math, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'tools'))
import bpy
import render_lib as RL
from jiuye_yingzao.gen import building as B
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
out = ROOT / 'catalog' / (args[0] if args and args[0].endswith('.png') else 'test_buildings.png')
items = [a for a in args if ':' in a] or ['zhengfang:lanxi', 'shop:lanxi', 'tingtang:song', 'dadian:song', 'dian_fujie:song', 'louge:song',
                                           'ting8:jiangnan', 'loufang:hui', 'zhengfang:lingnan', 'shop2:minnan', 'diaojiaolou:ganlan', 'maowu:north_folk']
sc = RL.reset(); RL.ground(800)
objs = []; report = []; cols = 4; cell = 34
for k, it in enumerate(items):
    t, st = it.split(':')[:2]; seed = int(it.split(':')[2]) if it.count(':') >= 2 else 1
    root = B.generate(t, st, seed, lod=1)
    root.location = ((k % cols) * cell - cell * 1.5, (k // cols) * cell, 0)
    objs += list(root.children); report.append((it, root['lyz_tris']))
    print('BUILT', it, root['lyz_tris'])
bpy.context.view_layer.update()
RL.frame_camera(objs, out, azimuth=-28, elevation=34, margin=1.0)
print('RENDERED', out, json.dumps(report))
