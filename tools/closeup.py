# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""blender -b --factory-startup --python tools/closeup.py -- type style seed out.png [azimuth elevation]"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'tools'))
import bpy, render_lib as RL
from jiuye_yingzao import catalog
a = sys.argv[sys.argv.index('--') + 1:]
RL.reset(); RL.ground(400)
root = catalog.generate(a[0], a[1], int(a[2]), int(a[6]) if len(a) > 6 else 1)
obs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Ground']
RL.frame_camera(obs, ROOT / 'catalog' / a[3], azimuth=float(a[4]) if len(a) > 4 else -32, elevation=float(a[5]) if len(a) > 5 else 30, margin=.75)
