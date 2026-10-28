# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
import sys, json, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'tools'))
import bpy, render_lib as RL
from jiuye_yingzao import catalog
a = sys.argv[sys.argv.index('--') + 1:]
RL.reset(); RL.ground(400)
ov = json.loads(a[4]); root = catalog.generate(a[0], a[1], int(a[2]), ov.pop('lod', 1), **ov)
obs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Ground']
if root.get('lyz_site'):                                   # sloped test ground through the retaining wedge
    st = json.loads(root['lyz_site']); g = bpy.data.objects['Ground']; k = st['slope'] / (st['y_back'] - st['y_front'])
    g.rotation_euler = (math.atan(k), 0, 0); g.location = (0, st['y_back'], 0)
if len(a) > 8:                                             # frame only these parts (e.g. Platform,Railings)
    keys = a[8].split(','); obs = [o for o in obs if any(k in o.name for k in keys)] or obs
RL.frame_camera(obs, ROOT / 'catalog' / a[3], azimuth=float(a[5]) if len(a) > 5 else -28, elevation=float(a[6]) if len(a) > 6 else 22, margin=float(a[7]) if len(a) > 7 else .95)
