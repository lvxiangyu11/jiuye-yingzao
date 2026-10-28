# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Export a generated root (and its children) for Unity: GLB (default) or FBX, Y-up, metres."""
from pathlib import Path

import bpy


def _select_tree(root):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    stack = [root]
    while stack:
        o = stack.pop(); o.select_set(True); stack.extend(o.children)
    bpy.context.view_layer.objects.active = root


def export_root(root, path, fmt='GLB'):
    """fmt: GLB (self-contained, textures embedded, ~10–20 MB per building) | GLTF_SEPARATE (.gltf + .bin, textures in a
    shared ../textures folder so a batch of buildings stores each texture once) | FBX."""
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    loc = root.location.copy(); rot = root.rotation_euler.copy()
    root.location = (0, 0, 0); root.rotation_euler = (0, 0, 0)
    _select_tree(root)
    try:
        if fmt == 'FBX':
            bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, apply_scale_options='FBX_SCALE_UNITS', axis_forward='-Z', axis_up='Y',
                                     object_types={'EMPTY', 'MESH'}, path_mode='COPY', embed_textures=True)
        elif fmt == 'GLTF_SEPARATE':
            bpy.ops.export_scene.gltf(filepath=str(path.with_suffix('.gltf')), use_selection=True, export_format='GLTF_SEPARATE', export_yup=True,
                                      export_apply=True, export_extras=True, export_image_format='AUTO', export_texture_dir='../textures')
            path = path.with_suffix('.gltf')
        else:
            bpy.ops.export_scene.gltf(filepath=str(path), use_selection=True, export_format='GLB', export_yup=True, export_apply=True,
                                      export_extras=True, export_image_format='AUTO')
    finally:
        root.location = loc; root.rotation_euler = rot
    return path
