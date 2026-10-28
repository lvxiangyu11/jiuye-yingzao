# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Headless render helpers for catalog/test scripts (Blender)."""
import math
import bpy
from mathutils import Vector


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            sc.render.engine = eng; break
        except TypeError:
            continue
    sc.render.resolution_x = 1600; sc.render.resolution_y = 1000
    sc.view_settings.view_transform = 'AgX'
    world = bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
    bg = world.node_tree.nodes['Background']; bg.inputs[0].default_value = (.62, .66, .70, 1); bg.inputs[1].default_value = .9
    sun = bpy.data.lights.new('Sun', 'SUN'); sun.energy = 3.2; sun.angle = .08
    ob = bpy.data.objects.new('Sun', sun); sc.collection.objects.link(ob); ob.rotation_euler = (math.radians(52), 0, math.radians(-38))
    try:
        sc.eevee.use_shadows = True
    except AttributeError:
        pass
    return sc


def ground(size=400, z=0.0):
    me = bpy.data.meshes.new('Ground'); s = size / 2
    me.from_pydata([(-s, -s, z), (s, -s, z), (s, s, z), (-s, s, z)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new('Ground', me); bpy.context.scene.collection.objects.link(ob)
    m = bpy.data.materials.new('GroundMat'); m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.36, .34, .30, 1)
    me.materials.append(m)
    return ob


def frame_camera(objs, path, azimuth=-35, elevation=32, lens=50, margin=1.15):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == 'MESH' for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (lo + hi) / 2; r = (hi - lo).length / 2 * margin
    cam = bpy.data.cameras.new('Cam'); cam.lens = lens; ob = bpy.data.objects.new('Cam', cam); bpy.context.scene.collection.objects.link(ob)
    d = r / math.tan(cam.angle / 2) * 1.0
    az = math.radians(azimuth); el = math.radians(elevation)
    ob.location = c + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * d
    ob.rotation_euler = (c - ob.location).to_track_quat('-Z', 'Y').to_euler()
    cam.clip_end = d * 4
    bpy.context.scene.camera = ob
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(ob)
