# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Modern residential block (现代居民楼), wrapping vendor/xingfuli (MIT, Copyright (c) 2026 kang340).

The upstream scripts build one fixed scene from module-level constants. Here the modules are loaded
from source with the constants patched (floors, random seeds), the build functions are called without
the scene reset/render setup, and the resulting objects are converted to meshes and joined per upstream
collection under one root. Upstream materials are procedural node trees; bake them before exporting to
Unity (see 技术手册 §导出).
"""
import importlib.util
import re
import sys
import types
from pathlib import Path

import bpy

VENDOR = Path(__file__).resolve().parents[1] / 'vendor' / 'xingfuli'


# Upstream targets Blender 5.2, where some sockets are named 'Factor'; Blender 4.x calls them 'Fac'.
_COMPAT = """
def _sock(coll, name):
    if name in coll.keys():
        return coll[name]
    alt = {'Factor': 'Fac', 'Fac': 'Factor'}.get(name, name)
    return coll[alt]
"""


def _load(name, patches=()):
    src = (VENDOR / f'{name}.py').read_text(encoding='utf-8')
    for pat, rep in patches:
        src, n = re.subn(pat, rep, src, count=1, flags=re.M)
        if not n:
            raise RuntimeError(f'patch not applied in {name}: {pat}')
    src = re.sub(r"([\w\.]+)\.(inputs|outputs)\[('Factor'|'Fac')\]", lambda m: f'_sock({m.group(1)}.{m.group(2)}, {m.group(3)})', src)
    src = _COMPAT + src if name == 'scene_lib' else src
    mod = types.ModuleType(name); mod.__file__ = str(VENDOR / f'{name}.py')
    sys.modules[name] = mod
    exec(compile(src, mod.__file__, 'exec'), mod.__dict__)
    return mod


def generate(floors=6, seed=1, street=False, collection=None, **_):
    col = collection or bpy.context.scene.collection
    before = set(bpy.data.objects)
    sys.path.insert(0, str(VENDOR))
    try:
        L = _load('scene_lib', [(r'^SEED = \d+', f'SEED = {20261018 + seed}')])
        L._COLLECTIONS.clear(); L.load_fonts()
        B = _load('parts_building', [(r'^NFLOORS = \d+', f'NFLOORS = {int(floors)}'), (r'^rand = random\.Random\(\d+\)', f'rand = random.Random({7319 + seed})')])
        B.MATS = B.init_materials()
        G = _load('parts_ground', [(r'^rand = random\.Random\(\d+\)', f'rand = random.Random({8417 + seed})')])
        G.init_materials()
        B.build_shell(); B.build_facade(); B.build_balconies(); B.build_side_details(); B.build_roof()
        G.build_ground_shell()
        for s in G.SHOPS:
            G.build_shop(s)
        for st in G.STAIRS:
            G.build_entrance(st)
        G.build_wall_details(); G.build_front_details()
        if street:
            S = _load('parts_street'); S.init_materials(); S.build_street()
        L.recalc_closed_normals()
    finally:
        sys.path.remove(str(VENDOR))
    new = [o for o in bpy.data.objects if o not in before]
    for o in [o for o in new if o.type in ('LIGHT', 'CAMERA')]:
        bpy.data.objects.remove(o); new.remove(o)
    root = bpy.data.objects.new(f'现代居民楼_{floors}层_{seed}', None); col.objects.link(root)
    groups = {}
    for o in new:
        groups.setdefault(o.users_collection[0].name if o.users_collection else 'misc', []).append(o)
    joined = []
    for name, obs in groups.items():
        meshes = []
        for o in obs:
            if o.type in ('CURVE', 'FONT', 'SURFACE', 'META'):
                dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
                mo = bpy.data.objects.new(o.name + '_mesh', me); mo.matrix_world = o.matrix_world; col.objects.link(mo)
                bpy.data.objects.remove(o); meshes.append(mo)
            elif o.type == 'MESH':
                meshes.append(o)
        if not meshes:
            continue
        for o in meshes:
            if col not in o.users_collection:
                col.objects.link(o)
        with bpy.context.temp_override(active_object=meshes[0], selected_editable_objects=meshes, selected_objects=meshes):
            bpy.ops.object.join()
        j = meshes[0]; j.name = f'{root.name}_{name}'; j['lyz_component'] = name
        for c in list(j.users_collection):
            if c != col:
                c.objects.unlink(j)
        j.parent = root; joined.append(j)
    for c in list(bpy.data.collections):
        if c.name in groups and not c.objects:
            bpy.data.collections.remove(c)
    root['lyz_type'] = 'modern_residential'; root['lyz_style'] = 'modern'
    root['lyz_tris'] = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in joined)
    root['lyz_license'] = 'adapted from github.com/kang340/xingfuli-residential (MIT)'
    return root
