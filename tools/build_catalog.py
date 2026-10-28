# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Blender: generate every catalog entry, render one thumbnail each, write catalog/report.json.

blender -b --factory-startup --python tools/build_catalog.py -- [--only key1,key2] [--variants N] [--lod 1] [--export]
"""
import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'tools'))
import bpy
import render_lib as RL
from jiuye_yingzao import catalog, export
from jiuye_yingzao.gen import building as B

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(name, default=None):
    return args[args.index(name) + 1] if name in args else default
only = set(arg('--only', '').split(',')) - {''}
variants = int(arg('--variants', '2')); lod = int(arg('--lod', '1')); do_export = '--export' in args
OUT = ROOT / 'catalog'; THUMBS = OUT / 'thumbs'; THUMBS.mkdir(parents=True, exist_ok=True)
EXP = OUT / 'glb'

sc = RL.reset(); RL.ground(2000)
sc.render.resolution_x = 720; sc.render.resolution_y = 520
try:
    sc.eevee.taa_render_samples = 16
except AttributeError:
    pass


def remove_tree(root):
    stack = [root]; obs = []
    while stack:
        o = stack.pop(); obs.append(o); stack.extend(o.children)
    for o in obs:
        me = o.data if o.type == 'MESH' else None
        bpy.data.objects.remove(o, do_unlink=True)
        if me and me.users == 0:
            bpy.data.meshes.remove(me)


def mesh_objects(root):
    stack = [root]; out = []
    while stack:
        o = stack.pop(); stack.extend(o.children)
        if o.type == 'MESH':
            out.append(o)
    return out


jobs = []
for key, label, cat, group, styles in catalog.entries():
    if only and key not in only:
        continue
    pref = [s for s in styles if s == 'modern' or not B.STYLES.get(s, {}).get('deemphasized')]
    picks = pref[:variants] if cat in ('building', 'special', 'compound') else pref[:1]
    for i, st in enumerate(picks):
        jobs.append((key, label, cat, group, st, i + 1))

report = []
for key, label, cat, group, st, seed in jobs:
    t0 = time.time(); rec = dict(key=key, label=label, category=cat, group=group, style=st, seed=seed)
    try:
        root = catalog.generate(key, None if st == 'modern' else st, seed, lod)
        bpy.context.view_layer.update()
        obs = mesh_objects(root)
        rec['objects'] = len(obs); rec['tris'] = int(root.get('lyz_tris', 0))
        pts = [o.matrix_world @ __import__('mathutils').Vector(c) for o in obs for c in o.bound_box]
        rec['size_m'] = [round(max(p[i] for p in pts) - min(p[i] for p in pts), 2) for i in range(3)]
        rec['spec'] = json.loads(root.get('lyz_spec', '{}')) if root.get('lyz_spec') else {}
        rec['gen_s'] = round(time.time() - t0, 2)
        img = THUMBS / f'{key}__{st}__{seed}.png'
        RL.frame_camera(obs, img, azimuth=-32, elevation=30, margin=1.08)
        rec['thumb'] = str(img.relative_to(OUT))
        if do_export:
            rec['glb'] = str(export.export_root(root, EXP / f'{key}__{st}__{seed}.glb').relative_to(OUT))
        remove_tree(root); rec['ok'] = True
    except Exception as e:
        rec['ok'] = False; rec['error'] = ''.join(traceback.format_exception_only(type(e), e)).strip(); rec['trace'] = traceback.format_exc()[-1500:]
        for o in list(bpy.data.objects):
            if o.name not in ('Sun', 'Ground'):
                bpy.data.objects.remove(o, do_unlink=True)
    rec['total_s'] = round(time.time() - t0, 2)
    report.append(rec)
    print('CATALOG', key, st, 'OK' if rec['ok'] else 'FAIL ' + rec.get('error', ''), rec.get('tris'), rec['total_s'], flush=True)

name = 'report.json' if not only else 'report_partial.json'
(OUT / name).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
print('CATALOG_DONE', sum(r['ok'] for r in report), 'of', len(report))
