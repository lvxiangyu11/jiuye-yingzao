# -*- coding: utf-8 -*-
"""Street, trees, vehicles, neighbourhood buildings and human-scale detail."""
import bpy
import math
import random
from mathutils import Vector, Matrix
from scene_lib import *
import parts_building as B
import parts_ground as G

M = {}
rand = random.Random(6912)

# ---------------------------------------------------------------------------
# materials
# ---------------------------------------------------------------------------
def init_materials():
    global M
    M = B.MATS
    M['road'] = mat_asphalt()
    M['pavement'] = mat_pavement()
    M['bark'] = mat_bark()
    M['paver1'] = mat_basic('人行道砖1', '#a49b8c', rough=0.84)
    M['paver2'] = mat_basic('人行道砖2', '#91897b', rough=0.86)
    M['paver3'] = mat_basic('人行道砖3', '#b0a493', rough=0.82)
    M['grout'] = mat_basic('砖缝', '#4f4b43', rough=0.95)
    M['curb'] = mat_concrete('路缘石', '#b3aa99', '#7e786d', rough=0.8)
    M['curb_yellow'] = mat_basic('路缘黄漆', '#b9963f', rough=0.7)
    M['line_white'] = mat_basic('道路白线', '#c5c1b2', rough=0.88)
    M['line_yellow'] = mat_basic('道路黄线', '#b3963d', rough=0.9)
    M['tire'] = mat_basic('橡胶轮胎', '#20211f', rough=0.82)
    M['rim'] = mat_basic('轮毂银', '#aeb1ad', rough=0.3, metal=0.85)
    M['car_white'] = mat_basic('白色车漆', '#d7d5cd', rough=0.28, metal=0.15, coat=0.45)
    M['car_silver'] = mat_basic('银色车漆', '#a8aaa5', rough=0.3, metal=0.55, coat=0.3)
    M['car_blue'] = mat_basic('蓝色车漆', '#3f596b', rough=0.32, metal=0.25, coat=0.3)
    M['car_red'] = mat_basic('红色车漆', '#8e342c', rough=0.3, metal=0.2, coat=0.35)
    M['car_glass'] = mat_glass('汽车玻璃', (0.03, 0.05, 0.055, 1.0), 0.06, 0.72)
    M['license_blue'] = mat_basic('蓝色车牌', '#1c3f6b', rough=0.4)
    M['license_white'] = mat_basic('车牌白字', '#d9d7c7', rough=0.5,
                                    emission=H('#d9d7c7'), emission_strength=0.1)
    M['headlight'] = mat_basic('车灯', '#dce3d6', rough=0.1,
                               emission=H('#fff0ce'), emission_strength=0.5)
    M['taillight'] = mat_basic('尾灯', '#7e1f1c', rough=0.2,
                               emission=H('#b32620'), emission_strength=0.3)
    M['chrome_car'] = mat_basic('汽车镀铬', '#c6c9c5', rough=0.12, metal=1.0)
    M['bike_yellow'] = mat_basic('共享单车黄', '#c6a62d', rough=0.45, metal=0.2)
    M['bike_blue'] = mat_basic('共享单车蓝', '#345b74', rough=0.45, metal=0.2)
    M['bike_black'] = mat_basic('旧自行车黑', '#353834', rough=0.6, metal=0.25)
    M['bike_red'] = mat_basic('自行车红', '#8a3c31', rough=0.55, metal=0.15)
    M['bike_basket'] = mat_basic('车筐', '#5b5e57', rough=0.6, metal=0.3)
    M['bike_seat'] = mat_basic('车座', '#2a2926', rough=0.7)
    M['scooter_white'] = mat_basic('电动车白', '#c9c6ba', rough=0.4, metal=0.1)
    M['scooter_blue'] = mat_basic('电动车蓝', '#466c7e', rough=0.45, metal=0.1)
    M['skin'] = mat_basic('皮肤', '#bd8f6f', rough=0.65)
    M['skin_old'] = mat_basic('老人皮肤', '#a97b5c', rough=0.7)
    M['hair_black'] = mat_basic('黑发', '#24211d', rough=0.75)
    M['hair_gray'] = mat_basic('花白头发', '#8a857a', rough=0.8)
    M['shirt_white'] = mat_basic('白衬衫', '#c7c1b2', rough=0.9, sheen=0.2)
    M['shirt_blue'] = mat_basic('蓝衬衫', '#4c6f8c', rough=0.9, sheen=0.2)
    M['shirt_red'] = mat_basic('红上衣', '#8f3c35', rough=0.9, sheen=0.2)
    M['shirt_green'] = mat_basic('绿外套', '#556b53', rough=0.9, sheen=0.2)
    M['pants_dark'] = mat_basic('深色裤子', '#343635', rough=0.92)
    M['pants_blue'] = mat_basic('蓝裤子', '#3f5263', rough=0.92)
    M['pants_gray'] = mat_basic('灰裤子', '#66655f', rough=0.92)
    M['shoe_black'] = mat_basic('黑鞋', '#222322', rough=0.75)
    M['bag_red'] = mat_basic('购物袋', '#8d3d35', rough=0.78)
    M['bag_white'] = mat_basic('塑料袋', '#c9c4b4', rough=0.82)
    M['bench_wood'] = mat_basic('长椅木', '#795a3c', rough=0.8)
    M['bench_metal'] = mat_basic('长椅铁', '#343a37', rough=0.7, metal=0.3)
    M['bin_green'] = mat_basic('垃圾桶绿', '#3d5f4c', rough=0.62)
    M['bin_blue'] = mat_basic('垃圾桶蓝', '#3c5d72', rough=0.62)
    M['bin_dark'] = mat_basic('桶盖', '#2b3731', rough=0.65)
    M['soil_dark'] = mat_basic('树池土', '#3d3023', rough=1.0)
    M['tree_grate'] = mat_basic('树池铁篦', '#42443f', rough=0.7, metal=0.4)
    M['shrub'] = mat_leaf('灌木叶', '#456d35', '#7f9a46')
    M['hedge'] = mat_leaf('绿篱', '#375a2d', '#6d863d')
    M['leaf_litter1'] = mat_basic('落叶黄', '#8d6b2e', rough=0.95)
    M['leaf_litter2'] = mat_basic('落叶褐', '#6c4a28', rough=0.95)
    M['puddle'] = mat_basic('积水', '#202725', rough=0.06, metal=0.35, spec=1.0)
    M['sign_blue_street'] = mat_basic('路牌蓝', '#1e4b75', rough=0.4)
    M['sign_white'] = mat_basic('路牌白', '#d7d4c4', rough=0.45)
    M['lamp_glass'] = mat_basic('路灯玻璃', '#c9d1c2', rough=0.2,
                                emission=H('#ffd99b'), emission_strength=0.25)
    M['paper_bag'] = mat_basic('牛皮纸袋', '#9c7444', rough=0.9)
    M['flower_red'] = mat_basic('红花', '#9d3b33', rough=0.7)
    M['flower_yellow'] = mat_basic('黄花', '#b08e32', rough=0.7)
    M['pole_concrete'] = mat_concrete('电线杆', '#9b968b', '#6d6960', rough=0.85, scale=2)
    M['transformer'] = mat_basic('变压器', '#7e857e', rough=0.52, metal=0.4)
    M['insulator'] = mat_basic('绝缘子', '#b5b6a9', rough=0.3)
    M['wire'] = mat_basic('电线', '#1f211f', rough=0.55)
    M['chalk'] = mat_basic('粉笔', '#c7c3b4', rough=0.9)
    M['tar'] = mat_basic('沥青补丁', '#262725', rough=0.9)
    M['neighbor_wall'] = mat_wall_tile('邻楼外墙', '#b5aa97', '#a79c88', '#7c7568',
                                       rough=0.62, dirt=0.42)
    M['neighbor_wall2'] = mat_wall_tile('邻楼外墙2', '#a9b0a6', '#9ba296', '#71756c',
                                         rough=0.62, dirt=0.4)
    M['neighbor_trim'] = mat_basic('邻楼线条', '#c7bfb0', rough=0.7)
    M['neighbor_glass'] = mat_glass('邻楼玻璃', (0.1, 0.16, 0.16, 1.0), 0.06, 0.85)
    M['distant'] = mat_basic('远景楼', '#8c9290', rough=0.9)
    M['distant2'] = mat_basic('远景楼2', '#7f8785', rough=0.9)
    M['distant_glass'] = mat_basic('远景窗', '#4e5c5d', rough=0.5, metal=0.2)
    return M

# ---------------------------------------------------------------------------
# ground / pavement / road
# ---------------------------------------------------------------------------
def build_ground():
    # large base ground
    add_box('大地', (0, -20, -0.12), (180, 180, 0.2), M['road'], '街道')
    # sidewalk slab
    add_box('人行道垫层', (0, -9.65, 0.055), (100.0, 7.1, 0.18),
            M['grout'], '街道')
    _build_paving()
    _build_curbs()
    # road
    add_box('车行道', (0, -19.9, -0.02), (110.0, 13.8, 0.08),
            M['road'], '街道')
    _build_road_details()
    # far side pavement strip to ground the opposite edge
    add_box('路对面路缘', (0, -27.1, 0.07), (110.0, 0.3, 0.16),
            M['curb'], '街道')
    add_box('路对面地面', (0, -31.0, 0.0), (110.0, 8.0, 0.12),
            M['curb'], '街道')
    # low dusty verge beyond
    add_box('远处地面', (0, -50.0, -0.03), (180, 40.0, 0.10),
            M['road'], '街道')

def _build_paving():
    # individual tiles, slightly irregular, materials assigned per tile
    x0, x1 = -50.0, 50.0
    y0, y1 = -13.05, -6.16
    tile = 0.60
    gap = 0.018
    verts, faces, midx = [], [], []
    nx = int((x1 - x0) / tile)
    ny = int((y1 - y0) / tile)
    mats = [M['paver1'], M['paver2'], M['paver3']]
    for ix in range(nx):
        for iy in range(ny):
            xa = x0 + ix * tile + gap / 2
            xb = x0 + (ix + 1) * tile - gap / 2
            ya = y0 + iy * tile + gap / 2
            yb = y0 + (iy + 1) * tile - gap / 2
            # occasional missing / broken tile
            r = rand.random()
            if r < 0.006:
                continue
            z = 0.155 + rand.uniform(-0.002, 0.002)
            if r > 0.94:
                z -= 0.006
            i = len(verts)
            verts.extend([(xa, ya, z), (xb, ya, z), (xb, yb, z), (xa, yb, z)])
            faces.append((i, i + 1, i + 2, i + 3))
            midx.append(rand.randrange(3))
    mesh = bpy.data.meshes.new('人行道地砖')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    for m in mats:
        mesh.materials.append(m)
    for p, mi in zip(mesh.polygons, midx):
        p.material_index = mi
    ob = bpy.data.objects.new('人行道地砖', mesh)
    C('街道').objects.link(ob)
    # tactile strip near the curb
    add_box('盲道', (0, -12.45, 0.165), (80.0, 0.32, 0.025),
            M['curb_yellow'], '街道')
    for i in range(90):
        x = -39 + i * 0.88
        add_cyl('盲道点' + str(i), (x, -12.45, 0.183), 0.018, 0.012,
                M['curb_yellow'], '街道', vertices=8)

def _build_curbs():
    for x in [(-50 + i * 3.0 + 1.5) for i in range(34)]:
        add_box('路缘石' + str(x), (x, -13.18, 0.085), (2.98, 0.28, 0.17),
                M['curb'], '街道', rot=(0, 0, rand.uniform(-0.006, 0.006)),
                bevel=0.01)
    # yellow curb paint, worn
    for x in (-36, -24, -12, 2, 14, 28, 40):
        add_box('路缘黄漆' + str(x), (x, -13.34, 0.09), (2.0, 0.03, 0.14),
                M['curb_yellow'], '街道')
    # drains along the curb
    for x in (-32, -18, -5, 9, 22, 37):
        add_box('雨水篦子框' + str(x), (x, -13.32, 0.025), (0.72, 0.34, 0.04),
                M['metal_gray'], '街道')
        for k in range(7):
            add_box('雨水篦条' + str(x) + str(k), (x - 0.27 + k * 0.09, -13.32, 0.05),
                    (0.035, 0.3, 0.015), M['tar'], '街道')
        add_box('雨水沟' + str(x), (x, -13.45, -0.01), (1.2, 0.25, 0.06),
                M['tar'], '街道')

def _build_road_details():
    # dashed centre line
    for i in range(18):
        x = -48 + i * 5.6
        add_box('道路虚线' + str(i), (x, -20.0, 0.021), (2.5, 0.11, 0.008),
                M['line_white'], '街道')
    # faded edge line
    add_box('道路边线', (0, -14.4, 0.018), (100.0, 0.08, 0.006),
            M['line_white'], '街道')
    # patched asphalt, tar seams and cracks
    patches = [(-17, -17.0, 4.8, 2.0, 0.08), (6.0, -23.0, 5.0, 2.6, -0.06),
               (24.0, -15.6, 3.0, 1.2, 0.0), (-33.0, -24.0, 4.0, 2.2, 0.1)]
    for i, (x, y, w, h, rot) in enumerate(patches):
        add_box('沥青补丁' + str(i), (x, y, 0.025), (w, h, 0.012),
                M['tar'], '街道', rot=(0, 0, rot))
    for i in range(9):
        x = rand.uniform(-45, 45)
        y = rand.uniform(-26, -14)
        pts = [(x, y, 0.032)]
        for k in range(rand.randint(2, 5)):
            x += rand.uniform(-0.8, 0.8)
            y += rand.uniform(-0.8, 0.8)
            pts.append((x, y, 0.032))
        add_curve('路面裂缝' + str(i), pts, 0.007,
                  M['tar'], '街道', resolution=2)
    # manholes
    for i, (x, y) in enumerate([(-2.8, -18.0), (19.0, -22.7), (-29.0, -15.7)]):
        add_cyl('井盖' + str(i), (x, y, 0.031), 0.38, 0.025, M['metal_gray'],
                '街道', vertices=28)
        add_cyl('井盖圈' + str(i), (x, y, 0.037), 0.30, 0.018, M['rust'],
                '街道', vertices=28)
        for k in range(6):
            a = k * math.pi / 3
            add_box('井盖纹' + str(i) + str(k),
                    (x + math.cos(a) * 0.17, y + math.sin(a) * 0.17, 0.045),
                    (0.22, 0.025, 0.006), M['tar'], '街道',
                    rot=(0, 0, a))
    # puddles
    for i, (x, y, w, h) in enumerate([(-4.0, -24.0, 2.2, 0.9),
                                       (17.0, -16.4, 1.3, 0.6),
                                       (-21.0, -21.5, 1.7, 0.8)]):
        _puddle('路面积水' + str(i), (x, y), w, h)
    # fallen leaves along the curb / trees
    _leaf_litter()

def _puddle(name, center, w, h):
    n = 18
    verts = [(center[0], center[1], 0.033)]
    for i in range(n):
        a = math.tau * i / n
        r = 0.72 + 0.28 * math.sin(a * 3 + rand.random())
        verts.append((center[0] + math.cos(a) * w / 2 * r,
                      center[1] + math.sin(a) * h / 2 * r, 0.033))
    faces = [(0, i + 1, (i + 1) % n + 1) for i in range(n)]
    add_mesh(name, verts, faces, M['puddle'], '街道', smooth=True)

def _leaf_litter():
    mats = [M['leaf_litter1'], M['leaf_litter2'], M['leaf_green'] if 'leaf_green' in M else M['leaf_litter1']]
    verts, faces, midx = [], [], []
    for i in range(260):
        x = rand.uniform(-40, 40)
        y = rand.uniform(-13.4, -6.4)
        # more leaves near tree positions
        if rand.random() < 0.5:
            x = rand.choice([-21.5, 8.5, 27.5]) + rand.uniform(-5, 5)
        z = 0.166 if y > -13.1 else 0.036
        a = rand.uniform(0, math.tau)
        l = rand.uniform(0.05, 0.11)
        w = l * rand.uniform(0.35, 0.55)
        pts = [(x + math.cos(a) * l, y + math.sin(a) * l),
               (x - math.sin(a) * w, y + math.cos(a) * w),
               (x - math.cos(a) * l, y - math.sin(a) * l),
               (x + math.sin(a) * w, y - math.cos(a) * w)]
        idx = len(verts)
        for p in pts:
            verts.append((p[0], p[1], z))
        faces.append((idx, idx + 1, idx + 2, idx + 3))
        midx.append(rand.randrange(3))
    mesh = bpy.data.meshes.new('地面落叶')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    for m in mats:
        mesh.materials.append(m)
    for p, mi in zip(mesh.polygons, midx):
        p.material_index = mi
    ob = bpy.data.objects.new('地面落叶', mesh)
    C('街道').objects.link(ob)

# ---------------------------------------------------------------------------
# trees
# ---------------------------------------------------------------------------
def _branch(name, p1, p2, r1, r2, mat):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    ob = add_cone(name, (p1 + p2) / 2, r1, r2, d.length, mat, '植物', vertices=10)
    ob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    return ob

def make_tree(name, loc, scale=1.0, seed=1):
    r = random.Random(seed)
    base = Vector(loc)
    tips = []
    # trunk, slightly leaning
    segs = 4
    p = base.copy()
    direction = Vector((0.03, -0.015, 1.0)).normalized()
    for s in range(segs):
        length = 1.65 * scale
        nxt = p + direction * length + Vector((r.uniform(-0.05, 0.05),
                                               r.uniform(-0.05, 0.05), 0))
        _branch(name + '_干' + str(s), p, nxt, (0.24 - s * 0.035) * scale,
                (0.21 - s * 0.035) * scale, M['bark'])
        p = nxt
        direction = (direction + Vector((r.uniform(-0.10, 0.10),
                     r.uniform(-0.10, 0.10), 0.06))).normalized()
    # primary branches from the upper trunk
    n_primary = 5
    for i in range(n_primary):
        ang = math.tau * i / n_primary + r.uniform(-0.4, 0.4)
        tilt = r.uniform(0.55, 1.05)
        d = Vector((math.cos(ang) * math.sin(tilt),
                    math.sin(ang) * math.sin(tilt), math.cos(tilt)))
        start = p - direction * r.uniform(0.2, 1.0)
        _grow_branch(name, start, d, 1.55 * scale, 0.085 * scale, 3, tips, r,
                     depth0=0)
    # make sure the crown is full: extra internal tips
    for i in range(16):
        a = r.uniform(0, math.tau)
        rr = r.uniform(0.6, 3.4) * scale
        tips.append(Vector((base.x + math.cos(a) * rr,
                            base.y + math.sin(a) * rr,
                            base.z + r.uniform(4.8, 7.3) * scale)))
    _make_leaf_canopy(name, tips, scale, r)
    # tree pit soil and grate
    add_cyl(name + '_树池', (loc[0], loc[1], 0.171), 0.72 * scale, 0.02,
            M['soil_dark'], '植物', vertices=24)
    for i in range(8):
        a = math.tau * i / 8
        add_box(name + '_树篦' + str(i),
                (loc[0] + math.cos(a) * 0.42 * scale,
                 loc[1] + math.sin(a) * 0.42 * scale, 0.187),
                (0.55 * scale, 0.045, 0.018), M['tree_grate'], '植物',
                rot=(0, 0, a + math.pi / 2))
    add_cyl(name + '_树箍', (loc[0], loc[1], 0.19), 0.7 * scale, 0.035,
            M['tree_grate'], '植物', vertices=24)
    # small weeds at the base
    for i in range(9):
        a = r.uniform(0, math.tau)
        rr = r.uniform(0.4, 0.9) * scale
        add_cone(name + '_草' + str(i),
                 (loc[0] + math.cos(a) * rr, loc[1] + math.sin(a) * rr, 0.2),
                 0.015, 0.004, r.uniform(0.18, 0.4), M['shrub'], '植物',
                 vertices=4, rot=(r.uniform(-0.2, 0.2), r.uniform(-0.2, 0.2), 0))

def _grow_branch(name, start, direction, length, radius, depth, tips, r, depth0=0):
    end = start + direction.normalized() * length
    _branch(name + f'_枝{depth0}_{len(tips)}', start, end,
            radius, radius * 0.62, M['bark'])
    if depth <= 0:
        tips.append(end)
        return
    n = 2 if depth == 1 else r.choice([2, 2, 3])
    for k in range(n):
        a = r.uniform(0, math.tau)
        tilt = r.uniform(0.35, 0.9)
        nd = direction.normalized() + Vector((math.cos(a) * math.sin(tilt) * 0.8,
                                              math.sin(a) * math.sin(tilt) * 0.8,
                                              r.uniform(0.1, 0.45)))
        # keep branches outward and up
        nd.z = max(nd.z, 0.12)
        _grow_branch(name, end, nd.normalized(), length * r.uniform(0.55, 0.72),
                     radius * 0.58, depth - 1, tips, r, depth0 + 1)

def _make_leaf_canopy(name, tips, scale, r):
    verts, faces, midx = [], [], []
    mats = [M['leaf1'], M['leaf2'], M['leaf3']]
    leaf_count = 0
    for tip in tips:
        # dense cluster around each tip; large enough cards read at street scale
        count = 76 if scale > 0.8 else 48
        for k in range(count):
            theta = r.uniform(0, math.tau)
            phi = math.acos(r.uniform(-1, 1))
            rad = r.uniform(0.18, 1.15) * scale
            c = tip + Vector((math.sin(phi) * math.cos(theta) * rad,
                              math.sin(phi) * math.sin(theta) * rad,
                              math.cos(phi) * rad * 0.72))
            # random leaf orientation
            n = Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-1, 1)))
            if n.length < 0.01:
                n = Vector((0, 0, 1))
            n.normalize()
            t = Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-1, 1)))
            t = (t - n * t.dot(n))
            if t.length < 0.01:
                t = n.orthogonal()
            t.normalize()
            b = n.cross(t)
            ll = r.uniform(0.17, 0.31) * scale
            ww = r.uniform(0.062, 0.118) * scale
            i = len(verts)
            verts.extend([
                tuple(c - t * ll * 0.5),
                tuple(c + b * ww),
                tuple(c + t * ll * 0.5),
                tuple(c - b * ww),
            ])
            faces.append((i, i + 1, i + 2, i + 3))
            midx.append(r.randrange(3))
            leaf_count += 1
    mesh = bpy.data.meshes.new(name + '_树冠')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    for m in mats:
        mesh.materials.append(m)
    for p, mi in zip(mesh.polygons, midx):
        p.material_index = mi
    ob = bpy.data.objects.new(name + '_树冠', mesh)
    C('植物').objects.link(ob)
    print('TREE', name, 'leaves', leaf_count)

def build_trees():
    make_tree('梧桐1', (-21.8, -10.6, 0.16), 1.12, seed=21)
    make_tree('梧桐2', (17.8, -10.4, 0.16), 0.92, seed=33)
    make_tree('梧桐3', (25.8, -10.8, 0.16), 1.06, seed=52)
    make_tree('梧桐4', (-38.0, -10.4, 0.16), 0.9, seed=77)
    # distant tree line at the far side for depth
    for i, x in enumerate((-55, -43, 34, 52)):
        make_tree('远树' + str(i), (x, -32.0, 0.1), 0.75, seed=100 + i)

def build_planting():
    # green hedge planters at the two outer bays of the main building
    for side, x in [(-1, -16.9), (1, 16.9)]:
        add_box('花池' + str(side), (x, -8.0, 0.36), (2.0, 1.0, 0.55),
                M['brick'], '植物', bevel=0.02)
        add_box('花池土' + str(side), (x, -8.0, 0.65), (1.86, 0.86, 0.08),
                M['soil_dark'], '植物')
        for i in range(8):
            px = x + rand.uniform(-0.8, 0.8)
            py = -8.0 + rand.uniform(-0.35, 0.35)
            add_ico('灌木' + str(side) + str(i), (px, py, 0.8 + rand.uniform(0, 0.2)),
                    rand.uniform(0.24, 0.38), M['hedge'], '植物', subdiv=1,
                    scale=(1.0, 1.0, 0.85))
    # a few potted shrubs along the wall and by the shops
    for i, (x, y) in enumerate([(-17.4, -7.5), (17.4, -7.6), (-4.0, -7.0),
                                 (12.9, -7.2), (-10.4, -7.35)]):
        _pot_plant('街边盆栽' + str(i), (x, y, 0.16), rand.uniform(0.8, 1.3))

def _pot_plant(name, loc, scale):
    x, y, z = loc
    add_cone(name + '_盆', (x, y, z + 0.2 * scale), 0.18 * scale, 0.24 * scale,
             0.4 * scale, M['terracotta'], '植物', vertices=16)
    add_cyl(name + '_土', (x, y, z + 0.39 * scale), 0.21 * scale, 0.02,
            M['soil_dark'], '植物', vertices=16)
    for k in range(9):
        a = rand.uniform(0, math.tau)
        rr = rand.uniform(0.05, 0.23) * scale
        add_ico(name + f'_叶{k}', (x + math.cos(a) * rr, y + math.sin(a) * rr,
                z + rand.uniform(0.45, 0.72) * scale), rand.uniform(0.13, 0.22) * scale,
                M['shrub'], '植物', subdiv=1, scale=(1, 1, 0.7))
    # a few flower dots
    for k in range(5):
        a = rand.uniform(0, math.tau)
        rr = rand.uniform(0.08, 0.2) * scale
        add_uvsphere(name + f'_花{k}', (x + math.cos(a) * rr, y + math.sin(a) * rr,
                     z + rand.uniform(0.55, 0.76) * scale), 0.035,
                     M['flower_red'] if k % 2 else M['flower_yellow'], '植物',
                     segments=8, rings=5)

# ---------------------------------------------------------------------------
# utility pole, wires, street lamps
# ---------------------------------------------------------------------------
def build_utilities():
    poles = [(-8.6, -12.55, 9.7), (28.5, -12.55, 9.4)]
    for i, (x, y, h) in enumerate(poles):
        add_cone('电线杆' + str(i), (x, y, h / 2 + 0.16), 0.19, 0.11, h,
                 M['pole_concrete'], '街道', vertices=12)
        add_cyl('电线杆帽' + str(i), (x, y, h + 0.2), 0.12, 0.14,
                M['concrete'], '街道', vertices=10)
        # climbing pegs
        for k in range(6):
            z = 2.3 + k * 0.75
            add_cyl('脚钉' + str(i) + str(k), (x + 0.16, y, z), 0.012, 0.3,
                    M['rust'], '街道', vertices=6, rot=(0, math.pi / 2, 0))
        # crossarms
        for j, z in enumerate((h - 0.55, h - 1.15)):
            add_box('横担' + str(i) + str(j), (x, y, z), (2.35, 0.09, 0.09),
                    M['metal_gray'], '街道')
            for k in range(3):
                ix = x - 0.95 + k * 0.95
                add_cone('绝缘子' + str(i) + str(j) + str(k),
                         (ix, y, z + 0.13), 0.055, 0.04, 0.16,
                         M['insulator'], '街道', vertices=8)
        # transformer
        if i == 0:
            add_cyl('变压器', (x + 0.42, y + 0.2, h - 2.3), 0.34, 0.82,
                    M['transformer'], '街道', vertices=18)
            add_box('变压器架', (x + 0.2, y + 0.1, h - 2.75), (0.7, 0.55, 0.08),
                    M['metal_gray'], '街道')
            add_cyl('变压器套管1', (x + 0.42, y + 0.2, h - 1.83), 0.07, 0.2,
                    M['insulator'], '街道', vertices=8)
            add_cyl('变压器套管2', (x + 0.42, y + 0.2, h - 1.83), 0.07, 0.2,
                    M['insulator'], '街道', vertices=8)
            add_box('配电箱', (x - 0.45, y + 0.25, 4.2), (0.5, 0.35, 0.8),
                    M['transformer'], '街道', bevel=0.01)
        # street sign
        add_box('路牌' + str(i), (x + 0.04, y - 0.2, 3.3), (0.04, 0.9, 0.32),
                M['sign_blue_street'], '街道')
        add_text('路牌字' + str(i), '幸福路', (x + 0.075, y - 0.2, 3.3), 0.16,
                 M['sign_white'], '标识', rot=(math.pi / 2, 0, math.pi / 2),
                 font=FONT_BOLD)
        # a few taped notices
        add_box('电线杆告示' + str(i), (x - 0.04, y - 0.2, 2.0), (0.02, 0.28, 0.38),
                M['paper'], '街道')
    # messenger wires along the street, with sag
    for k, dz in enumerate((0.0, 0.33, 0.67)):
        add_curve('主电线1_' + str(k),
                  catenary((-52, -12.55, 8.9 + dz), (-8.6, -12.55, 8.9 + dz),
                           sag=0.55, n=24), 0.011, M['wire'], '街道')
        add_curve('主电线2_' + str(k),
                  catenary((-8.6, -12.55, 8.9 + dz), (28.5, -12.55, 8.65 + dz),
                           sag=0.65, n=30), 0.011, M['wire'], '街道')
        add_curve('主电线3_' + str(k),
                  catenary((28.5, -12.55, 8.65 + dz), (58, -12.55, 8.7 + dz),
                           sag=0.5, n=24), 0.011, M['wire'], '街道')
    # service drops to the building
    for k, dz in enumerate((0.0, 0.25, 0.5, 0.8)):
        add_curve('入户线' + str(k),
                  catenary((-8.6, -12.55, 8.5 - dz), (-13.0, -6.05, 7.4 + dz * 0.4),
                           sag=0.7, n=26), 0.008, M['wire'], '街道')
    add_curve('楼顶拉线', catenary((28.5, -12.55, 8.6), (17.8, 2.4, 22.1),
              sag=1.0, n=28), 0.008, M['wire'], '街道')
    add_curve('斜拉线', [(28.5, -12.55, 9.5), (-8.6, -12.55, 9.3)],
              0.006, M['wire'], '街道')
    # street lamps
    for i, (x, y) in enumerate([(-18.0, -12.8), (13.0, -12.8)]):
        _street_lamp('路灯' + str(i), (x, y, 0.16), 6.8)
    # small junction boxes on the lines
    for i, x in enumerate((-4.0, 19.0)):
        add_box('接线盒' + str(i), (x, -12.55, 8.25), (0.22, 0.22, 0.3),
                M['transformer'], '街道')
    # birds on the wires
    for i, x in enumerate((-1.0, 4.5, 16.0, 31.0)):
        _bird('麻雀' + str(i), (x, -12.54, 8.6 - 0.05 * math.sin((x + 8.6) / 8)))

def _street_lamp(name, loc, height):
    x, y, z = loc
    add_cyl(name + '_杆', (x, y, z + height / 2), 0.085, height,
            M['metal_gray'], '街道', vertices=12)
    add_cyl(name + '_座', (x, y, z + 0.14), 0.22, 0.28,
            M['concrete'], '街道', vertices=14)
    # curved arm and lamp head
    pts = [(x, y, z + height), (x, y - 0.4, z + height + 0.2),
           (x, y - 1.5, z + height + 0.22), (x, y - 1.7, z + height + 0.1)]
    add_curve(name + '_臂', pts, 0.06, M['metal_gray'], '街道', resolution=4)
    add_box(name + '_灯头', (x, y - 1.8, z + height + 0.02), (0.55, 0.85, 0.18),
            M['metal_gray'], '街道', bevel=0.04)
    add_box(name + '_灯罩', (x, y - 1.8, z + height - 0.08), (0.42, 0.68, 0.06),
            M['lamp_glass'], '街道')
    add_box(name + '_灯罩框', (x, y - 1.8, z + height - 0.13), (0.46, 0.72, 0.03),
            M['metal_gray'], '街道')

def _bird(name, loc):
    x, y, z = loc
    add_uvsphere(name + '_身', (x, y, z), 0.075, M['hair_black'], '动物',
                 segments=10, rings=6)
    add_uvsphere(name + '_头', (x + 0.06, y, z + 0.055), 0.045,
                 M['hair_black'], '动物', segments=8, rings=5)
    add_cone(name + '_喙', (x + 0.105, y, z + 0.055), 0.015, 0.002, 0.045,
             M['yellow_paint'], '动物', vertices=6, rot=(0, math.pi / 2, 0))
    for sx in (-1, 1):
        add_box(name + '_翅' + str(sx), (x, y + sx * 0.055, z - 0.01),
                (0.08, 0.04, 0.015), M['hair_black'], '动物',
                rot=(0, 0, sx * 0.25))

# ---------------------------------------------------------------------------
# cars, bikes, scooters, tricycle
# ---------------------------------------------------------------------------
class LocalGroup:
    def __init__(self, name, loc, rot=(0, 0, 0), coll='车辆'):
        self.e = bpy.data.objects.new(name, None)
        C(coll).objects.link(self.e)
        self.e.location = loc
        self.e.rotation_euler = rot
        self.coll = coll
        self.n = 0
    def box(self, name, c, size, mat, bevel=0.0, rot=(0, 0, 0)):
        ob = add_box(self.e.name + '_' + name, (0, 0, 0), size, mat, self.coll, bevel=bevel)
        ob.parent = self.e
        ob.location = c
        ob.rotation_euler = rot
        return ob
    def cyl(self, name, c, r, d, mat, vertices=16, rot=(0, 0, 0)):
        ob = add_cyl(self.e.name + '_' + name, (0, 0, 0), r, d, mat, self.coll,
                     vertices=vertices)
        ob.parent = self.e
        ob.location = c
        ob.rotation_euler = rot
        return ob
    def curve(self, name, pts, r, mat, resolution=3):
        ob = add_curve(self.e.name + '_' + name, pts, r, mat, self.coll, resolution=resolution)
        ob.parent = self.e
        return ob
    def sphere(self, name, c, r, mat, segments=12, rings=8):
        ob = add_uvsphere(self.e.name + '_' + name, (0, 0, 0), r, mat, self.coll,
                          segments=segments, rings=rings)
        ob.parent = self.e
        ob.location = c
        return ob
    def torus(self, name, c, R, rr, mat, axis='Y'):
        ob = add_torus(self.e.name + '_' + name, (0, 0, 0), R, rr, mat, self.coll, axis=axis)
        ob.parent = self.e
        ob.location = c
        return ob
    def text(self, name, body, c, size, mat, rot=(math.pi/2, 0, math.pi/2), font=None):
        ob = add_text(self.e.name + '_' + name, body, (0, 0, 0), size, mat,
                      '标识', rot=rot, font=font or FONT_BOLD)
        ob.parent = self.e
        ob.location = c
        return ob

def make_car(name, loc, rot_z=0.0, paint=None, kind='sedan'):
    paint = paint or M['car_white']
    g = LocalGroup(name, loc, (0, 0, rot_z), '车辆')
    if kind == 'sedan':
        # lower body, hood and boot
        g.box('车身', (0, 0, 0.68), (4.52, 1.82, 0.52), paint, bevel=0.08)
        g.box('机盖', (1.48, 0, 0.97), (1.48, 1.76, 0.16), paint, bevel=0.05)
        g.box('后备箱', (-1.62, 0, 0.97), (1.05, 1.76, 0.20), paint, bevel=0.04)
        # cabin: a tapered box with glass
        verts = [(-1.12, -0.82, 0.94), (1.05, -0.82, 0.94),
                 (1.00, 0.82, 0.94), (-1.12, 0.82, 0.94),
                 (-0.85, -0.74, 1.56), (0.62, -0.74, 1.56),
                 (0.55, 0.74, 1.56), (-0.85, 0.74, 1.56)]
        faces = [(0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7),
                 (4,5,6,7), (0,3,2,1)]
        ob = add_mesh(name + '_车顶', verts, faces, paint, '车辆', smooth=False)
        ob.parent = g.e
        # glass panels
        g.box('前挡', (0.83, 0, 1.29), (0.04, 1.44, 0.58), M['car_glass'],
              rot=(0, 0.38, 0))
        g.box('后挡', (-1.0, 0, 1.29), (0.04, 1.44, 0.56), M['car_glass'],
              rot=(0, -0.34, 0))
        for sy in (-1, 1):
            g.box('侧窗前' + str(sy), (0.15, sy * 0.78, 1.3),
                  (0.92, 0.035, 0.47), M['car_glass'])
            g.box('侧窗后' + str(sy), (-0.77, sy * 0.76, 1.3),
                  (0.68, 0.035, 0.44), M['car_glass'])
            g.box('B柱' + str(sy), (-0.2, sy * 0.77, 1.28),
                  (0.08, 0.04, 0.5), M['black_paint'])
        # trim, bumpers, lights
        g.box('前杠', (2.28, 0, 0.55), (0.12, 1.78, 0.28), M['car_silver'], bevel=0.03)
        g.box('后杠', (-2.28, 0, 0.55), (0.12, 1.78, 0.28), M['car_silver'], bevel=0.03)
        g.box('中网', (2.25, 0, 0.79), (0.05, 1.1, 0.2), M['black_paint'])
        for k in range(5):
            g.box('格栅' + str(k), (2.28, 0, 0.72 + k * 0.035),
                  (0.03, 1.0, 0.012), M['chrome_car'])
        g.box('前灯L', (2.26, -0.62, 0.88), (0.06, 0.36, 0.16), M['headlight'])
        g.box('前灯R', (2.26, 0.62, 0.88), (0.06, 0.36, 0.16), M['headlight'])
        g.box('尾灯L', (-2.26, -0.62, 0.85), (0.06, 0.34, 0.18), M['taillight'])
        g.box('尾灯R', (-2.26, 0.62, 0.85), (0.06, 0.34, 0.18), M['taillight'])
        g.box('车标', (2.3, 0, 0.9), (0.015, 0.13, 0.13), M['chrome_car'])
        for sy in (-1, 1):
            g.box('后视镜' + str(sy), (0.72, sy * 0.94, 1.18),
                  (0.16, 0.18, 0.1), paint, bevel=0.02)
            g.cyl('后视镜杆' + str(sy), (0.72, sy * 0.86, 1.16),
                  0.018, 0.16, M['black_paint'], vertices=6,
                  rot=(math.pi / 2, 0, 0))
        # door seams and handles
        for sy in (-1, 1):
            for dx in (-0.85, 0.3):
                g.box('门缝' + str(sy) + str(dx), (dx, sy * 0.915, 0.78),
                      (0.014, 0.01, 0.5), M['black_paint'])
                g.box('门把' + str(sy) + str(dx), (dx + 0.15, sy * 0.93, 0.99),
                      (0.14, 0.025, 0.035), M['chrome_car'])
        # wheels
        for ix, sx in enumerate((-1.42, 1.42)):
            for iy, sy in enumerate((-0.86, 0.86)):
                g.cyl('轮胎' + str(ix) + str(iy), (sx, sy, 0.42), 0.34, 0.24,
                      M['tire'], vertices=24, rot=(math.pi / 2, 0, 0))
                g.cyl('轮毂' + str(ix) + str(iy), (sx, sy * 1.005, 0.42), 0.21, 0.25,
                      M['rim'], vertices=20, rot=(math.pi / 2, 0, 0))
                g.cyl('轴心' + str(ix) + str(iy), (sx, sy * 1.02, 0.42), 0.055, 0.26,
                      M['chrome_car'], vertices=12, rot=(math.pi / 2, 0, 0))
        # license plates (front + rear)
        g.box('前牌', (2.31, 0, 0.42), (0.02, 0.46, 0.16), M['license_blue'])
        g.text('前牌字', '苏A·F3T29', (2.325, 0, 0.42), 0.055, M['license_white'],
               rot=(math.pi / 2, 0, math.pi / 2))
        g.box('后牌', (-2.31, 0, 0.42), (0.02, 0.46, 0.16), M['license_blue'])
        g.text('后牌字', '苏A·F3T29', (-2.325, 0, 0.42), 0.055, M['license_white'],
               rot=(math.pi / 2, 0, -math.pi / 2))
        # wipers and exhaust
        for sy in (-0.45, 0.15):
            g.box('雨刮' + str(sy), (2.19, sy, 0.99), (0.02, 0.05, 0.46),
                  M['black_paint'], rot=(0.7, 0, 0))
        g.cyl('排气管', (-2.25, 0.55, 0.28), 0.045, 0.2, M['rust'],
              vertices=10, rot=(0, math.pi / 2, 0))
        # a little dust on the lower panels
        g.box('侧裙', (0, 0, 0.45), (3.6, 1.88, 0.18), M['car_silver'])
    elif kind == 'van':
        g.box('车身', (0, 0, 1.0), (4.7, 1.9, 1.45), paint, bevel=0.1)
        g.box('车头', (2.05, 0, 0.85), (0.7, 1.84, 0.8), paint, bevel=0.08)
        g.box('前挡', (2.22, 0, 1.48), (0.05, 1.5, 0.52), M['car_glass'],
              rot=(0, 0.18, 0))
        for sy in (-1, 1):
            g.box('侧窗' + str(sy), (0.4, sy * 0.94, 1.48),
                  (2.4, 0.03, 0.5), M['car_glass'])
            g.box('滑门缝' + str(sy), (-0.7, sy * 0.955, 0.95),
                  (0.02, 0.01, 1.1), M['black_paint'])
        for ix, sx in enumerate((-1.55, 1.5)):
            for iy, sy in enumerate((-0.9, 0.9)):
                g.cyl('轮' + str(ix) + str(iy), (sx, sy, 0.44), 0.35, 0.26,
                      M['tire'], vertices=24, rot=(math.pi / 2, 0, 0))
                g.cyl('毂' + str(ix) + str(iy), (sx, sy * 1.005, 0.44), 0.19, 0.27,
                      M['rim'], vertices=18, rot=(math.pi / 2, 0, 0))
        g.box('前灯L', (2.4, -0.64, 0.92), (0.06, 0.34, 0.18), M['headlight'])
        g.box('前灯R', (2.4, 0.64, 0.92), (0.06, 0.34, 0.18), M['headlight'])
        g.box('前牌', (2.41, 0, 0.48), (0.02, 0.46, 0.16), M['license_blue'])
    return g

def make_bicycle(name, loc, rot_z=0.0, color=None, basket=True):
    color = color or M['bike_black']
    g = LocalGroup(name, loc, (0, 0, rot_z), '车辆')
    for sx in (-0.58, 0.58):
        g.torus('轮胎' + str(sx), (sx, 0, 0.36), 0.34, 0.022, M['tire'])
        g.cyl('花鼓' + str(sx), (sx, 0, 0.36), 0.045, 0.07, M['chrome'], vertices=12,
              rot=(math.pi / 2, 0, 0))
        for k in range(6):
            a = math.tau * k / 6
            g.box('辐条' + str(sx) + str(k), (sx, 0, 0.36), (0.012, 0.012, 0.58),
                  M['chrome'], rot=(0, a, 0))
    frame_pts = [
        ((-0.58, 0, 0.36), (0.0, 0, 0.82)),
        ((0.0, 0, 0.82), (0.32, 0, 1.03)),
        ((0.32, 0, 1.03), (0.58, 0, 0.36)),
        ((0.32, 0, 1.03), (-0.05, 0, 0.42)),
        ((-0.05, 0, 0.42), (-0.58, 0, 0.36)),
        ((-0.05, 0, 0.42), (0.0, 0, 0.82)),
        ((-0.05, 0, 0.42), (-0.25, 0, 0.9)),
    ]
    for i, (p1, p2) in enumerate(frame_pts):
        tube_between(g.e.name + '_架' + str(i), p1, p2, 0.022, color)
        # parent last object
        bpy.data.objects[g.e.name + '_架' + str(i)].parent = g.e
    # seat, handlebar, basket, pedals
    g.box('车座', (-0.26, 0, 0.95), (0.28, 0.13, 0.06), M['bike_seat'], bevel=0.02)
    g.cyl('座杆', (-0.26, 0, 0.9), 0.018, 0.22, M['chrome'], vertices=8)
    g.cyl('车把立', (0.53, 0, 1.06), 0.02, 0.32, M['chrome'], vertices=8,
          rot=(0, 0.12, 0))
    g.cyl('车把', (0.55, 0, 1.2), 0.016, 0.46, M['chrome'], vertices=8,
          rot=(math.pi / 2, 0, 0))
    for sy in (-1, 1):
        g.cyl('握把' + str(sy), (0.55, sy * 0.2, 1.2), 0.026, 0.12,
              M['bike_seat'], vertices=8, rot=(math.pi / 2, 0, 0))
    g.cyl('前叉', (0.55, 0, 0.75), 0.02, 0.72, color, vertices=8, rot=(0, 0.12, 0))
    g.cyl('曲柄', (0.0, 0, 0.42), 0.045, 0.28, M['chrome'], vertices=8,
          rot=(math.pi / 2, 0, 0))
    g.box('脚蹬L', (0.0, -0.2, 0.3), (0.15, 0.05, 0.03), M['bike_seat'])
    g.box('脚蹬R', (0.0, 0.2, 0.55), (0.15, 0.05, 0.03), M['bike_seat'])
    g.cyl('撑脚', (-0.4, -0.12, 0.18), 0.012, 0.36, M['chrome'], vertices=6,
          rot=(0.3, 0, 0))
    if basket:
        bx, bz = 0.72, 0.92
        g.box('车筐底', (bx, 0, bz - 0.14), (0.3, 0.32, 0.02), M['bike_basket'])
        for sx in (-0.14, 0.14):
            g.box('筐边' + str(sx), (bx + sx, 0, bz), (0.015, 0.32, 0.25),
                  M['bike_basket'])
        for sy in (-0.15, 0.15):
            g.box('筐边y' + str(sy), (bx, sy, bz), (0.3, 0.015, 0.25),
                  M['bike_basket'])
        # wire basket texture
        for k in range(4):
            g.box('筐丝' + str(k), (bx, 0, bz - 0.03 + k * 0.05),
                  (0.29, 0.29, 0.006), M['bike_basket'])
    return g

def make_scooter(name, loc, rot_z=0.0, color=None):
    color = color or M['scooter_white']
    g = LocalGroup(name, loc, (0, 0, rot_z), '车辆')
    for sx in (-0.48, 0.5):
        g.cyl('轮' + str(sx), (sx, 0, 0.27), 0.26, 0.11, M['tire'],
              vertices=22, rot=(math.pi / 2, 0, 0))
        g.cyl('毂' + str(sx), (sx, 0, 0.27), 0.13, 0.12, M['rim'],
              vertices=16, rot=(math.pi / 2, 0, 0))
    g.box('踏板', (0.0, 0, 0.42), (0.95, 0.38, 0.08), M['black_paint'], bevel=0.02)
    g.box('车身', (-0.2, 0, 0.66), (0.75, 0.36, 0.44), color, bevel=0.08)
    g.box('前罩', (0.38, 0, 0.76), (0.22, 0.4, 0.72), color, bevel=0.08,
          rot=(0, -0.18, 0))
    g.box('车座', (-0.3, 0, 0.92), (0.62, 0.3, 0.12), M['bike_seat'], bevel=0.03)
    g.cyl('把立', (0.47, 0, 1.08), 0.025, 0.3, M['chrome'], vertices=8,
          rot=(0, 0.15, 0))
    g.cyl('车把', (0.48, 0, 1.22), 0.02, 0.54, M['chrome'], vertices=8,
          rot=(math.pi / 2, 0, 0))
    for sy in (-1, 1):
        g.cyl('握把' + str(sy), (0.48, sy * 0.24, 1.22), 0.03, 0.13,
              M['bike_seat'], vertices=8, rot=(math.pi / 2, 0, 0))
        g.cyl('镜杆' + str(sy), (0.47, sy * 0.27, 1.36), 0.012, 0.22,
              M['chrome'], vertices=6, rot=(0.1, 0, sy * 0.2))
        g.box('后视镜' + str(sy), (0.45, sy * 0.31, 1.48), (0.03, 0.14, 0.09),
              M['black_paint'], rot=(0, 0, sy * 0.1))
    g.box('前灯', (0.53, 0, 0.96), (0.04, 0.2, 0.12), M['headlight'])
    g.box('后尾箱', (-0.63, 0, 0.87), (0.32, 0.36, 0.26), M['black_paint'], bevel=0.02)
    g.box('牌照', (-0.66, 0, 0.64), (0.02, 0.22, 0.12), M['license_blue'])
    g.cyl('支撑', (-0.1, -0.2, 0.2), 0.012, 0.35, M['chrome'], vertices=6,
          rot=(0.25, 0, 0))
    g.cyl('前叉', (0.48, 0, 0.52), 0.02, 0.5, M['chrome'], vertices=8,
          rot=(0, 0.1, 0))
    return g

def make_tricycle(name, loc, rot_z=0.0):
    g = LocalGroup(name, loc, (0, 0, rot_z), '车辆')
    # wheels: one front, two rear
    g.cyl('前轮', (1.0, 0, 0.32), 0.31, 0.1, M['tire'], vertices=22,
          rot=(math.pi / 2, 0, 0))
    for sy in (-0.55, 0.55):
        g.cyl('后轮' + str(sy), (-0.8, sy, 0.32), 0.31, 0.12, M['tire'],
              vertices=22, rot=(math.pi / 2, 0, 0))
    g.box('车斗', (-0.55, 0, 0.72), (1.4, 1.0, 0.55), M['car_blue'], bevel=0.03)
    g.box('车斗围', (-0.55, 0, 0.99), (1.4, 1.0, 0.06), M['car_silver'])
    g.box('车头', (0.75, 0, 0.8), (0.45, 0.38, 0.75), M['car_blue'], bevel=0.06)
    g.cyl('车把', (0.85, 0, 1.2), 0.02, 0.55, M['chrome'], vertices=8,
          rot=(math.pi / 2, 0, 0))
    g.box('座', (0.45, 0, 1.0), (0.35, 0.3, 0.08), M['bike_seat'])
    g.box('车篷', (0.55, 0, 1.42), (0.5, 1.0, 0.05), M['car_blue'], bevel=0.02,
          rot=(0, 0.1, 0))
    # cargo: cardboard boxes and greens
    for i in range(4):
        g.box('货箱' + str(i), (-0.7 + (i % 2) * 0.45, -0.2 + (i // 2) * 0.45, 1.12),
              (0.42, 0.38, 0.32), M['cardboard'], rot=(0, 0, rand.uniform(-0.2, 0.2)))
    for i in range(6):
        g.sphere('青菜' + str(i), (-0.9 + (i % 3) * 0.25, 0.3, 1.2 + (i // 3) * 0.12),
                 0.13, M['vegetable'], segments=8, rings=5)
    return g

def build_vehicles():
    make_car('白色桑塔纳', (8.5, -15.35, 0.15), rot_z=0.0, paint=M['car_white'])
    make_car('银色面包车', (-20.5, -17.1, 0.15), rot_z=math.pi, paint=M['car_silver'],
             kind='van')
    make_tricycle('三轮车', (-11.2, -16.9, 0.15), rot_z=0.15)
    # bicycles along the shopfront
    bike_specs = [
        ('旧自行车1', (-11.4, -7.8, 0.16), 0.1, M['bike_black']),
        ('共享单车1', (4.5, -7.7, 0.16), -0.15, M['bike_yellow']),
        ('共享单车2', (5.2, -7.6, 0.16), -0.08, M['bike_blue']),
        ('旧自行车2', (11.0, -7.9, 0.16), 0.2, M['bike_red']),
        ('共享单车3', (18.8, -7.9, 0.16), -1.2, M['bike_yellow']),
    ]
    for n, l, r, c in bike_specs:
        make_bicycle(n, l, rot_z=r, color=c)
    make_scooter('电动车1', (1.3, -7.65, 0.16), rot_z=-0.08, color=M['scooter_blue'])
    make_scooter('电动车2', (12.1, -7.7, 0.16), rot_z=0.2, color=M['scooter_white'])
    # bicycle at the tree, leaning
    make_bicycle('树下自行车', (-19.2, -9.4, 0.16), rot_z=1.45, color=M['bike_black'])

# ---------------------------------------------------------------------------
# street furniture
# ---------------------------------------------------------------------------
def build_furniture():
    # bench under the left tree and another by the right tree
    _bench('长椅1', (-18.0, -8.9, 0.16), 0.0)
    _bench('长椅2', (25.3, -8.9, 0.16), math.pi)
    # bins near the notice board
    for i, (x, y, mat) in enumerate([(-2.75, -7.25, M['bin_green']),
                                     (-2.1, -7.3, M['bin_green']),
                                     (-3.4, -7.2, M['bin_blue'])]):
        _wheelie_bin('垃圾桶' + str(i), (x, y, 0.16), mat)
    # trash bags
    for i in range(3):
        add_ico('垃圾袋' + str(i), (-3.9 + i * 0.35, -7.1 - i * 0.12, 0.35),
                rand.uniform(0.24, 0.34), M['tar'], '街道',
                subdiv=2, scale=(1.0, 0.8, 0.9))
    # old sofa / discarded chair by the bins
    add_box('废弃沙发', (16.5, -7.9, 0.48), (1.3, 0.6, 0.35), M['cloth_green'],
            '街道', bevel=0.05)
    add_box('废弃沙发背', (16.5, -7.65, 0.85), (1.3, 0.16, 0.6), M['cloth_green'],
            '街道', bevel=0.04)
    # cat
    _cat('流浪猫', (17.3, -7.4, 0.16), 0.0)
    # a small handcart / cardboard stack by grocery
    add_box('废纸板', (-7.8, -8.2, 0.25), (0.9, 0.6, 0.18), M['cardboard'],
            '街道', rot=(0, 0, 0.2))
    add_box('废纸板2', (-7.6, -8.15, 0.43), (0.8, 0.5, 0.16), M['cardboard_dark'],
            '街道', rot=(0, 0, 0.1))
    # cardboard/ recycling pile near the parking area
    for i in range(5):
        add_box('回收纸箱' + str(i), (10.0 + (i % 3) * 0.38, -8.4 + (i // 3) * 0.35,
                0.26 + (i // 3) * 0.26), (0.42, 0.38, 0.42),
                M['cardboard'], '街道', rot=(0, 0, rand.uniform(-0.2, 0.2)))
    # a makeshift table by the garage
    add_box('旧桌', (12.3, -8.0, 0.62), (0.9, 0.55, 0.06), M['wood'], '街道',
            bevel=0.01)
    for dx, dy in ((-0.35, -0.2), (0.35, -0.2), (-0.35, 0.2), (0.35, 0.2)):
        add_box('旧桌腿' + str(dx) + str(dy), (12.3 + dx, -8.0 + dy, 0.38),
                (0.04, 0.04, 0.5), M['wood'], '街道')
    # parking barrier and motorbike in the side gap
    add_box('停车挡', (19.3, -7.8, 0.45), (0.12, 1.1, 0.6), M['rust'], '街道')
    make_scooter('侧巷电动车', (19.4, -9.4, 0.16), rot_z=math.pi / 2,
                 color=M['scooter_white'])
    # community notice board / recycling sign near bins
    add_box('分类牌', (-2.1, -8.2, 1.0), (0.6, 0.08, 0.85),
            M['sign_green'], '街道', bevel=0.01)
    add_text('分类字', '垃圾分类\n人人有责', (-2.1, -8.25, 1.05), 0.10,
             M['white_paint'], '标识', font=FONT_BOLD)
    # old payphone / power box, tucked into the corner by the side wall
    add_box('旧电话亭', (-17.25, -7.9, 1.2), (0.62, 0.55, 2.1),
            M['blue_paint'], '街道', bevel=0.02)
    add_box('电话亭玻璃', (-17.25, -8.19, 1.55), (0.5, 0.02, 1.1),
            M['glass_frost'], '街道')
    add_text('电话亭字', '公用电话', (-17.25, -8.22, 2.05), 0.08,
             M['white_paint'], '标识', font=FONT_BOLD)

def _bench(name, loc, rot_z):
    g = LocalGroup(name, loc, (0, 0, rot_z), '街道')
    for k in range(3):
        g.box('座条' + str(k), (0, -0.10 + k * 0.06, 0.47), (2.0, 0.05, 0.035),
              M['bench_wood'], bevel=0.008)
    for k in range(2):
        g.box('背条' + str(k), (0, 0.24 + k * 0.07, 0.74 + k * 0.12),
              (2.0, 0.05, 0.07), M['bench_wood'], rot=(0.15, 0, 0), bevel=0.008)
    for sx in (-0.8, 0.8):
        g.box('腿' + str(sx), (sx, 0, 0.25), (0.05, 0.52, 0.5), M['bench_metal'])
        g.box('靠背腿' + str(sx), (sx, 0.24, 0.56), (0.05, 0.05, 0.62),
              M['bench_metal'], rot=(0.12, 0, 0))
    return g

def and_(a, b):
    return b

def _wheelie_bin(name, loc, mat):
    x, y, z = loc
    add_box(name + '_桶', (x, y, z + 0.62), (0.58, 0.55, 0.86), mat, '街道',
            bevel=0.04)
    add_box(name + '_盖', (x, y + 0.02, z + 1.08), (0.62, 0.6, 0.09),
            M['bin_dark'], '街道', bevel=0.03, rot=(0.05, 0, 0))
    add_box(name + '_沿', (x, y, z + 1.02), (0.6, 0.57, 0.04), mat, '街道')
    for sy in (-0.22, 0.22):
        add_cyl(name + '_轮' + str(sy), (x, y + sy, z + 0.12), 0.09, 0.06,
                M['tire'], '街道', vertices=12, rot=(math.pi / 2, 0, 0))
    add_box(name + '_标', (x - 0.3, y, z + 0.67), (0.01, 0.28, 0.28),
            M['white_paint'], '街道')
    add_text(name + '_字', '垃圾', (x - 0.306, y, z + 0.68), 0.09,
             M['ink'], '标识', font=FONT_BOLD, rot=(math.pi / 2, 0, math.pi / 2))

def _cat(name, loc, rot_z):
    x, y, z = loc
    add_uvsphere(name + '_身', (x, y, z + 0.26), 0.19, M['hair_gray'], '动物',
                 segments=14, rings=8)
    add_uvsphere(name + '_头', (x + 0.17, y, z + 0.4), 0.13, M['hair_gray'], '动物',
                 segments=12, rings=8)
    for sy in (-1, 1):
        add_cone(name + '_耳' + str(sy), (x + 0.17, y + sy * 0.07, z + 0.52),
                 0.055, 0.002, 0.12, M['hair_gray'], '动物', vertices=4,
                 rot=(sy * 0.15, 0, 0))
    add_curve(name + '_尾', [(x - 0.17, y, z + 0.28), (x - 0.33, y + 0.1, z + 0.34),
              (x - 0.38, y + 0.22, z + 0.48)], 0.025, M['hair_gray'], '动物')
    for sy in (-0.1, 0.1):
        add_cyl(name + '_腿' + str(sy), (x + 0.1, y + sy, z + 0.1), 0.035, 0.16,
                M['hair_gray'], '动物', vertices=6)
    for sy in (-1, 1):
        add_curve(name + '_胡须' + str(sy),
                  [(x + 0.27, y + sy * 0.03, z + 0.39),
                   (x + 0.37, y + sy * 0.12, z + 0.36)],
                  0.003, M['white_paint'], '动物')

# ---------------------------------------------------------------------------
# people
# ---------------------------------------------------------------------------
def make_person(name, loc, rot_z=0.0, height=1.7, shirt=None, pants=None,
                hair=None, cap=False, bag=None, pose='stand'):
    shirt = shirt or M['shirt_white']
    pants = pants or M['pants_dark']
    hair = hair or M['hair_black']
    g = LocalGroup(name, loc, (0, 0, rot_z), '人物')
    if pose == 'stand':
        # shoes
        for sx in (-0.10, 0.10):
            g.box('鞋' + str(sx), (sx, -0.03, 0.055), (0.14, 0.26, 0.11),
                  M['shoe_black'], bevel=0.03)
            g.cyl('腿' + str(sx), (sx, 0, 0.44), 0.075, 0.76, pants,
                  vertices=10, rot=(0.02, 0, 0))
        g.box('胯', (0, 0, 0.86), (0.36, 0.24, 0.2), pants, bevel=0.06)
        g.box('躯干', (0, 0, 1.1), (0.44, 0.26, 0.45), shirt, bevel=0.09)
        g.box('肩', (0, 0, 1.32), (0.48, 0.27, 0.11), shirt, bevel=0.05)
        # arms with a slight bend
        for sx in (-1, 1):
            g.cyl('上臂' + str(sx), (sx * 0.27, 0, 1.19), 0.055, 0.34, shirt,
                  vertices=8, rot=(0, sx * 0.15, 0))
            g.cyl('小臂' + str(sx), (sx * 0.3, -0.05, 0.93), 0.045, 0.34,
                  M['skin'], vertices=8, rot=(0.25, sx * 0.05, 0))
            g.sphere('手' + str(sx), (sx * 0.31, -0.1, 0.75), 0.06,
                     M['skin'], segments=8, rings=6)
        g.cyl('颈', (0, 0, 1.4), 0.05, 0.1, M['skin'], vertices=8)
        g.sphere('头', (0, 0, 1.52), 0.105, M['skin'], segments=14, rings=9)
        if cap:
            g.cyl('帽', (0, 0, 1.61), 0.115, 0.06, M['hair_black'], vertices=16)
            g.box('帽檐', (0, -0.1, 1.59), (0.17, 0.17, 0.02), M['hair_black'])
        else:
            g.sphere('头发', (0, 0.01, 1.57), 0.108, hair, segments=14, rings=8)
        # nose, ears (tiny but adds profile)
        g.sphere('鼻', (0.0, -0.105, 1.52), 0.022, M['skin'], segments=6, rings=4)
        for sy in (-1, 1):
            g.sphere('耳' + str(sy), (0, sy * 0.103, 1.52), 0.024,
                     M['skin'], segments=6, rings=4)
        if bag:
            bx = 0.34
            g.box('袋', (bx, -0.11, 0.66), (0.24, 0.16, 0.3), bag, bevel=0.03)
            g.curve('袋带', [(bx, -0.11, 0.8), (bx, -0.09, 0.88),
                      (bx + 0.12, -0.11, 0.8)], 0.01, M['bag_red'])
    else:
        # seated pose
        for sx in (-0.11, 0.11):
            g.box('大腿' + str(sx), (sx, -0.1, 0.52), (0.16, 0.45, 0.16), pants,
                  bevel=0.04, rot=(0.15, 0, 0))
            g.cyl('小腿' + str(sx), (sx, -0.3, 0.26), 0.06, 0.42, pants,
                  vertices=8, rot=(0.1, 0, 0))
            g.box('鞋' + str(sx), (sx, -0.34, 0.06), (0.14, 0.25, 0.1),
                  M['shoe_black'], bevel=0.03)
        g.box('胯', (0, 0.02, 0.66), (0.36, 0.3, 0.2), pants, bevel=0.05)
        g.box('躯干', (0, 0.05, 0.91), (0.44, 0.27, 0.46), shirt, bevel=0.09,
              rot=(-0.08, 0, 0))
        g.box('肩', (0, 0.04, 1.12), (0.48, 0.28, 0.11), shirt, bevel=0.05)
        for sx in (-1, 1):
            g.cyl('上臂' + str(sx), (sx * 0.27, 0.02, 1.0), 0.055, 0.34, shirt,
                  vertices=8, rot=(0.05, sx * 0.05, 0))
            g.cyl('小臂' + str(sx), (sx * 0.29, -0.15, 0.84), 0.045, 0.3,
                  M['skin'], vertices=8, rot=(1.0, 0, 0))
            g.sphere('手' + str(sx), (sx * 0.29, -0.3, 0.82), 0.055,
                     M['skin'], segments=8, rings=6)
        g.cyl('颈', (0, 0.04, 1.2), 0.05, 0.1, M['skin'], vertices=8)
        g.sphere('头', (0, 0.04, 1.31), 0.105, M['skin_old'], segments=14, rings=9)
        g.sphere('头发', (0, 0.05, 1.36), 0.107, M['hair_gray'], segments=14, rings=8)
        g.sphere('鼻', (0.0, -0.07, 1.31), 0.022, M['skin_old'], segments=6, rings=4)
    return g

def build_people():
    make_person('老人', (-17.8, -8.55, 0.16), rot_z=-0.1, height=1.68,
                shirt=M['shirt_green'], pants=M['pants_gray'], hair=M['hair_gray'],
                cap=True, pose='sit')
    make_person('店主', (-12.7, -7.6, 0.16), rot_z=2.4, height=1.72,
                shirt=M['shirt_blue'], pants=M['pants_dark'], hair=M['hair_black'],
                bag=None)
    make_person('买菜的阿姨', (1.0, -9.2, 0.16), rot_z=-1.4, height=1.6,
                shirt=M['shirt_red'], pants=M['pants_blue'], hair=M['hair_gray'],
                bag=M['bag_white'])
    make_person('修车师傅', (11.9, -8.7, 0.16), rot_z=0.4, height=1.65,
                shirt=M['shirt_white'], pants=M['pants_dark'], hair=M['hair_black'])
    make_person('路过的学生', (20.2, -9.8, 0.16), rot_z=2.8, height=1.48,
                shirt=M['shirt_white'], pants=M['pants_blue'], hair=M['hair_black'],
                bag=M['bag_red'])

# ---------------------------------------------------------------------------
# neighbouring buildings / compound walls / background
# ---------------------------------------------------------------------------
def _neighbor(x0, x1, floors=5, wall=None, seed=1, shops=None):
    r = random.Random(seed)
    wall = wall or M['neighbor_wall']
    width = x1 - x0
    gh = 3.9
    sh = 2.85
    h = gh + floors * sh
    # volume
    add_box('邻楼主体' + str(seed), ((x0 + x1) / 2, 0.0, h / 2),
            (width, 12.0, h), wall, '邻楼')
    add_box('邻楼背' + str(seed), ((x0 + x1) / 2, 6.02, h / 2),
            (width, 0.12, h), wall, '邻楼')
    add_box('邻楼前墙' + str(seed), ((x0 + x1) / 2, -6.02, h / 2),
            (width, 0.12, h), wall, '邻楼')
    # roof parapet
    add_box('邻楼女儿墙' + str(seed), ((x0 + x1) / 2, -5.95, h + 0.45),
            (width, 0.22, 0.9), wall, '邻楼')
    add_box('邻楼压顶' + str(seed), ((x0 + x1) / 2, -5.95, h + 0.92),
            (width + 0.2, 0.34, 0.1), M['neighbor_trim'], '邻楼')
    # floor bands
    for f in range(floors + 1):
        z = gh + f * sh
        add_box(f'邻楼线{seed}_{f}', ((x0 + x1) / 2, -6.1, z + 0.08),
                (width, 0.2, 0.13), M['neighbor_trim'], '邻楼')
    # upper facade windows and shallow balconies
    n_bays = max(3, int(width / 3.5))
    for f in range(floors):
        z0 = gh + f * sh
        for b in range(n_bays):
            bx = x0 + width * (b + 0.5) / n_bays
            if b % 3 == 1:
                # balcony
                add_box(f'邻楼阳台{seed}_{f}_{b}', (bx, -6.9, z0 + 0.12),
                        (2.0, 1.0, 0.16), M['concrete'], '邻楼')
                add_box(f'邻楼阳台沿{seed}_{f}_{b}', (bx, -7.38, z0 + 0.8),
                        (2.0, 0.08, 0.9), M['neighbor_trim'], '邻楼')
                B.make_grille(f'邻楼栏杆{seed}_{f}_{b}', bx - 0.95, bx + 0.95,
                            z0 + 0.35, z0 + 1.05, -7.42, spacing=0.18,
                            bar=0.016, mat=M['railing'], coll='邻楼')
                add_plane(f'邻楼阳台门{seed}_{f}_{b}', (bx, -6.06, z0 + 1.25),
                          1.8, 2.1, M['neighbor_glass'], '邻楼',
                          rot=(math.pi / 2, 0, 0))
                if r.random() < 0.45:
                    B.add_ac_unit(f'邻楼空调{seed}_{f}_{b}', bx + 0.95, -6.55,
                                z0 + 0.45, body_mat=M['ac_white'], scale=0.9,
                                coll='邻楼')
            else:
                add_box(f'邻楼窗洞{seed}_{f}_{b}', (bx, -6.09, z0 + 1.45),
                        (1.35, 0.03, 1.55), M['dark'], '邻楼')
                add_box(f'邻楼窗台{seed}_{f}_{b}', (bx, -6.2, z0 + 0.63),
                        (1.55, 0.2, 0.08), M['neighbor_trim'], '邻楼')
                add_plane(f'邻楼窗玻璃{seed}_{f}_{b}', (bx, -6.115, z0 + 1.45),
                          1.28, 1.48, M['neighbor_glass'], '邻楼',
                          rot=(math.pi / 2, 0, 0))
                add_boxes(f'邻楼窗框{seed}_{f}_{b}', [
                    ((bx, -6.12, z0 + 0.7), (1.38, 0.04, 0.05)),
                    ((bx, -6.12, z0 + 2.2), (1.38, 0.04, 0.05)),
                    ((bx - 0.67, -6.12, z0 + 1.45), (0.05, 0.04, 1.55)),
                    ((bx + 0.67, -6.12, z0 + 1.45), (0.05, 0.04, 1.55)),
                    ((bx, -6.12, z0 + 1.45), (0.04, 0.04, 1.55)),
                ], M['neighbor_trim'], '邻楼')
                if r.random() < 0.4:
                    B.make_grille(f'邻楼防盗窗{seed}_{f}_{b}', bx - 0.7, bx + 0.7,
                                z0 + 0.67, z0 + 2.23, -6.23, spacing=0.17,
                                bar=0.014, mat=M['metal_gray'], coll='防盗网')
    # ground floor: simple shopfronts
    shops = shops or [('五金建材', '#3e5a66'), ('早点铺', '#8c3730'), ('彩票站', '#4c5d42')]
    for i, (txt, color) in enumerate(shops):
        sx = x0 + width * (i + 0.5) / len(shops)
        add_box(f'邻楼店招{seed}_{i}', (sx, -6.15, 3.45), (width / len(shops) - 0.25, 0.1, 0.8),
                mat_basic(f'邻楼店招色{seed}_{i}', color, rough=0.55), '邻楼')
        add_text(f'邻楼店字{seed}_{i}', txt, (sx, -6.23, 3.45), 0.28,
                 M['white_paint'], '标识', font=FONT_BOLD)
        add_box(f'邻楼门洞{seed}_{i}', (sx, -6.06, 1.65), (width / len(shops) - 0.6, 0.02, 2.3),
                M['neighbor_glass'], '邻楼')
        add_box(f'邻楼雨棚{seed}_{i}', (sx, -6.9, 2.95), (width / len(shops) - 0.4, 1.0, 0.08),
                M['white_metal'], '邻楼', rot=(0.1, 0, 0))
    # drainpipes
    for i, x in enumerate((x0 + 0.4, x1 - 0.4)):
        add_cyl(f'邻楼落水{seed}_{i}', (x, -6.12, h / 2), 0.05, h,
                M['pipe'], '邻楼', vertices=8)
    # roof tank
    add_box(f'邻楼屋顶{seed}', ((x0 + x1) / 2, 0.5, h + 0.1), (width - 0.4, 11.2, 0.12),
            M['roof'], '邻楼')
    add_cyl(f'邻楼水箱{seed}', (x0 + width * 0.35, 2.0, h + 0.9), 0.55, 1.3,
            M['tank_blue'], '邻楼', vertices=18)

def build_neighbours():
    _neighbor(20.2, 45.0, floors=5, seed=101,
              shops=[('五金水暖', '#3d5863'), ('早餐铺', '#8b3630'), ('彩票站', '#4b5c42')])
    _neighbor(-45.0, -20.2, floors=5, seed=203, wall=M['neighbor_wall2'],
              shops=[('修鞋配锁', '#4a5a47'), ('家常菜馆', '#7e302b')])
    # compound wall/gate in the right-hand gap
    for side, x0, x1 in [(-1, -20.2, -18.05), (1, 18.05, 20.2)]:
        add_box('院墙' + str(side), ((x0 + x1) / 2, -6.25, 1.35),
                (x1 - x0, 0.28, 2.4), M['wall_warm'], '邻楼')
        add_box('院墙帽' + str(side), ((x0 + x1) / 2, -6.25, 2.58),
                (x1 - x0 + 0.15, 0.4, 0.12), M['concrete'], '邻楼')
        add_box('院墙门' + str(side), ((x0 + x1) / 2 + 0.25, -6.18, 1.2),
                (0.9, 0.1, 2.1), M['green_metal'], '邻楼')
        add_text('院墙字' + str(side), '幸福里', ((x0 + x1) / 2, -6.43, 2.9),
                 0.22, M['red_paint'], '标识', font=FONT_BOLD)
    # small wall-mounted compound sign
    add_box('社区牌', (19.1, -6.45, 3.1), (1.7, 0.06, 0.5), M['sign_red'],
            '标识', bevel=0.01)
    add_text('社区牌字', '幸福里社区', (19.1, -6.51, 3.1), 0.18,
             M['gold'], '标识', font=FONT_BOLD)

def build_background():
    # distant apartment slabs, softened by atmosphere
    specs = [(-62, 44, 27, 14, M['distant']), (-28, 52, 33, 16, M['distant2']),
             (8, 58, 30, 18, M['distant']), (48, 47, 26, 15, M['distant2']),
             (78, 58, 34, 17, M['distant'])]
    for i, (x, y, h, w, mat) in enumerate(specs):
        add_box('远景楼' + str(i), (x, y, h / 2), (w, 12, h), mat, '远景')
        # window grid suggestion
        for r in range(int(h / 3)):
            for c in range(3):
                add_box('远景窗' + str(i) + str(r) + str(c),
                        (x - w / 2 + 2.0 + c * 3.2, y - 6.06, 2.2 + r * 3.0),
                        (1.5, 0.04, 1.2), M['distant_glass'], '远景')
    # low industrial roof silhouette
    add_box('远处厂房', (22, 36, 3.2), (25, 15, 6.4), M['distant2'], '远景')
    add_box('远处厂房2', (-50, 42, 4.0), (20, 12, 8.0), M['distant'], '远景')

# ---------------------------------------------------------------------------
# final assembly
# ---------------------------------------------------------------------------
def build_street():
    build_ground()
    build_neighbours()
    build_background()
    build_trees()
    build_planting()
    build_utilities()
    build_vehicles()
    build_furniture()
    build_people()
