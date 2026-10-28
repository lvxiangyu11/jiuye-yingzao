# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
import sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import bpy, addon_utils
import jiuye_yingzao as A
A.register()
sc = bpy.context.scene; p = sc.lyz
p.category = 'building'; p.kind = 'tingtang'; p.style = 'lanxi'; p.seed = 4
with bpy.context.temp_override(collection=sc.collection):
    print('GEN', bpy.ops.lyz.generate(reseed=False))
root = [o for o in bpy.data.objects if o.parent is None and o.get('lyz_type')][0]
print('ROOT', root.name, root['lyz_tris'])
p.export_dir = os.environ['TEMP'] + '/lyz_test/'
bpy.context.view_layer.objects.active = root
print('EXP', bpy.ops.lyz.export())
f = Path(p.export_dir) / (root.name + '.glb'); print('GLB', f.exists(), f.stat().st_size if f.exists() else 0)
A.unregister(); print('ADDON_OK')
