# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Blender: render a list of variants to one labelled sheet.
blender -b --factory-startup --python tools/test_variants.py -- out_name.png variants.json
variants.json: [[key, style, seed, {overrides}, "caption"], ...]"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'tools'))
import bpy
import render_lib as RL
from jiuye_yingzao import catalog

a = sys.argv[sys.argv.index('--') + 1:]
out_name, spec = a[0], json.loads(Path(a[1]).read_text(encoding='utf-8'))
sc = RL.reset(); RL.ground(800); sc.render.resolution_x = 640; sc.render.resolution_y = 480
tmp = ROOT / 'catalog' / 'variants'; tmp.mkdir(parents=True, exist_ok=True); shots = []
for k, (key, style, seed, over, cap) in enumerate(spec):
    root = catalog.generate(key, style, seed, over.pop('lod', 1), **over)
    stack = [root]; obs = []
    while stack:
        o = stack.pop(); stack.extend(o.children)
        if o.type == 'MESH':
            obs.append(o)
    f = tmp / f'{Path(out_name).stem}_{k:02d}.png'
    RL.frame_camera(obs, f, azimuth=-30, elevation=24, margin=1.05)
    shots.append((str(f), cap, int(root.get('lyz_tris', 0))))
    for o in [root] + obs:
        bpy.data.objects.remove(o, do_unlink=True)
    print('VARIANT', k, cap, flush=True)
(tmp / (Path(out_name).stem + '.json')).write_text(json.dumps(shots, ensure_ascii=False), encoding='utf-8')
print('VARIANTS_DONE', len(shots))
