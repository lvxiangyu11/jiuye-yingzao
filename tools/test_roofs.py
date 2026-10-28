# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Blender: build every roof form on a simple box and render. blender -b --factory-startup --python tools/test_roofs.py"""
import sys, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'tools'))
import bpy
import render_lib as RL
from jiuye_yingzao.core import mesh as M, materials, rules as R
from jiuye_yingzao.gen.roof import RoofModel

sc = RL.reset(); RL.ground()
mats = materials.library()
forms = [('wudian', {}), ('xieshan', {}), ('xuanshan', {}), ('yingshan', {}), ('juanpeng', {}), ('luding', {'flat_t': .45}),
         ('cuanjian', {'sides': 4}), ('cuanjian', {'sides': 6}), ('cuanjian', {'sides': 8}), ('yuan', {}), ('danpo', {}), ('skirt', {'flat_t': .55})]
objs = []
for k, (form, kw) in enumerate(forms):
    w, d = (8.0, 6.0) if form not in ('cuanjian', 'yuan') else (5.0, 5.0)
    root = bpy.data.objects.new(f'Roof_{form}_{k}', None); sc.collection.objects.link(root)
    ox = (k % 4) * 16 - 24; oy = (k // 4) * 16 - 16; root.location = (ox, oy, 0)
    body = M.Part('Body'); roofp = M.Part('Roof'); timber = M.Part('Timber'); walls = M.Part('Walls')
    M.box_minmax(body, (-w / 2, -d / 2, 0), (w / 2, d / 2, 3.2), 'plaster_white')
    if form == 'danpo':
        pts = R.folk_pitch(2 * d, 2, .45)
        sec = R.Section([(s, z / 2) for s, z in pts], d, .8, .4)
    elif form in ('cuanjian', 'yuan'):
        pts = R.song_juzhe(d, 3, 'dian'); pts[0] = (0, pts[0][1] * 1.45)
        sec = R.Section(pts, d / 2, .9, .5)
    elif form == 'skirt':
        sec = R.Section([(0, 1.2), (1, 0)], d / 2, .9, .5)
    else:
        sec = R.Section(R.song_juzhe(d, 3, 'ting'), d / 2, 1.0, .6, juanpeng=.6 if form == 'juanpeng' else 0)
    model = RoofModel(form, w / 2, d / 2, 3.4, sec, 1.6, corner_lift=.35 if form in ('wudian', 'xieshan', 'cuanjian', 'skirt', 'luding') else 0,
                      corner_out=.2, shengqi=.06, chuji=R.chuji(4), lod=0, ridge='chiwei' if form in ('wudian', 'xieshan') else 'raised',
                      ridge_h=.55, hip_beasts=3, **kw)
    model.build(roofp, timber, walls)
    for p in (body, roofp, timber, walls):
        ob = p.finish(root, sc.collection, mats)
        if ob: objs.append(ob)
    print('form', form, 'tris', roofp.tri_count() + timber.tri_count())
bpy.context.view_layer.update()
out = ROOT / 'catalog/test_roofs.png'
RL.frame_camera(objs, out, azimuth=-30, elevation=38)
print('RENDERED', out)
