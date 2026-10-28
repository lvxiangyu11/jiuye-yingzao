# -*- coding: utf-8 -*-
"""Shared helpers for the Chinese residential building scene."""
import bpy
import bmesh
import math
import random
import os
from mathutils import Vector, Euler, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 20261018
random.seed(SEED)

# ----------------------------------------------------------------------------
# scene / collections
# ----------------------------------------------------------------------------
def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = (d.type == 'OPTIX')
    except Exception as exc:
        print("GPU setup warning:", exc)
    scene.cycles.samples = 160
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 3
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 8
    scene.cycles.transparent_max_bounces = 8
    scene.cycles.use_fast_gi = True
    scene.render.use_persistent_data = True
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0.35
    scene.view_settings.gamma = 1.0
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    return scene


_COLLECTIONS = {}

def C(name):
    if name in _COLLECTIONS:
        return _COLLECTIONS[name]
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    _COLLECTIONS[name] = col
    return col

def link(ob, coll_name):
    coll = C(coll_name)
    if ob.name not in coll.objects:
        coll.objects.link(ob)
    # unlink from scene root if the operator linked it there
    for c in list(ob.users_collection):
        if c != coll and c.name == "Scene Collection":
            c.objects.unlink(ob)
    return ob

# ----------------------------------------------------------------------------
# colour and materials
# ----------------------------------------------------------------------------
def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def H(hexstr, alpha=1.0):
    """sRGB hex -> linear RGBA."""
    h = hexstr.lstrip('#')
    if len(h) == 3:
        h = ''.join(ch * 2 for ch in h)
    return (_lin(int(h[0:2], 16)), _lin(int(h[2:4], 16)), _lin(int(h[4:6], 16)), alpha)

def mixc(a, b, t):
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(4))

_MATS = {}

def _principled(mat):
    return mat.node_tree.nodes.get('Principled BSDF')

def mat_basic(name, color, rough=0.55, metal=0.0, spec=0.5,
              emission=None, emission_strength=0.0, coat=0.0, sheen=0.0):
    if name in _MATS:
        return _MATS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = _principled(mat)
    if isinstance(color, str):
        color = H(color)
    elif len(color) == 3:
        color = (*color, 1.0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = spec
    if coat:
        bsdf.inputs['Coat Weight'].default_value = coat
        bsdf.inputs['Coat Roughness'].default_value = 0.15
    if sheen:
        bsdf.inputs['Sheen Weight'].default_value = sheen
    if emission is not None:
        if isinstance(emission, str):
            emission = H(emission)
        if len(emission) == 3:
            emission = (*emission, 1.0)
        bsdf.inputs['Emission Color'].default_value = emission
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    mat.diffuse_color = color
    _MATS[name] = mat
    return mat

def mat_glass(name, tint=(0.28, 0.41, 0.40, 1.0), rough=0.035, transmission=0.92):
    if name in _MATS:
        return _MATS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = _principled(mat)
    bsdf.inputs['Base Color'].default_value = tint
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Transmission Weight'].default_value = transmission
    bsdf.inputs['IOR'].default_value = 1.46
    bsdf.inputs['Specular IOR Level'].default_value = 0.55
    mat.diffuse_color = (*tint[:3], 0.35)
    _MATS[name] = mat
    return mat

def mat_emit(name, color, strength=1.0):
    if isinstance(color, str):
        color = H(color)
    return mat_basic(name, color, rough=0.4, emission=color, emission_strength=strength)

def _n(nt, ntype, loc=(0, 0)):
    node = nt.nodes.new(ntype)
    node.location = loc
    return node

def _connect(nt, a, b):
    nt.links.new(a, b)

def _add_obj_coords(nt, scale=(1, 1, 1), loc=-700):
    tc = _n(nt, 'ShaderNodeTexCoord', (loc, 0))
    mp = _n(nt, 'ShaderNodeMapping', (loc + 180, 0))
    mp.inputs['Scale'].default_value = scale
    _connect(nt, tc.outputs['Object'], mp.inputs['Vector'])
    return tc, mp

def mat_wall_tile(name, base='#cdbfa6', base2='#c3b397', mortar='#8f887a',
                  rough=0.56, dirt=0.30, scale=1.0):
    if name in _MATS:
        return _MATS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = _principled(mat)
    geo = nodes.new('ShaderNodeNewGeometry'); geo.location = (-1000, 120)
    sep = nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-820, 100)
    comb = nodes.new('ShaderNodeCombineXYZ'); comb.location = (-640, 100)
    links.new(geo.outputs['Position'], sep.inputs[0])
    links.new(sep.outputs['X'], comb.inputs['X'])
    links.new(sep.outputs['Z'], comb.inputs['Z'])
    # tiny distortion to keep the tile grid from looking mathematical
    dist = nodes.new('ShaderNodeTexNoise'); dist.location = (-820, -120)
    dist.inputs['Scale'].default_value = 3.2
    dist.inputs['Detail'].default_value = 3.0
    links.new(geo.outputs['Position'], dist.inputs['Vector'])
    vm = nodes.new('ShaderNodeVectorMath'); vm.operation = 'MULTIPLY_ADD'; vm.location = (-480, 40)
    vm.inputs[1].default_value = (0.006, 0.006, 0.006)
    vm.inputs[2].default_value = (0, 0, 0)
    links.new(dist.outputs['Color'], vm.inputs[0])
    links.new(comb.outputs['Vector'], vm.inputs[2])
    brick = nodes.new('ShaderNodeTexBrick'); brick.location = (-300, 160)
    brick.offset = 0.5
    brick.offset_frequency = 1
    brick.squash = 1.0
    brick.inputs['Color1'].default_value = H(base)
    brick.inputs['Color2'].default_value = H(base2)
    brick.inputs['Mortar'].default_value = H(mortar)
    brick.inputs['Scale'].default_value = 7.2 * scale
    brick.inputs['Mortar Size'].default_value = 0.012
    brick.inputs['Mortar Smooth'].default_value = 0.15
    brick.inputs['Brick Width'].default_value = 0.66
    brick.inputs['Row Height'].default_value = 0.31
    links.new(vm.outputs['Vector'], brick.inputs['Vector'])
    # large scale dirt / damp patches
    dirt_n = nodes.new('ShaderNodeTexNoise'); dirt_n.location = (-320, -220)
    dirt_n.inputs['Scale'].default_value = 0.55
    dirt_n.inputs['Detail'].default_value = 8.0
    dirt_n.inputs['Roughness'].default_value = 0.65
    links.new(geo.outputs['Position'], dirt_n.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB'); ramp.location = (-110, -220)
    ramp.color_ramp.elements[0].position = 0.28
    ramp.color_ramp.elements[0].color = (0.34, 0.32, 0.27, 1)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    links.new(dirt_n.outputs['Fac'], ramp.inputs['Factor'])
    mix = nodes.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'; mix.location = (80, 100)
    mix.inputs['Fac'].default_value = dirt
    links.new(brick.outputs['Color'], mix.inputs[1])
    links.new(ramp.outputs['Color'], mix.inputs[2])
    # subtle horizontal grime streaks
    streak = nodes.new('ShaderNodeTexNoise'); streak.location = (-320, -500)
    streak.inputs['Scale'].default_value = 3.0
    streak.inputs['Detail'].default_value = 3.0
    streak.inputs['Distortion'].default_value = 1.2
    streak_map = nodes.new('ShaderNodeMapping'); streak_map.location = (-500, -500)
    streak_map.inputs['Scale'].default_value = (4.0, 4.0, 0.16)
    links.new(geo.outputs['Position'], streak_map.inputs['Vector'])
    links.new(streak_map.outputs['Vector'], streak.inputs['Vector'])
    sramp = nodes.new('ShaderNodeValToRGB'); sramp.location = (-110, -500)
    sramp.color_ramp.elements[0].position = 0.5
    sramp.color_ramp.elements[0].color = (0.55, 0.54, 0.49, 1)
    sramp.color_ramp.elements[1].position = 0.78
    sramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    links.new(streak.outputs['Fac'], sramp.inputs['Factor'])
    mix2 = nodes.new('ShaderNodeMixRGB'); mix2.blend_type = 'MULTIPLY'; mix2.location = (300, 60)
    mix2.inputs['Fac'].default_value = 0.20
    links.new(mix.outputs['Color'], mix2.inputs[1])
    links.new(sramp.outputs['Color'], mix2.inputs[2])
    links.new(mix2.outputs['Color'], bsdf.inputs['Base Color'])
    # bump: tile relief plus grime
    bump1 = nodes.new('ShaderNodeBump'); bump1.location = (100, -260)
    bump1.inputs['Strength'].default_value = 0.28
    bump1.inputs['Distance'].default_value = 0.012
    links.new(brick.outputs['Factor'], bump1.inputs['Height'])
    bump2 = nodes.new('ShaderNodeBump'); bump2.location = (300, -260)
    bump2.inputs['Strength'].default_value = 0.16
    bump2.inputs['Distance'].default_value = 0.01
    links.new(dirt_n.outputs['Fac'], bump2.inputs['Height'])
    links.new(bump1.outputs['Normal'], bump2.inputs['Normal'])
    links.new(bump2.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Specular IOR Level'].default_value = 0.42
    mat.diffuse_color = H(base)
    _MATS[name] = mat
    return mat

def mat_concrete(name='混凝土', base='#a8a196', dark='#6f6a60', rough=0.78, scale=1.0):
    if name in _MATS:
        return _MATS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = _principled(mat)
    tc = nodes.new('ShaderNodeTexCoord'); tc.location = (-800, 0)
    noise = nodes.new('ShaderNodeTexNoise'); noise.location = (-560, 100)
    noise.inputs['Scale'].default_value = 7.0 * scale
    noise.inputs['Detail'].default_value = 10.0
    noise.inputs['Roughness'].default_value = 0.7
    links.new(tc.outputs['Object'], noise.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB'); ramp.location = (-320, 100)
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[0].color = H(dark)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = H(base)
    links.new(noise.outputs['Fac'], ramp.inputs['Factor'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    fine = nodes.new('ShaderNodeTexNoise'); fine.location = (-560, -220)
    fine.inputs['Scale'].default_value = 130.0
    fine.inputs['Detail'].default_value = 5.0
    links.new(tc.outputs['Object'], fine.inputs['Vector'])
    bump = nodes.new('ShaderNodeBump'); bump.location = (-50, -120)
    bump.inputs['Strength'].default_value = 0.22
    bump.inputs['Distance'].default_value = 0.006
    links.new(fine.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = rough
    mat.diffuse_color = H(base)
    _MATS[name] = mat
    return mat

def mat_asphalt():
    name = '沥青路面'
    if name in _MATS:
        return _MATS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = _principled(mat)
    tc = nodes.new('ShaderNodeTexCoord'); tc.location = (-850, 0)
    noise = nodes.new('ShaderNodeTexNoise'); noise.location = (-620, 100)
    noise.inputs['Scale'].default_value = 1.4
    noise.inputs['Detail'].default_value = 12.0
    noise.inputs['Roughness'].default_value = 0.72
    links.new(tc.outputs['Object'], noise.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB'); ramp.location = (-380, 100)
    ramp.color_ramp.elements[0].position = 0.26
    ramp.color_ramp.elements[0].color = H('#2c2b28')
    ramp.color_ramp.elements[1].position = 0.8
    ramp.color_ramp.elements[1].color = H('#55524b')
    links.new(noise.outputs['Fac'], ramp.inputs['Factor'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    fine = nodes.new('ShaderNodeTexNoise'); fine.location = (-620, -230)
    fine.inputs['Scale'].default_value = 180.0
    fine.inputs['Detail'].default_value = 4.0
    links.new(tc.outputs['Object'], fine.inputs['Vector'])
    bump = nodes.new('ShaderNodeBump'); bump.location = (-100, -120)
    bump.inputs['Strength'].default_value = 0.42
    bump.inputs['Distance'].default_value = 0.015
    links.new(fine.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = 0.88
    mat.diffuse_color = H('#3b3935')
    _MATS[name] = mat
    return mat

def mat_pavement():
    name = '人行道砖'
    if name in _MATS:
        return _MATS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = _principled(mat)
    tc = nodes.new('ShaderNodeTexCoord'); tc.location = (-820, 0)
    sep = nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-640, 80)
    comb = nodes.new('ShaderNodeCombineXYZ'); comb.location = (-460, 80)
    links.new(tc.outputs['Object'], sep.inputs[0])
    links.new(sep.outputs['X'], comb.inputs['X'])
    links.new(sep.outputs['Y'], comb.inputs['Y'])
    brick = nodes.new('ShaderNodeTexBrick'); brick.location = (-260, 80)
    brick.inputs['Color1'].default_value = H('#a39a8a')
    brick.inputs['Color2'].default_value = H('#8f8778')
    brick.inputs['Mortar'].default_value = H('#5e5a52')
    brick.inputs['Scale'].default_value = 1.0
    brick.inputs['Mortar Size'].default_value = 0.012
    brick.inputs['Brick Width'].default_value = 0.48
    brick.inputs['Row Height'].default_value = 0.48
    links.new(comb.outputs['Vector'], brick.inputs['Vector'])
    noise = nodes.new('ShaderNodeTexNoise'); noise.location = (-280, -260)
    noise.inputs['Scale'].default_value = 7.0
    noise.inputs['Detail'].default_value = 8.0
    links.new(tc.outputs['Object'], noise.inputs['Vector'])
    mix = nodes.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'; mix.location = (20, 40)
    mix.inputs['Fac'].default_value = 0.32
    links.new(brick.outputs['Color'], mix.inputs[1])
    darks = nodes.new('ShaderNodeValToRGB'); darks.location = (-30, -220)
    darks.color_ramp.elements[0].color = (0.55, 0.54, 0.50, 1)
    darks.color_ramp.elements[1].color = (1, 1, 1, 1)
    links.new(noise.outputs['Fac'], darks.inputs['Factor'])
    links.new(darks.outputs['Color'], mix.inputs[2])
    links.new(mix.outputs['Color'], bsdf.inputs['Base Color'])
    bump = nodes.new('ShaderNodeBump'); bump.location = (240, -100)
    bump.inputs['Strength'].default_value = 0.18
    bump.inputs['Distance'].default_value = 0.006
    links.new(brick.outputs['Factor'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = 0.82
    mat.diffuse_color = H('#9b9284')
    _MATS[name] = mat
    return mat

def mat_striped(name, color_a, color_b, scale=4.0, axis='X'):
    name = name
    if name in _MATS:
        return _MATS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = _principled(mat)
    tc = nodes.new('ShaderNodeTexCoord'); tc.location = (-720, 0)
    wave = nodes.new('ShaderNodeTexWave'); wave.location = (-500, 0)
    wave.wave_type = 'BANDS'
    wave.bands_direction = axis
    wave.wave_profile = 'SIN'
    wave.inputs['Scale'].default_value = scale
    wave.inputs['Distortion'].default_value = 0.4
    links.new(tc.outputs['Generated'], wave.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB'); ramp.location = (-260, 0)
    ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements[0].position = 0.34
    ramp.color_ramp.elements[0].color = H(color_a)
    ramp.color_ramp.elements[1].position = 0.66
    ramp.color_ramp.elements[1].color = H(color_b)
    links.new(wave.outputs['Fac'], ramp.inputs['Factor'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.62
    mat.diffuse_color = H(color_a)
    _MATS[name] = mat
    return mat

def mat_bark(name='梧桐树皮'):
    if name in _MATS:
        return _MATS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = _principled(mat)
    tc = nodes.new('ShaderNodeTexCoord'); tc.location = (-750, 0)
    noise = nodes.new('ShaderNodeTexNoise'); noise.location = (-520, 80)
    noise.inputs['Scale'].default_value = 3.8
    noise.inputs['Detail'].default_value = 9.0
    noise.inputs['Roughness'].default_value = 0.72
    links.new(tc.outputs['Object'], noise.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB'); ramp.location = (-280, 80)
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = H('#4b463c')
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = H('#9a927e')
    links.new(noise.outputs['Fac'], ramp.inputs['Factor'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    bump = nodes.new('ShaderNodeBump'); bump.location = (-40, -100)
    bump.inputs['Strength'].default_value = 0.55
    bump.inputs['Distance'].default_value = 0.04
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = 0.86
    mat.diffuse_color = H('#6e6656')
    _MATS[name] = mat
    return mat

def mat_leaf(name, color_a, color_b):
    if name in _MATS:
        return _MATS[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    out = nodes.get('Material Output')
    bsdf = _principled(mat)
    tc = nodes.new('ShaderNodeTexCoord'); tc.location = (-720, 0)
    noise = nodes.new('ShaderNodeTexNoise'); noise.location = (-500, 0)
    noise.inputs['Scale'].default_value = 6.0
    noise.inputs['Detail'].default_value = 3.0
    links.new(tc.outputs['Object'], noise.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB'); ramp.location = (-260, 0)
    ramp.color_ramp.elements[0].position = 0.28
    ramp.color_ramp.elements[0].color = H(color_a)
    ramp.color_ramp.elements[1].position = 0.76
    ramp.color_ramp.elements[1].color = H(color_b)
    links.new(noise.outputs['Fac'], ramp.inputs['Factor'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.52
    bsdf.inputs['Specular IOR Level'].default_value = 0.32
    # a whisper of emission keeps dense foliage from going muddy in shadow
    bsdf.inputs['Emission Color'].default_value = H(color_b)
    bsdf.inputs['Emission Strength'].default_value = 0.18
    # a touch of translucency for backlit foliage
    trans = nodes.new('ShaderNodeBsdfTranslucent'); trans.location = (300, -80)
    trans.inputs['Color'].default_value = H(color_a)
    mix = nodes.new('ShaderNodeMixShader'); mix.location = (520, 0)
    mix.inputs['Fac'].default_value = 0.34
    links.new(bsdf.outputs['BSDF'], mix.inputs[1])
    links.new(trans.outputs['BSDF'], mix.inputs[2])
    links.new(mix.outputs['Shader'], out.inputs['Surface'])
    mat.diffuse_color = H(color_a)
    _MATS[name] = mat
    return mat

# ----------------------------------------------------------------------------
# geometry
# ----------------------------------------------------------------------------
def _finish_mesh(name, mesh, coll):
    ob = bpy.data.objects.new(name, mesh)
    C(coll).objects.link(ob)
    return ob

def add_box(name, center, size, mat, coll='细节', rot=(0, 0, 0), bevel=0.0):
    cx, cy, cz = center
    sx, sy, sz = size
    verts = [
        (-sx/2, -sy/2, -sz/2), ( sx/2, -sy/2, -sz/2),
        ( sx/2,  sy/2, -sz/2), (-sx/2,  sy/2, -sz/2),
        (-sx/2, -sy/2,  sz/2), ( sx/2, -sy/2,  sz/2),
        ( sx/2,  sy/2,  sz/2), (-sx/2,  sy/2,  sz/2),
    ]
    faces = [(0,3,2,1), (4,5,6,7), (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    for f in mesh.polygons:
        f.material_index = 0
    if mat is not None:
        mesh.materials.append(mat)
    ob = _finish_mesh(name, mesh, coll)
    ob.location = (cx, cy, cz)
    ob.rotation_euler = rot
    if bevel > 0:
        mod = ob.modifiers.new('倒角', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = 'ANGLE'
        mod.use_clamp_overlap = True
    return ob

def add_boxes(name, boxes, mat, coll='细节'):
    """boxes: list of (center, size) tuples, all in one mesh."""
    verts, faces = [], []
    for (cx, cy, cz), (sx, sy, sz) in boxes:
        i = len(verts)
        verts.extend([
            (cx-sx/2, cy-sy/2, cz-sz/2), (cx+sx/2, cy-sy/2, cz-sz/2),
            (cx+sx/2, cy+sy/2, cz-sz/2), (cx-sx/2, cy+sy/2, cz-sz/2),
            (cx-sx/2, cy-sy/2, cz+sz/2), (cx+sx/2, cy-sy/2, cz+sz/2),
            (cx+sx/2, cy+sy/2, cz+sz/2), (cx-sx/2, cy+sy/2, cz+sz/2),
        ])
        faces.extend([
            (i+0,i+3,i+2,i+1), (i+4,i+5,i+6,i+7),
            (i+0,i+1,i+5,i+4), (i+1,i+2,i+6,i+5),
            (i+2,i+3,i+7,i+6), (i+3,i+0,i+4,i+7),
        ])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    if mat is not None:
        mesh.materials.append(mat)
    return _finish_mesh(name, mesh, coll)

def add_mesh(name, verts, faces, mat, coll='细节', location=(0,0,0), smooth=False):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()
    if isinstance(mat, (list, tuple)):
        for m in mat:
            mesh.materials.append(m)
    elif mat is not None:
        mesh.materials.append(mat)
    if smooth:
        for p in mesh.polygons:
            p.use_smooth = True
    ob = _finish_mesh(name, mesh, coll)
    ob.location = location
    return ob

def add_cyl(name, center, radius, depth, mat, coll='细节', vertices=16,
            rot=(0,0,0), smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=vertices,
                          radius1=radius, radius2=radius, depth=depth)
    if smooth:
        for f in bm.faces:
            f.smooth = len(f.verts) == 4
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    ob = _finish_mesh(name, mesh, coll)
    ob.location = center
    ob.rotation_euler = rot
    return ob

def add_cone(name, center, r1, r2, depth, mat, coll='细节', vertices=16, rot=(0,0,0)):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=vertices,
                          radius1=r1, radius2=r2, depth=depth)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    ob = _finish_mesh(name, mesh, coll)
    ob.location = center
    ob.rotation_euler = rot
    return ob

def add_uvsphere(name, center, radius, mat, coll='细节', segments=20, rings=12):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    for f in bm.faces:
        f.smooth = True
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    ob = _finish_mesh(name, mesh, coll)
    ob.location = center
    return ob

def add_ico(name, center, radius, mat, coll='细节', subdiv=2, scale=(1,1,1)):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=radius)
    for f in bm.faces:
        f.smooth = True
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    ob = _finish_mesh(name, mesh, coll)
    ob.location = center
    ob.scale = scale
    return ob

def add_torus(name, center, major_r, minor_r, mat, coll='细节',
              major_seg=24, minor_seg=8, axis='Y'):
    verts, faces = [], []
    for i in range(major_seg):
        u = math.tau * i / major_seg
        for j in range(minor_seg):
            v = math.tau * j / minor_seg
            rr = major_r + minor_r * math.cos(v)
            if axis == 'Y':
                verts.append((rr * math.cos(u), minor_r * math.sin(v), rr * math.sin(u)))
            elif axis == 'Z':
                verts.append((rr * math.cos(u), rr * math.sin(u), minor_r * math.sin(v)))
            else:
                verts.append((minor_r * math.sin(v), rr * math.cos(u), rr * math.sin(u)))
    for i in range(major_seg):
        for j in range(minor_seg):
            a = i * minor_seg + j
            b = i * minor_seg + (j + 1) % minor_seg
            c = ((i + 1) % major_seg) * minor_seg + (j + 1) % minor_seg
            d = ((i + 1) % major_seg) * minor_seg + j
            faces.append((a, b, c, d))
    ob = add_mesh(name, verts, faces, mat, coll, smooth=True)
    ob.location = center
    return ob

def add_curve(name, points, radius, mat, coll='细节', resolution=3, cyclic=False):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = resolution
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    curve.fill_mode = 'FULL'
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for p, pt in zip(spline.points, points):
        p.co = (pt[0], pt[1], pt[2], 1.0)
    spline.use_cyclic_u = cyclic
    curve.materials.append(mat)
    ob = bpy.data.objects.new(name, curve)
    C(coll).objects.link(ob)
    return ob

def tube_between(name, p1, p2, radius, mat, coll='细节', vertices=12):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    ob = add_cyl(name, (p1 + p2) / 2, radius, d.length, mat, coll,
                 vertices=vertices)
    ob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    return ob

def add_text(name, body, loc, size, mat, coll='招牌', rot=(math.pi/2, 0, 0),
             extrude=0.0, align_x='CENTER', align_y='CENTER', font=None, spacing=1.0):
    curve = bpy.data.curves.new(name, 'FONT')
    curve.body = body
    curve.size = size
    curve.extrude = extrude
    curve.align_x = align_x
    curve.align_y = align_y
    curve.space_character = spacing
    curve.space_line = 0.95
    if font is not None:
        curve.font = font
    curve.materials.append(mat)
    ob = bpy.data.objects.new(name, curve)
    C(coll).objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    return ob

def add_plane(name, center, width, height, mat, coll='细节', rot=(0,0,0)):
    verts = [(-width/2, -height/2, 0), (width/2, -height/2, 0),
             (width/2, height/2, 0), (-width/2, height/2, 0)]
    ob = add_mesh(name, verts, [(0,1,2,3)], mat, coll, smooth=False)
    ob.location = center
    ob.rotation_euler = rot
    return ob

# ----------------------------------------------------------------------------
# fonts
# ----------------------------------------------------------------------------
FONT_SANS = None
FONT_BOLD = None
FONT_SERIF = None

def load_fonts():
    global FONT_SANS, FONT_BOLD, FONT_SERIF
    candidates_sans = [
        r'C:\Windows\Fonts\NotoSansSC-VF.ttf',
        r'C:\Windows\Fonts\msyh.ttc',
        r'C:\Windows\Fonts\simhei.ttf',
    ]
    candidates_bold = [
        r'C:\Windows\Fonts\msyhbd.ttc',
        r'C:\Windows\Fonts\simhei.ttf',
        r'C:\Windows\Fonts\Dengb.ttf',
    ]
    candidates_serif = [
        r'C:\Windows\Fonts\NotoSerifSC-VF.ttf',
        r'C:\Windows\Fonts\simsun.ttc',
    ]
    for path in candidates_sans:
        if os.path.exists(path):
            try:
                FONT_SANS = bpy.data.fonts.load(path, check_existing=True)
                break
            except Exception as e:
                print('font failed', path, e)
    for path in candidates_bold:
        if os.path.exists(path):
            try:
                FONT_BOLD = bpy.data.fonts.load(path, check_existing=True)
                break
            except Exception as e:
                print('font failed', path, e)
    for path in candidates_serif:
        if os.path.exists(path):
            try:
                FONT_SERIF = bpy.data.fonts.load(path, check_existing=True)
                break
            except Exception as e:
                print('font failed', path, e)
    if FONT_SANS is None:
        FONT_SANS = bpy.data.fonts.load('<builtin>') if False else None
    if FONT_BOLD is None:
        FONT_BOLD = FONT_SANS
    if FONT_SERIF is None:
        FONT_SERIF = FONT_SANS
    print('FONTS', FONT_SANS, FONT_BOLD, FONT_SERIF)
    return FONT_SANS, FONT_BOLD, FONT_SERIF

# ----------------------------------------------------------------------------
# misc
# ----------------------------------------------------------------------------
def look_at(ob, target):
    direction = Vector(target) - ob.location
    ob.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

def catenary(p1, p2, sag=0.5, n=18):
    p1, p2 = Vector(p1), Vector(p2)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        p = p1.lerp(p2, t)
        p.z -= sag * math.sin(math.pi * t)
        pts.append(tuple(p))
    return pts

def set_smooth(ob):
    if ob.type == 'MESH':
        for p in ob.data.polygons:
            p.use_smooth = True

def recalc_closed_normals():
    """Fix winding on watertight meshes; leave open cloth/leaf cards alone."""
    fixed = 0
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob.data.users > 1:
            continue
        me = ob.data
        if len(me.polygons) == 0:
            continue
        bm = bmesh.new()
        bm.from_mesh(me)
        closed = len(bm.edges) > 0 and all(e.is_manifold for e in bm.edges)
        if closed:
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
            bm.to_mesh(me)
            me.update()
            fixed += 1
        bm.free()
    print('NORMALS recalculated on', fixed, 'closed meshes')
