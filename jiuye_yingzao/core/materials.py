# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Shared materials, one Blender material per key in data/materials.json (prefix LYZ_).

Albedo and roughness come from textures/derived (tint baked by tools/bake_textures.py) so
glTF/FBX exports carry the final look; normal maps are the CC0 base sets (OpenGL, Non-Color).
"""
import hashlib
import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'LYZ_'


def specs():
    return {k: v for k, v in json.loads((ROOT / 'data/materials.json').read_text(encoding='utf-8')).items() if not k.startswith('_')}


def _image(path, non_color):
    img = bpy.data.images.load(str(path), check_existing=True)
    img.colorspace_settings.name = 'Non-Color' if non_color else 'sRGB'
    return img


def library(force=False):
    out = {}
    for key, s in specs().items():
        name = PREFIX + key; m = bpy.data.materials.get(name)
        rev = hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()[:12]
        if m is None or force or m.get('lyz_rev') != rev:
            m = m or bpy.data.materials.new(name)
            m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
            p = nt.nodes.new('ShaderNodeBsdfPrincipled'); o = nt.nodes.new('ShaderNodeOutputMaterial')
            nt.links.new(p.outputs[0], o.inputs[0]); o.location = (400, 0)
            p.inputs['Base Color'].default_value = (*[c ** 2.2 for c in s['color']], 1)
            p.inputs['Roughness'].default_value = sum(s['roughness']) / 2
            p.inputs['Metallic'].default_value = s.get('metallic', 0.0)
            m.diffuse_color = (*s['color'], 1)
            if s.get('base'):
                coord = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
                sc = 1 / s.get('scale', 1.0); mp.inputs['Scale'].default_value = (sc, sc, 1)
                nt.links.new(coord.outputs['UV'], mp.inputs['Vector'])

                def tex(path, non_color, y):
                    n = nt.nodes.new('ShaderNodeTexImage'); n.image = _image(path, non_color); n.location = (-500, y)
                    nt.links.new(mp.outputs['Vector'], n.inputs['Vector']); return n
                d = ROOT / 'textures/derived'; b = ROOT / 'textures/pbr'
                col = tex(d / f'{key}_Color.jpg', False, 300); nt.links.new(col.outputs['Color'], p.inputs['Base Color'])
                rough = tex(d / f'{key}_Roughness.jpg', True, 0); nt.links.new(rough.outputs['Color'], p.inputs['Roughness'])
                nrm = tex(b / f"{s['base']}_NormalGL.jpg", True, -300); nm = nt.nodes.new('ShaderNodeNormalMap')
                nm.inputs['Strength'].default_value = s.get('normal', .6)
                nt.links.new(nrm.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], p.inputs['Normal'])
            if key == 'glass':
                p.inputs['Alpha'].default_value = .55
                try:
                    m.surface_render_method = 'BLENDED'
                except AttributeError:
                    pass
            m['lyz_rev'] = rev; m['lyz_label'] = s.get('label', key)
            m['lyz_license'] = 'CC0-1.0 (ambientCG)' if s.get('base') else 'project-authored'
        out[key] = m
    return out
