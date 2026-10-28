# -*- coding: utf-8 -*-
"""Main building: shell, tiled facade, balconies, roof and side details."""
import bpy
import math
import random
from mathutils import Vector, Euler, Matrix
from scene_lib import *

# ---------------------------------------------------------------------------
# dimensions
# ---------------------------------------------------------------------------
W = 36.0
HALF = W / 2
FRONT = -6.0
BACK = 6.0
GROUND_H = 4.35
RES_H = 2.95
NFLOORS = 6
ROOF = GROUND_H + NFLOORS * RES_H       # 22.05
BAY_W = 3.9
BAY_X0 = -17.55
BAY_XS = [BAY_X0 + BAY_W * (i + 0.5) for i in range(9)]
BAY_EDGES = [BAY_X0 + BAY_W * i for i in range(10)]
STAIR_BAYS = {0, 4, 8}
APT_BAYS = [1, 2, 3, 5, 6, 7]
FRONT_Z0 = GROUND_H
rand = random.Random(7319)

# ---------------------------------------------------------------------------
# materials
# ---------------------------------------------------------------------------
def init_materials():
    M = {}
    M['wall'] = mat_wall_tile('米色外墙砖', '#d3c4a9', '#c5b496', '#968c7b',
                              rough=0.55, dirt=0.33)
    M['wall_warm'] = mat_wall_tile('暖灰外墙砖', '#c8b193', '#bba384', '#8f8676',
                                   rough=0.58, dirt=0.38)
    M['wall_stair'] = mat_wall_tile('楼梯间蓝灰砖', '#a9ada5', '#989d96', '#777b73',
                                    rough=0.6, dirt=0.35)
    M['concrete'] = mat_concrete('清水混凝土', '#aaa397', '#746e64', rough=0.8)
    M['concrete_dark'] = mat_concrete('旧混凝土', '#847d70', '#575249', rough=0.84)
    M['trim'] = mat_basic('白色窗套', '#d7d1c2', rough=0.62)
    M['trim_gray'] = mat_basic('灰色窗套', '#8d918f', rough=0.6)
    M['dark'] = mat_basic('室内暗部', '#181512', rough=1.0)
    M['dark_warm'] = mat_basic('室内暖暗部', '#2b1c11', rough=1.0,
                               emission=H('#6b431f'), emission_strength=0.18)
    M['glass'] = mat_glass('窗玻璃', (0.16, 0.25, 0.24, 1.0), 0.045, 0.9)
    M['glass_green'] = mat_glass('绿玻璃', (0.16, 0.29, 0.25, 1.0), 0.06, 0.86)
    M['glass_frost'] = mat_glass('磨砂玻璃', (0.38, 0.47, 0.42, 1.0), 0.24, 0.7)
    M['aluminum'] = mat_basic('铝合金框', '#c9cbc6', rough=0.32, metal=0.6)
    M['aluminum_dark'] = mat_basic('深色铝框', '#565b59', rough=0.36, metal=0.55)
    M['white_metal'] = mat_basic('白色喷塑金属', '#d4d2c9', rough=0.48, metal=0.15)
    M['green_metal'] = mat_basic('墨绿防盗门', '#345548', rough=0.46, metal=0.25)
    M['rust'] = mat_basic('锈铁', '#70452d', rough=0.78, metal=0.3)
    M['railing'] = mat_basic('栏杆白灰', '#c3c1b7', rough=0.5, metal=0.2)
    M['railing_green'] = mat_basic('栏杆绿', '#4d6554', rough=0.5, metal=0.2)
    M['railing_blue'] = mat_basic('栏杆蓝', '#5c7377', rough=0.5, metal=0.2)
    M['ac_white'] = mat_basic('空调白', '#cfcdc2', rough=0.5, metal=0.1)
    M['ac_beige'] = mat_basic('空调米黄', '#c3b89f', rough=0.56, metal=0.05)
    M['ac_gray'] = mat_basic('空调灰', '#a5a49d', rough=0.52, metal=0.1)
    M['ac_dark'] = mat_basic('空调格栅', '#3a3c39', rough=0.6, metal=0.2)
    M['pipe'] = mat_basic('PVC落水管', '#b8b5aa', rough=0.6)
    M['pipe_gray'] = mat_basic('灰色管道', '#8b8b83', rough=0.65)
    M['roof'] = mat_concrete('屋面防水层', '#615e56', '#3f3d38', rough=0.9, scale=2.0)
    M['solar_glass'] = mat_glass('太阳能玻璃', (0.05, 0.11, 0.15, 1.0), 0.08, 0.4)
    M['solar_frame'] = mat_basic('太阳能铝架', '#9fa4a2', rough=0.4, metal=0.7)
    M['tank_blue'] = mat_basic('蓝白水箱', '#d7e0df', rough=0.4)
    M['water_blue'] = mat_basic('蓝色水桶', '#3b7192', rough=0.55)
    M['terracotta'] = mat_basic('陶土花盆', '#a25e3d', rough=0.8)
    M['soil'] = mat_basic('盆土', '#36291e', rough=0.95)
    M['leaf1'] = mat_leaf('叶子A', '#4a7433', '#8da84e')
    M['leaf2'] = mat_leaf('叶子B', '#396230', '#719541')
    M['leaf3'] = mat_leaf('叶子C', '#627f36', '#a0b258')
    M['leaf_dark'] = mat_leaf('叶子深', '#2f4c28', '#5e7b35')
    M['wood'] = mat_basic('旧木头', '#6d5138', rough=0.82)
    M['wood_light'] = mat_basic('浅木', '#a37b51', rough=0.75)
    M['cardboard'] = mat_basic('纸箱', '#a67a4b', rough=0.88)
    M['cardboard_dark'] = mat_basic('旧纸箱', '#785a3d', rough=0.9)
    M['cloth_red'] = mat_basic('红布', '#a63a32', rough=0.9, sheen=0.2)
    M['cloth_blue'] = mat_basic('蓝布', '#5c7891', rough=0.9, sheen=0.2)
    M['cloth_yellow'] = mat_basic('黄布', '#c5a150', rough=0.9, sheen=0.2)
    M['cloth_white'] = mat_basic('白布', '#d7d2c4', rough=0.95, sheen=0.25)
    M['cloth_pink'] = mat_basic('粉布', '#c9918e', rough=0.92, sheen=0.2)
    M['cloth_green'] = mat_basic('绿布', '#6b8064', rough=0.92, sheen=0.2)
    M['cloth_gray'] = mat_basic('灰布', '#8d8b82', rough=0.94, sheen=0.2)
    M['cloth_plaid'] = mat_striped('格子布', '#96855d', '#695e46', scale=18, axis='X')
    M['curtain_cream'] = mat_basic('米色窗帘', '#c1b49e', rough=0.95, sheen=0.3)
    M['curtain_pink'] = mat_basic('粉色窗帘', '#b58d88', rough=0.95, sheen=0.3)
    M['curtain_blue'] = mat_basic('蓝色窗帘', '#78909c', rough=0.95, sheen=0.3)
    M['curtain_green'] = mat_basic('绿色窗帘', '#70816d', rough=0.95, sheen=0.3)
    M['curtain_white'] = mat_basic('白色纱帘', '#d7d0c1', rough=0.98, sheen=0.4)
    M['red_banner'] = mat_basic('红横幅', '#a32322', rough=0.88, sheen=0.25)
    M['gold'] = mat_basic('金色字', '#d8a948', rough=0.4, metal=0.7)
    M['white_paint'] = mat_basic('白漆', '#d9d5c9', rough=0.75)
    M['black_paint'] = mat_basic('黑漆', '#282724', rough=0.7)
    M['red_paint'] = mat_basic('红漆', '#a7352d', rough=0.72)
    M['blue_paint'] = mat_basic('蓝漆', '#31556f', rough=0.72)
    M['yellow_paint'] = mat_basic('黄漆', '#c79c3a', rough=0.72)
    M['sign_board'] = mat_basic('招牌底板', '#a44c3e', rough=0.6)
    M['sign_green'] = mat_basic('绿色招牌', '#2e5a45', rough=0.55)
    M['sign_blue'] = mat_basic('蓝色招牌', '#31576d', rough=0.55)
    M['sign_yellow'] = mat_basic('黄色招牌', '#c39b3d', rough=0.55)
    M['sign_white'] = mat_basic('白色招牌', '#c9c3b4', rough=0.58)
    M['sign_red'] = mat_basic('红色招牌', '#9f302b', rough=0.55)
    M['paper'] = mat_basic('纸张', '#d6cfbc', rough=0.9)
    M['paper_old'] = mat_basic('旧纸', '#b7aa8b', rough=0.95)
    M['ink'] = mat_basic('墨字', '#24211c', rough=0.8)
    M['light_warm'] = mat_emit('室内暖光', '#ffb45e', 1.0)
    M['light_cool'] = mat_emit('冷白灯管', '#d9e5e2', 0.4)
    M['roof_patch'] = mat_basic('屋面补丁', '#4b4842', rough=0.95)
    M['brick'] = mat_basic('红砖', '#8b503a', rough=0.85)
    M['moss'] = mat_basic('青苔', '#435231', rough=1.0)
    M['sign_red_plastic'] = mat_basic('红色亚克力', '#b23b32', rough=0.4, coat=0.2)
    M['metal_gray'] = mat_basic('镀锌铁', '#8d8f88', rough=0.45, metal=0.6)
    return M

MATS = {}

# ---------------------------------------------------------------------------
# custom meshes
# ---------------------------------------------------------------------------
def cloth_panel(name, x_center, y, z_top, width, height, mat, folds=7, amp=0.025,
                coll='阳台'):
    cols, rows = max(folds, 4), 6
    verts, faces = [], []
    for j in range(rows + 1):
        for i in range(cols + 1):
            u = i / cols
            v = j / rows
            x = x_center - width / 2 + u * width
            # slight nonuniform folds and a little swing
            dy = amp * math.sin(u * math.pi * folds) * (0.35 + 0.65 * v)
            dy += amp * 0.4 * math.sin(v * 4.0 + u * 6.0)
            z = z_top - v * height
            verts.append((x, y + dy, z))
    for j in range(rows):
        for i in range(cols):
            a = j * (cols + 1) + i
            faces.append((a, a + cols + 1, a + cols + 2, a + 1))
    return add_mesh(name, verts, faces, mat, coll, smooth=True)

def shirt(name, x_center, y, z_top, width, height, mat, coll='阳台'):
    hw, sh = width / 2, width * 0.38
    verts = [
        (x_center-hw*0.55, y, z_top), (x_center+hw*0.55, y, z_top),
        (x_center+hw*0.56, y, z_top-height*0.16),
        (x_center+sh, y, z_top-height*0.34),
        (x_center+sh*0.92, y, z_top-height*0.56),
        (x_center+hw*0.52, y, z_top-height*0.42),
        (x_center+hw*0.52, y, z_top-height),
        (x_center-hw*0.52, y, z_top-height),
        (x_center-hw*0.52, y, z_top-height*0.42),
        (x_center-sh*0.92, y, z_top-height*0.56),
        (x_center-sh, y, z_top-height*0.34),
        (x_center-hw*0.56, y, z_top-height*0.16),
    ]
    # triangulated fan around a central chest point for a robust, readable silhouette
    c = (x_center, y, z_top - height * 0.46)
    verts.append(c)
    ci = len(verts) - 1
    faces = []
    for i in range(len(verts) - 1):
        faces.append((i, (i + 1) % (len(verts) - 1), ci))
    ob = add_mesh(name, verts, faces, mat, coll, smooth=False)
    return ob

def add_potted_plant(name, center, scale=1.0, leaf_mat=None, coll='阳台'):
    x, y, z = center
    pot_h = 0.26 * scale
    add_cone(name + '_盆', (x, y, z + pot_h / 2), 0.11 * scale, 0.16 * scale,
             pot_h, MATS['terracotta'], coll, vertices=14)
    add_cyl(name + '_土', (x, y, z + pot_h - 0.015), 0.145 * scale, 0.02,
            MATS['soil'], coll, vertices=14)
    leaf_mat = leaf_mat or MATS['leaf1']
    n = rand.randint(7, 13)
    for k in range(n):
        ang = rand.uniform(0, math.tau)
        tilt = rand.uniform(0.45, 1.1)
        length = rand.uniform(0.22, 0.45) * scale
        w = rand.uniform(0.035, 0.07) * scale
        base = Vector((x, y, z + pot_h - 0.01))
        direction = Vector((math.cos(ang) * math.sin(tilt),
                            math.sin(ang) * math.sin(tilt),
                            math.cos(tilt)))
        side = Vector((-math.sin(ang), math.cos(ang), 0)) * w
        p0 = base
        p1 = base + direction * length * 0.45 + side * 0.6
        p2 = base + direction * length
        p3 = base + direction * length * 0.45 - side * 0.6
        verts = [tuple(p0), tuple(p1), tuple(p2), tuple(p3)]
        ob = add_mesh(name + f'_叶{k}', verts, [(0, 1, 2, 3)], leaf_mat, coll)
        ob.data.materials.clear()
        ob.data.materials.append(leaf_mat)

def make_grille(name, x0, x1, z0, z1, y, spacing=0.15, bar=0.018,
                mat=None, with_frame=True, coll='阳台'):
    mat = mat or MATS['metal_gray']
    boxes = []
    n = max(1, int((x1 - x0) / spacing))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        boxes.append(((x, y, (z0 + z1) / 2), (bar, bar, z1 - z0)))
    if with_frame:
        boxes.append(((x0, y, z0), (bar * 1.8, bar * 1.8, bar * 2)))
        boxes.append(((x0, y, z1), (bar * 1.8, bar * 1.8, bar * 2)))
        boxes.append((((x0 + x1) / 2, y, z0), (x1 - x0, bar * 1.5, bar)))
        boxes.append((((x0 + x1) / 2, y, z1), (x1 - x0, bar * 1.5, bar)))
        boxes.append(((x0, y, (z0 + z1) / 2), (bar * 1.5, bar * 1.5, z1 - z0)))
        boxes.append(((x1, y, (z0 + z1) / 2), (bar * 1.5, bar * 1.5, z1 - z0)))
    return add_boxes(name, boxes, mat, coll)

def add_ac_unit(name, x, y, z, rot_z=0.0, body_mat=None, scale=1.0, coll='立面设备'):
    """A reasonably detailed split AC outdoor unit, facing -Y before rotation."""
    body_mat = body_mat or MATS['ac_white']
    s = scale
    # a parent empty makes rotation trivial
    empty = bpy.data.objects.new(name, None)
    C(coll).objects.link(empty)
    empty.location = (x, y, z)
    empty.rotation_euler = (0, 0, rot_z)

    def local_box(n, c, sz, m):
        ob = add_box(n, (0, 0, 0), sz, m, coll)
        ob.parent = empty
        ob.location = c
        return ob
    local_box(name + '_机身', (0, 0, 0), (0.86 * s, 0.34 * s, 0.62 * s), body_mat)
    # fan recess and hub
    fan = add_cyl(name + '_风扇', (0.18 * s, -0.176 * s, 0), 0.225 * s, 0.02,
                  MATS['ac_dark'], coll, vertices=28, rot=(math.pi / 2, 0, 0))
    fan.parent = empty
    fan.location = (0.18 * s, -0.176 * s, 0)
    hub = add_cyl(name + '_轴', (0.18 * s, -0.191 * s, 0), 0.045 * s, 0.025,
                  MATS['metal_gray'], coll, vertices=16, rot=(math.pi / 2, 0, 0))
    hub.parent = empty
    hub.location = (0.18 * s, -0.191 * s, 0)
    # fan blades (simple, catches light)
    for k in range(5):
        ang = k * math.tau / 5
        b = add_box(name + f'_叶片{k}', (0, 0, 0), (0.17 * s, 0.01, 0.05 * s),
                    MATS['metal_gray'], coll)
        b.parent = empty
        b.location = (0.18 * s + math.cos(ang) * 0.09 * s,
                      -0.198 * s,
                      math.sin(ang) * 0.09 * s)
        b.rotation_euler = (0, ang, 0)
    # right-hand louver stack
    boxes = []
    for k in range(9):
        zz = -0.24 * s + k * 0.06 * s
        boxes.append(((0.33 * s, -0.185 * s, zz), (0.18 * s, 0.012, 0.018 * s)))
    add_boxes(name + '_格栅', boxes, MATS['ac_dark'], coll).parent = empty
    local_box(name + '_顶缝', (0, -0.02, 0.315 * s), (0.86 * s, 0.30 * s, 0.018), MATS['ac_gray'] if 'ac_gray' in MATS else MATS['ac_white'])
    for sx in (-0.32, 0.32):
        local_box(name + '_脚', (sx * s, -0.02, -0.33 * s), (0.10 * s, 0.24 * s, 0.05), MATS['rust'])
    # L brackets
    for sx in (-0.33, 0.33):
        local_box(name + '_架', (sx * s, 0.2 * s, -0.34 * s), (0.05 * s, 0.36 * s, 0.05), MATS['rust'])
        local_box(name + '_架2', (sx * s, 0.34 * s, -0.16 * s), (0.05 * s, 0.05, 0.38 * s), MATS['rust'])
    # short insulated refrigerant line in the wall direction
    pts = [(x + 0.38 * s * math.cos(rot_z), y + 0.2 * s * math.sin(rot_z), z - 0.2 * s),
           (x + 0.55 * s * math.cos(rot_z), y + 0.3 * s * math.sin(rot_z), z - 0.32 * s),
           (x + 0.58 * s * math.cos(rot_z), y + 0.4 * s * math.sin(rot_z), z - 0.55 * s)]
    add_curve(name + '_铜管', pts, 0.018, MATS['pipe_gray'], coll, resolution=2)
    return empty

# ---------------------------------------------------------------------------
# shell and facade
# ---------------------------------------------------------------------------
def build_shell():
    M = MATS
    # ground floor structural shell (interiors are built separately)
    add_box('一层后墙', (0, 6.0, GROUND_H / 2), (36.0, 0.3, GROUND_H), M['wall_warm'], '建筑主体')
    add_box('一层左墙', (-17.88, 0.05, GROUND_H / 2), (0.24, 12.1, GROUND_H), M['wall_warm'], '建筑主体')
    add_box('一层右墙', (17.88, 0.05, GROUND_H / 2), (0.24, 12.1, GROUND_H), M['wall_warm'], '建筑主体')
    add_box('一层楼板', (0, 0.05, GROUND_H - 0.08), (36.0, 12.2, 0.16), M['concrete'], '建筑主体')
    add_box('一层地坪', (0, 0.05, 0.06), (35.6, 12.0, 0.12), M['concrete_dark'], '建筑主体')
    # mass behind the shop interiors, keeps the building opaque
    add_box('一层内部实体', (0, 0.9, GROUND_H / 2), (35.4, 9.9, GROUND_H - 0.18), M['dark'], '建筑主体')
    # upper volume
    add_box('住宅主体', (0, 0.15, GROUND_H + (ROOF - GROUND_H) / 2),
            (35.6, 11.7, ROOF - GROUND_H), M['wall'], '建筑主体')
    add_box('左侧山墙', (-17.9, 0.05, GROUND_H + (ROOF - GROUND_H) / 2),
            (0.2, 12.1, ROOF - GROUND_H), M['wall_warm'], '建筑主体')
    add_box('右侧山墙', (17.9, 0.05, GROUND_H + (ROOF - GROUND_H) / 2),
            (0.2, 12.1, ROOF - GROUND_H), M['wall_warm'], '建筑主体')
    add_box('背立面', (0, 6.02, GROUND_H + (ROOF - GROUND_H) / 2),
            (36.0, 0.14, ROOF - GROUND_H), M['wall_warm'], '建筑主体')
    # parapet, roof slab and coping
    add_box('女儿墙前', (0, -5.88, ROOF + 0.48), (36.0, 0.26, 0.96), M['wall'], '屋顶')
    add_box('女儿墙后', (0, 5.88, ROOF + 0.48), (36.0, 0.26, 0.96), M['wall'], '屋顶')
    add_box('女儿墙左', (-17.88, 0, ROOF + 0.48), (0.26, 12.0, 0.96), M['wall_warm'], '屋顶')
    add_box('女儿墙右', (17.88, 0, ROOF + 0.48), (0.26, 12.0, 0.96), M['wall_warm'], '屋顶')
    for n, c, s in [
        ('前压顶', (0, -5.88, ROOF + 0.99), (36.3, 0.4, 0.10)),
        ('后压顶', (0, 5.88, ROOF + 0.99), (36.3, 0.4, 0.10)),
        ('左压顶', (-17.88, 0, ROOF + 0.99), (0.4, 12.2, 0.10)),
        ('右压顶', (17.88, 0, ROOF + 0.99), (0.4, 12.2, 0.10)),
    ]:
        add_box(n, c, s, M['concrete'], '屋顶', bevel=0.02)
    add_box('屋面', (0, 0, ROOF + 0.05), (35.4, 11.6, 0.12), M['roof'], '屋顶')
    # simple roof access penthouses
    for i, x in enumerate((-15.6, 0.1, 15.6)):
        add_box(f'楼梯出屋面{i}', (x, -1.9, ROOF + 1.45), (3.3, 3.4, 2.8),
                M['wall_stair'], '屋顶')
        add_box(f'出屋面顶{i}', (x, -1.9, ROOF + 2.9), (3.6, 3.7, 0.16),
                M['concrete'], '屋顶', bevel=0.02)
        add_box(f'出屋面门{i}', (x, -3.62, ROOF + 1.2), (0.95, 0.08, 2.1),
                M['green_metal'], '屋顶')
        add_box(f'出屋面窗{i}', (x + 1.0, -3.63, ROOF + 1.8), (0.7, 0.04, 0.55),
                M['glass_frost'], '屋顶')
    # horizontal floor bands
    for f in range(NFLOORS + 1):
        z = GROUND_H + f * RES_H
        if f == NFLOORS:
            z = ROOF - 0.02
        add_box(f'楼层线{f}', (0, -5.83, z + 0.09), (36.02, 0.46, 0.18),
                M['concrete'], '立面构件')
        add_box(f'楼层线顶{f}', (0, -6.04, z + 0.18), (36.02, 0.12, 0.06),
                M['trim'], '立面构件')
    # vertical pilasters at the outer corners
    for x in (-17.78, 17.78):
        add_box('角柱' + ('左' if x < 0 else '右'), (x, -5.9, (GROUND_H + ROOF) / 2),
                (0.46, 0.30, ROOF - GROUND_H), M['wall_warm'], '立面构件')
        add_box('角柱线' + ('左' if x < 0 else '右'), (x - 0.22 if x < 0 else x + 0.22,
                -6.05, (GROUND_H + ROOF) / 2), (0.08, 0.12, ROOF - GROUND_H),
                M['concrete'], '立面构件')

def build_facade():
    M = MATS
    for f in range(NFLOORS):
        z0 = GROUND_H + f * RES_H
        for bi in range(9):
            x0, x1 = BAY_EDGES[bi], BAY_EDGES[bi + 1]
            cx = (x0 + x1) / 2
            if bi in STAIR_BAYS:
                _build_stair_bay(f, bi, z0, x0, x1, cx)
            else:
                _build_apartment_bay(f, bi, z0, x0, x1, cx)

def _wall_piece(name, cx, cz, w, h, y=-5.85, d=0.30, mat=None):
    return add_box(name, (cx, y, cz), (w, d, h), mat or MATS['wall'], '立面墙体')

def _build_stair_bay(f, bi, z0, x0, x1, cx):
    M = MATS
    # opening 1.50 x 1.95
    ow, oh = 1.52, 1.98
    oz_rel = 0.66
    oz = z0 + oz_rel
    side = ((x1 - x0) - ow) / 2
    _wall_piece(f'楼梯间墙L{bi}_{f}', x0 + side / 2, z0 + RES_H / 2, side, RES_H)
    _wall_piece(f'楼梯间墙R{bi}_{f}', x1 - side / 2, z0 + RES_H / 2, side, RES_H)
    _wall_piece(f'楼梯间墙下{bi}_{f}', cx, z0 + oz_rel / 2, ow, oz_rel)
    top_h = RES_H - oz_rel - oh
    _wall_piece(f'楼梯间墙上{bi}_{f}', cx, z0 + oz_rel + oh + top_h / 2,
                ow, top_h)
    # dark interior, then frame and glass
    add_plane(f'楼梯暗部{bi}_{f}', (cx, -5.69, z0 + 1.62), ow - 0.02, oh - 0.02,
              M['dark_warm'], '立面墙体', rot=(math.pi / 2, 0, 0))
    # aluminum frame, 2 x 3 grid
    yf = -5.93
    add_boxes(f'楼梯窗框{bi}_{f}', [
        ((cx, yf, oz + oh / 2), (ow + 0.08, 0.06, 0.06)),
        ((cx, yf, oz), (ow + 0.08, 0.06, 0.06)),
        ((cx, yf, oz + oh), (ow + 0.08, 0.06, 0.06)),
        ((cx - ow / 2, yf, oz + oh / 2), (0.055, 0.06, oh)),
        ((cx + ow / 2, yf, oz + oh / 2), (0.055, 0.06, oh)),
        ((cx, yf, oz + oh * 0.5), (0.045, 0.05, oh)),
        ((cx, yf, oz + oh * 0.5), (ow, 0.05, 0.045)),
    ], M['aluminum'], '立面门窗')
    # panes
    for ix in range(2):
        for iz in range(2):
            gx = cx - ow / 4 + ix * ow / 2
            gz = oz + oh / 4 + iz * oh / 2
            add_plane(f'楼梯玻璃{bi}_{f}_{ix}{iz}', (gx, -5.945, gz),
                      ow / 2 - 0.05, oh / 2 - 0.05, M['glass_frost'],
                      '立面门窗', rot=(math.pi / 2, 0, 0))
    # exterior security grille, a little in front of the wall
    make_grille(f'楼梯防盗网{bi}_{f}', cx - ow / 2 - 0.05, cx + ow / 2 + 0.05,
                oz - 0.02, oz + oh + 0.02, -6.07, spacing=0.16, bar=0.016,
                mat=M['metal_gray'], coll='防盗网')
    # protruding sill
    add_box(f'楼梯窗台{bi}_{f}', (cx, -6.08, oz - 0.06), (ow + 0.35, 0.3, 0.10),
            M['concrete'], '立面构件', bevel=0.015)
    # small painted floor plaque beside stair window
    fy = z0 + 2.72
    add_box(f'楼层牌{bi}_{f}', (cx + 0.95, -6.09, fy), (0.32, 0.03, 0.2),
            M['white_paint'], '标识')
    add_text(f'楼层字{bi}_{f}', f'{f + 2}', (cx + 0.95, -6.112, fy - 0.005),
             0.12, M['ink'], '标识', font=FONT_BOLD, rot=(math.pi / 2, 0, 0))

def _build_apartment_bay(f, bi, z0, x0, x1, cx):
    M = MATS
    ow = 3.04
    oz_rel = 0.20
    oh = 2.46
    oz = z0 + oz_rel
    side = ((x1 - x0) - ow) / 2
    _wall_piece(f'住宅墙L{bi}_{f}', x0 + side / 2, z0 + RES_H / 2, side, RES_H)
    _wall_piece(f'住宅墙R{bi}_{f}', x1 - side / 2, z0 + RES_H / 2, side, RES_H)
    top_h = RES_H - oz_rel - oh
    _wall_piece(f'住宅墙上{bi}_{f}', cx, z0 + oz_rel + oh + top_h / 2, ow, top_h)
    _wall_piece(f'住宅墙下{bi}_{f}', cx, z0 + oz_rel / 2, ow, oz_rel)
    # a shallow reveal and the dark room behind the sliding door
    add_plane(f'室内暗部{bi}_{f}', (cx, -5.69, z0 + 1.45), ow - 0.02, oh - 0.02,
              M['dark_warm'] if rand.random() < 0.28 else M['dark'],
              '立面墙体', rot=(math.pi / 2, 0, 0))
    # reveal jambs
    for sx in (-1, 1):
        add_box(f'门洞侧板{bi}_{f}_{sx}', (cx + sx * (ow / 2 - 0.025), -5.84, oz + oh / 2),
                (0.05, 0.32, oh), M['trim_gray'], '立面门窗')
    add_box(f'门洞上板{bi}_{f}', (cx, -5.84, oz + oh - 0.025), (ow, 0.32, 0.05),
            M['trim_gray'], '立面门窗')

def build_balconies():
    M = MATS
    enclosed_map = {
        1: ['enclosed', 'open', 'open', 'enclosed', 'open', 'open'],
        2: ['enclosed', 'enclosed', 'open', 'enclosed', 'enclosed', 'open'],
        3: ['open', 'open', 'enclosed', 'open', 'open', 'enclosed'],
        5: ['enclosed', 'open', 'enclosed', 'open', 'enclosed', 'open'],
        6: ['open', 'open', 'open', 'enclosed', 'open', 'open'],
        7: ['enclosed', 'enclosed', 'open', 'enclosed', 'enclosed', 'enclosed'],
    }
    rail_mats = [M['railing'], M['railing_green'], M['railing_blue'], M['railing']]
    for f in range(NFLOORS):
        z0 = GROUND_H + f * RES_H
        for bi in APT_BAYS:
            x0, x1 = BAY_EDGES[bi], BAY_EDGES[bi + 1]
            cx = (x0 + x1) / 2
            style = enclosed_map[bi][f]
            _build_balcony(f, bi, z0, x0, x1, cx, style,
                           rail_mats[(bi + f) % len(rail_mats)])

def _build_balcony(f, bi, z0, x0, x1, cx, style, rail_mat):
    M = MATS
    y_outer = -7.35
    # slab
    add_box(f'阳台板{bi}_{f}', (cx, -6.66, z0 + 0.10), (3.50, 1.42, 0.20),
            M['concrete'], '阳台', bevel=0.012)
    add_box(f'阳台面层{bi}_{f}', (cx, -6.66, z0 + 0.205), (3.38, 1.30, 0.025),
            M['concrete_dark'], '阳台')
    # side fins
    for sx in (-1, 1):
        add_box(f'阳台隔板{bi}_{f}_{sx}', (cx + sx * 1.72, -6.67, z0 + 1.50),
                (0.07, 1.36, 2.60), M['wall'], '阳台')
    # subtle drip stain under slab
    # top canopy for the highest floor
    if f == NFLOORS - 1:
        add_box(f'阳台雨棚{bi}_{f}', (cx, -6.67, z0 + 2.92), (3.54, 1.46, 0.16),
                M['concrete'], '阳台', bevel=0.02)
    # rear sliding door and curtains
    _balcony_door(f, bi, cx, z0)
    if style == 'open':
        _open_balcony(f, bi, z0, x0, x1, cx, y_outer, rail_mat)
    else:
        _enclosed_balcony(f, bi, z0, x0, x1, cx, y_outer)
    # occasional security cage on the outside
    if rand.random() < 0.34:
        make_grille(f'阳台外防盗网{bi}_{f}', x0 + 0.24, x1 - 0.24, z0 + 0.28,
                    z0 + 2.68, y_outer - 0.18, spacing=0.19, bar=0.018,
                    mat=M['metal_gray'], coll='防盗网')
        for sx in (-1, 1):
            add_box(f'防盗网侧{bi}_{f}_{sx}', (x0 + 0.24 if sx < 0 else x1 - 0.24,
                    y_outer - 0.09, z0 + 1.48), (0.018, 0.18, 2.4),
                    M['metal_gray'], '防盗网')
    # AC unit in about a third of the balconies
    if rand.random() < 0.42:
        acm = [M['ac_white'], M['ac_beige'], M['ac_gray']][rand.randrange(3)]
        add_ac_unit(f'空调{bi}_{f}', cx + 1.05, -7.05, z0 + 0.47,
                    rot_z=rand.uniform(-0.03, 0.03), body_mat=acm,
                    scale=rand.uniform(0.93, 1.04), coll='立面设备')
    # plants, clutter, laundry
    if style == 'open':
        _balcony_props(f, bi, z0, x0, x1, cx)
    else:
        if rand.random() < 0.55:
            px = x0 + rand.choice([0.55, 2.9])
            add_potted_plant(f'阳台盆花{bi}_{f}', (px, -6.48, z0 + 0.22),
                             rand.uniform(0.75, 1.05),
                             [M['leaf1'], M['leaf2'], M['leaf3']][rand.randrange(3)])
    # a few hanging red lanterns / wind chimes for character
    if rand.random() < 0.10:
        lx = cx + rand.uniform(-1.0, 1.0)
        add_uvsphere(f'阳台灯笼{bi}_{f}', (lx, y_outer + 0.15, z0 + 2.35),
                     0.13, M['red_banner'], '阳台', segments=16, rings=10)
        add_cyl(f'灯笼穗{bi}_{f}', (lx, y_outer + 0.15, z0 + 2.16), 0.01, 0.16,
                M['gold'], '阳台', vertices=6)

def _balcony_door(f, bi, cx, z0):
    M = MATS
    y = -5.96
    width, height = 3.0, 2.42
    z = z0 + 0.22
    # white aluminum outer frame
    add_boxes(f'阳台门框{bi}_{f}', [
        ((cx, y, z + height / 2), (width, 0.08, 0.06)),
        ((cx, y, z), (width, 0.08, 0.06)),
        ((cx - width / 2, y, z + height / 2), (0.06, 0.08, height)),
        ((cx + width / 2, y, z + height / 2), (0.06, 0.08, height)),
        ((cx - width / 6, y, z + height / 2), (0.045, 0.07, height)),
        ((cx + width / 6, y, z + height / 2), (0.045, 0.07, height)),
        ((cx, y, z + height * 0.52), (width, 0.06, 0.045)),
    ], M['aluminum'], '立面门窗')
    # dark gap / glass panes
    for k in range(3):
        add_plane(f'阳台门玻璃{bi}_{f}_{k}', (cx - width / 3 + k * width / 3,
                  y + 0.005, z + height * 0.55), width / 3 - 0.075,
                  height * 0.83, M['glass'], '立面门窗', rot=(math.pi / 2, 0, 0))
    # curtains, mostly drawn to the sides
    curtain_mats = [M['curtain_cream'], M['curtain_pink'], M['curtain_blue'],
                    M['curtain_green'], M['curtain_white'], M['curtain_white']]
    cm = curtain_mats[rand.randrange(len(curtain_mats))]
    for sx in (-1, 1):
        if rand.random() < 0.82:
            w = rand.uniform(0.55, 0.95)
            ccx = cx + sx * (width / 2 - w / 2 - 0.04)
            cloth_panel(f'窗帘{bi}_{f}_{sx}', ccx, -5.72, z0 + 2.55, w,
                        rand.uniform(1.75, 2.30), cm, folds=6, amp=0.025,
                        coll='室内软装')
    # a half-open curtain in some rooms
    if rand.random() < 0.28:
        cloth_panel(f'纱帘{bi}_{f}', cx, -5.74, z0 + 2.55, 2.7,
                    rand.uniform(1.3, 2.1), M['curtain_white'], folds=12,
                    amp=0.018, coll='室内软装')

def _open_balcony(f, bi, z0, x0, x1, cx, y_outer, rail_mat):
    M = MATS
    # low curb
    add_box(f'阳台矮墙{bi}_{f}', (cx, y_outer, z0 + 0.28), (3.50, 0.12, 0.28),
            M['concrete'], '阳台', bevel=0.012)
    z_rail0, z_rail1 = z0 + 0.32, z0 + 1.25
    boxes = []
    n = 22
    for i in range(n + 1):
        x = x0 + 0.18 + (x1 - x0 - 0.36) * i / n
        boxes.append(((x, y_outer, (z_rail0 + z_rail1) / 2),
                      (0.022, 0.022, z_rail1 - z_rail0)))
    add_boxes(f'阳台栏杆{bi}_{f}', boxes, rail_mat, '阳台')
    add_boxes(f'阳台栏杆横{bi}_{f}', [
        ((cx, y_outer, z_rail1), (3.22, 0.045, 0.045)),
        ((cx, y_outer, z_rail0 + 0.05), (3.22, 0.035, 0.035)),
        ((cx, y_outer, z0 + 0.86), (3.22, 0.025, 0.025)),
    ], rail_mat, '阳台')
    # drying pole and clothes line
    pole_z = z0 + 2.52
    add_cyl(f'晾衣杆{bi}_{f}', (cx, -6.75, pole_z), 0.018, 3.1,
            M['metal_gray'], '阳台', vertices=8, rot=(0, math.pi / 2, 0))
    if rand.random() < 0.72:
        line_z = z0 + 2.34
        add_curve(f'晾衣绳{bi}_{f}', catenary((x0 + 0.25, -6.9, line_z),
                  (x1 - 0.25, -6.9, line_z), sag=0.06, n=10), 0.006,
                  M['pipe_gray'], '阳台')
        _laundry_on_line(f, bi, z0, x0, x1, -6.9, line_z)

def _laundry_on_line(f, bi, z0, x0, x1, y, line_z):
    M = MATS
    cloth_mats = [M['cloth_red'], M['cloth_blue'], M['cloth_yellow'],
                  M['cloth_white'], M['cloth_pink'], M['cloth_green'],
                  M['cloth_gray'], M['cloth_plaid']]
    n_items = rand.randint(2, 4)
    slots = [0.24, 0.42, 0.58, 0.76]
    rand.shuffle(slots)
    for k in range(n_items):
        t = slots[k]
        x = x0 + (x1 - x0) * t
        kind = rand.random()
        mat = cloth_mats[rand.randrange(len(cloth_mats))]
        if kind < 0.28:
            shirt(f'晾晒上衣{bi}_{f}_{k}', x, y, line_z - 0.02,
                  rand.uniform(0.52, 0.72), rand.uniform(0.55, 0.75), mat)
        elif kind < 0.46:
            cloth_panel(f'晾晒 towels{bi}_{f}_{k}', x, y + 0.01, line_z - 0.02,
                        rand.uniform(0.38, 0.62), rand.uniform(0.45, 0.8),
                        mat, folds=5, amp=0.025)
        elif kind < 0.65:
            # trousers made of two narrow hanging panels
            for leg in (-1, 1):
                cloth_panel(f'晾晒裤{bi}_{f}_{k}_{leg}', x + leg * 0.1,
                            y + 0.005, line_z - 0.02, 0.16,
                            rand.uniform(0.65, 0.95), mat, folds=3, amp=0.012)
        else:
            cloth_panel(f'晾晒床单{bi}_{f}_{k}', x, y + 0.02, line_z - 0.02,
                        rand.uniform(0.85, 1.15), rand.uniform(0.9, 1.35),
                        mat, folds=9, amp=0.045)

def _enclosed_balcony(f, bi, z0, x0, x1, cx, y_outer):
    M = MATS
    y = y_outer
    z_bot, z_top = z0 + 0.23, z0 + 2.70
    frame_mat = M['aluminum'] if (bi + f) % 3 else M['aluminum_dark']
    # lower opaque panel
    add_box(f'封闭阳台下板{bi}_{f}', (cx, y, z0 + 0.63), (3.46, 0.08, 0.80),
            M['white_metal'] if frame_mat == M['aluminum'] else M['aluminum_dark'],
            '阳台', bevel=0.008)
    add_boxes(f'封闭阳台框{bi}_{f}', [
        ((cx, y, z_top), (3.50, 0.075, 0.06)),
        ((cx, y, z_bot), (3.50, 0.075, 0.06)),
        ((cx, y, z0 + 1.10), (3.50, 0.075, 0.05)),
        ((cx, y, z0 + 1.88), (3.50, 0.075, 0.05)),
        ((x0 + 0.18, y, (z_bot + z_top) / 2), (0.06, 0.075, z_top - z_bot)),
        ((x1 - 0.18, y, (z_bot + z_top) / 2), (0.06, 0.075, z_top - z_bot)),
        ((cx, y, (z_bot + z_top) / 2), (0.055, 0.075, z_top - z_bot)),
        ((cx - 1.15, y, (z_bot + z_top) / 2), (0.05, 0.075, z_top - z_bot)),
        ((cx + 1.15, y, (z_bot + z_top) / 2), (0.05, 0.075, z_top - z_bot)),
    ], frame_mat, '阳台')
    for k in range(4):
        px = x0 + 0.18 + (x1 - x0 - 0.36) * (k + 0.5) / 4
        add_plane(f'封闭阳台玻璃{bi}_{f}_{k}', (px, y - 0.045,
                  (z_bot + z_top) / 2), (x1 - x0 - 0.36) / 4 - 0.06,
                  z_top - z_bot - 0.06, M['glass_green'], '阳台',
                  rot=(math.pi / 2, 0, 0))
    # horizontal opening gap for one sliding sash
    if rand.random() < 0.36:
        px = cx + 0.58
        add_box(f'半开窗缝{bi}_{f}', (px, y - 0.05, z0 + 1.48),
                (1.1, 0.02, 0.64), M['dark'], '阳台')

def _balcony_props(f, bi, z0, x0, x1, cx):
    M = MATS
    # plants
    for k in range(rand.randint(1, 3)):
        px = x0 + rand.uniform(0.35, 3.55)
        py = -6.42 - rand.uniform(0.0, 0.5)
        add_potted_plant(f'阳台植物{bi}_{f}_{k}', (px, py, z0 + 0.215),
                         rand.uniform(0.7, 1.25),
                         [M['leaf1'], M['leaf2'], M['leaf3'], M['leaf_dark']][rand.randrange(4)])
    # mop and bucket
    if rand.random() < 0.28:
        mx = x0 + rand.uniform(0.4, 0.8)
        add_cyl(f'拖把桶{bi}_{f}', (mx, -6.55, z0 + 0.34), 0.16, 0.27,
                M['blue_paint'], '阳台', vertices=14)
        add_cyl(f'拖把杆{bi}_{f}', (mx + 0.08, -6.55, z0 + 0.95), 0.018, 1.25,
                M['wood'], '阳台', vertices=8, rot=(0.15, 0.1, 0))
    # a folding stool
    if rand.random() < 0.18:
        sx = x0 + rand.uniform(0.45, 1.0)
        add_box(f'小凳{bi}_{f}', (sx, -6.4, z0 + 0.46), (0.32, 0.3, 0.04),
                M['wood'], '阳台', bevel=0.01)
        for dx, dy in ((-0.12, -0.1), (0.12, -0.1), (-0.12, 0.1), (0.12, 0.1)):
            add_box(f'凳腿{bi}_{f}_{dx}{dy}', (sx + dx, -6.4 + dy, z0 + 0.33),
                    (0.03, 0.03, 0.3), M['wood'], '阳台')
    # hanging mop / cleaning tools
    if rand.random() < 0.15:
        add_curve(f'挂绳{bi}_{f}', [(cx + 1.5, -6.55, z0 + 2.55),
                  (cx + 1.5, -6.55, z0 + 2.05)], 0.005, M['pipe_gray'], '阳台')
    # a small red plastic basin
    if rand.random() < 0.14:
        add_cone(f'红盆{bi}_{f}', (x0 + 0.55, -6.3, z0 + 0.29), 0.16, 0.20,
                 0.14, M['red_paint'], '阳台', vertices=16)

# ---------------------------------------------------------------------------
# side wall, pipes, posters
# ---------------------------------------------------------------------------
def build_side_details():
    M = MATS
    # right side is visible from the camera
    for f in range(NFLOORS):
        z0 = GROUND_H + f * RES_H
        for k, y in enumerate((-3.4, 0.4, 4.0)):
            w, h = (0.68, 0.88) if k != 1 else (0.95, 1.2)
            zc = z0 + 1.55
            add_box(f'侧窗洞{f}_{k}', (18.015, y, zc), (0.03, w, h),
                    M['dark'], '侧面细节')
            add_box(f'侧窗框{f}_{k}', (18.04, y, zc), (0.06, w + 0.08, h + 0.08),
                    M['aluminum'], '侧面细节')
            add_plane(f'侧窗玻璃{f}_{k}', (18.07, y, zc), w - 0.05, h - 0.05,
                      M['glass_frost'], '侧面细节', rot=(math.pi / 2, 0, math.pi / 2))
            make_grille(f'侧窗网{f}_{k}', y - w / 2, y + w / 2, zc - h / 2,
                        zc + h / 2, 18.10, spacing=0.13, bar=0.014,
                        mat=M['metal_gray'], coll='防盗网')
            add_box(f'侧窗台{f}_{k}', (18.08, y, zc - h / 2 - 0.04),
                    (0.2, w + 0.22, 0.07), M['concrete'], '侧面细节', bevel=0.01)
    # side downpipes with brackets
    for y in (-4.7, 1.8, 5.3):
        add_cyl(f'侧落水管{y}', (18.09, y, (0.2 + ROOF) / 2), 0.055, ROOF - 0.2,
                M['pipe'], '侧面细节', vertices=10)
        for z in (2.0, 5.0, 8.0, 11.0, 14.0, 17.0, 20.5):
            add_box(f'侧管卡{y}_{z}', (18.06, y, z), (0.12, 0.12, 0.08),
                    M['pipe_gray'], '侧面细节')
        add_curve(f'侧管弯{y}', [(18.09, y, 0.22), (18.14, y + 0.12, 0.13),
                  (18.18, y + 0.2, 0.035)], 0.055, M['pipe'], '侧面细节')
    # side AC units, rotated to face +X
    for k, (y, f) in enumerate([(-2.2, 1), (2.0, 3), (4.6, 5), (-4.0, 4)]):
        add_ac_unit(f'侧空调{k}', 18.35, y, GROUND_H + f * RES_H + 0.9,
                    rot_z=-math.pi / 2, body_mat=M['ac_white'], scale=0.95,
                    coll='立面设备')
    # big painted building number on the side wall
    add_box('侧面楼号底', (18.02, -1.6, 16.4), (0.03, 3.0, 3.2),
            M['white_paint'], '标识')
    add_text('侧面楼号', '3', (18.055, -1.6, 16.4), 2.5, M['red_paint'],
             '标识', rot=(math.pi / 2, 0, math.pi / 2), font=FONT_BOLD)
    add_text('侧面楼名', '幸福里', (18.055, -1.6, 14.0), 0.42, M['red_paint'],
             '标识', rot=(math.pi / 2, 0, math.pi / 2), font=FONT_SANS)
    add_text('侧面楼名2', '3 号 楼', (18.05, -1.6, 13.5), 0.28, M['ink'],
             '标识', rot=(math.pi / 2, 0, math.pi / 2), font=FONT_SANS)
    # side satellite dish
    _satellite_dish('侧面卫星锅', (18.6, 3.5, 9.5), 0.55, rot_z=-1.2)
    # small ventilation grilles near the ground
    for y in (-2.8, 2.8):
        add_box(f'侧通风口{y}', (18.03, y, 3.2), (0.05, 0.45, 0.35),
                M['dark'], '侧面细节')
        for i in range(5):
            add_box(f'侧通风条{y}_{i}', (18.06, y, 3.04 + i * 0.07),
                    (0.02, 0.4, 0.015), M['metal_gray'], '侧面细节')

# ---------------------------------------------------------------------------
# roof details
# ---------------------------------------------------------------------------
def build_roof():
    M = MATS
    # waterproofing patches on the roof
    for i in range(10):
        x = rand.uniform(-16, 16)
        y = rand.uniform(-4.8, 4.8)
        w = rand.uniform(1.0, 3.2)
        h = rand.uniform(0.6, 2.2)
        add_box(f'屋面补丁{i}', (x, y, ROOF + 0.115), (w, h, 0.014),
                M['roof_patch'], '屋顶', rot=(0, 0, rand.uniform(-0.2, 0.2)))
    # concrete bases for equipment
    for i, x in enumerate((-9.8, -5.8, 2.4, 7.6, 12.0)):
        y = rand.uniform(2.2, 4.0)
        _solar_heater(f'太阳能{i}', (x, y, ROOF + 0.12), rand.uniform(-0.08, 0.08))
    # water tanks
    for i, (x, y, r) in enumerate([(-13.4, 2.0, 0.55), (11.6, 3.9, 0.6), (5.7, 4.6, 0.45)]):
        add_box(f'水箱基座{i}', (x, y, ROOF + 0.25), (1.4, 1.4, 0.3),
                M['concrete'], '屋顶')
        add_cyl(f'水箱{i}', (x, y, ROOF + 0.95), r, 1.2,
                M['tank_blue'], '屋顶', vertices=24)
        add_cyl(f'水箱盖{i}', (x, y, ROOF + 1.58), r * 0.92, 0.08,
                M['water_blue'], '屋顶', vertices=24)
        add_cyl(f'水箱箍{i}', (x, y, ROOF + 0.76), r + 0.012, 0.045,
                M['metal_gray'], '屋顶', vertices=24)
    # antennas
    for i, (x, y) in enumerate([(-3.4, 4.2), (6.9, 3.2), (14.0, 2.5), (-14.2, 3.1)]):
        _tv_antenna(f'天线{i}', (x, y, ROOF + 0.12), rand.uniform(3.2, 5.8))
    # dishes
    _satellite_dish('屋顶卫星锅1', (-11.5, 0.9, ROOF + 0.25), 0.75, rot_z=0.8)
    _satellite_dish('屋顶卫星锅2', (9.0, 1.6, ROOF + 0.25), 0.58, rot_z=-0.4)
    # vents and pipes
    for i, (x, y) in enumerate([(-7.1, -2.2), (3.0, -1.3), (13.0, -3.0), (-2.1, 4.8)]):
        add_cyl(f'屋顶通气管{i}', (x, y, ROOF + 0.6), 0.09, 1.0,
                M['pipe_gray'], '屋顶', vertices=12)
        add_cyl(f'屋顶通气帽{i}', (x, y, ROOF + 1.12), 0.22, 0.12,
                M['metal_gray'], '屋顶', vertices=16)
    # laundry line across the roof
    add_cyl('屋顶晾衣杆1', (-6.6, -4.6, ROOF + 1.9), 0.03, 3.4,
            M['metal_gray'], '屋顶', vertices=8, rot=(0, math.pi / 2, 0))
    for sy in (-0.9, 0.9):
        add_cyl(f'屋顶衣杆立柱{sy}', (-6.6, -4.6 + sy, ROOF + 0.95), 0.022, 1.9,
                M['metal_gray'], '屋顶', vertices=8)
    add_curve('屋顶晾衣绳', catenary((-8.2, -3.7, ROOF + 1.88),
              (-5.0, -3.7, ROOF + 1.88), sag=0.05, n=10), 0.006,
              M['pipe_gray'], '屋顶')
    for j, (x, mat) in enumerate([(-7.6, M['cloth_white']), (-6.9, M['cloth_blue']),
                                  (-6.0, M['cloth_pink'])]):
        cloth_panel(f'屋顶晾布{j}', x, -3.7, ROOF + 1.82,
                    rand.uniform(0.6, 0.9), rand.uniform(0.8, 1.25), mat,
                    folds=7, amp=0.04, coll='屋顶')
    # scattered bricks, cable spool, bucket, broken tiles
    for i in range(8):
        x, y = rand.uniform(-16, 16), rand.uniform(-4.0, 4.0)
        add_box(f'屋顶砖{i}', (x, y, ROOF + 0.17), (0.24, 0.12, 0.07),
                M['brick'], '屋顶', rot=(0, 0, rand.uniform(0, 3.14)))
    add_cyl('屋顶线轴', (-2.0, 3.7, ROOF + 0.45), 0.42, 0.55,
            M['wood'], '屋顶', vertices=18, rot=(math.pi / 2, 0, 0))
    # pigeon cage with a tiny silhouette
    add_box('鸽笼底', (14.0, -3.2, ROOF + 0.45), (0.9, 0.7, 0.1), M['wood'], '屋顶')
    for sx in (-0.4, 0.4):
        for sy in (-0.3, 0.3):
            add_box(f'鸽笼柱{sx}{sy}', (14.0 + sx, -3.2 + sy, ROOF + 0.9),
                    (0.04, 0.04, 0.8), M['wood'], '屋顶')
    make_grille('鸽笼网', 13.58, 14.42, ROOF + 0.54, ROOF + 1.25, -3.53,
                spacing=0.12, bar=0.008, mat=M['metal_gray'], coll='屋顶')
    add_box('鸽笼顶', (14.0, -3.2, ROOF + 1.32), (1.0, 0.8, 0.04), M['wood'], '屋顶')

def _solar_heater(name, loc, rot_z=0.0):
    M = MATS
    x, y, z = loc
    theta = math.radians(34)
    # base frame
    add_box(name + '_基座', (x, y, z + 0.08), (2.05, 1.65, 0.16), M['concrete'], '屋顶')
    # tilted glazed panel, rises toward +Y
    length = 1.55
    cx, cy = x, y + math.cos(theta) * length / 2
    cz = z + 0.28 + math.sin(theta) * length / 2
    panel = add_box(name + '_集热板', (cx, cy, cz), (1.78, length, 0.06),
                    M['solar_glass'], '屋顶', rot=(theta, 0, 0))
    # metal border
    add_box(name + '_边框', (cx, cy, cz + 0.035), (1.86, length + 0.08, 0.035),
            M['solar_frame'], '屋顶', rot=(theta, 0, 0))
    # vacuum tubes running down the incline
    for i in range(13):
        tx = x - 0.80 + i * 1.6 / 12
        p0 = Vector((tx, y - 0.18, z + 0.29))
        p1 = Vector((tx, y + math.cos(theta) * length - 0.18,
                     z + 0.29 + math.sin(theta) * length))
        tube_between(name + f'_管{i}', p0, p1, 0.036, M['solar_glass'], '屋顶', vertices=8)
    # tank
    add_cyl(name + '_水箱', (x, y + math.cos(theta) * length + 0.1,
            z + 0.29 + math.sin(theta) * length + 0.12), 0.17, 1.95,
            M['tank_blue'], '屋顶', vertices=20, rot=(0, math.pi / 2, 0))
    # legs
    for sx in (-0.8, 0.8):
        for dy in (-0.55, 0.55):
            add_box(name + f'_腿{sx}{dy}', (x + sx, y + dy, z + 0.35),
                    (0.05, 0.05, 0.65), M['solar_frame'], '屋顶')

def _tv_antenna(name, loc, height):
    M = MATS
    x, y, z = loc
    add_cyl(name + '_杆', (x, y, z + height / 2), 0.035, height,
            M['metal_gray'], '屋顶', vertices=8)
    for i in range(6):
        hz = z + height - 0.15 - i * 0.32
        w = 1.15 - i * 0.12
        add_cyl(name + f'_横{i}', (x, y, hz), 0.012, w, M['metal_gray'], '屋顶',
                vertices=6, rot=(0, math.pi / 2, 0))
    for i in range(4):
        hz = z + height - 0.3 - i * 0.45
        add_box(name + f'_引向{i}', (x, y + 0.25, hz), (0.015, 0.5, 0.015),
                M['metal_gray'], '屋顶')
    add_curve(name + '_馈线', [(x, y, z + 0.1), (x + 0.4, y + 0.5, z + 0.05),
              (x + 0.8, y + 0.8, z + 0.02)], 0.008, M['black_paint'], '屋顶')

def _satellite_dish(name, loc, radius, rot_z=0.0):
    M = MATS
    x, y, z = loc
    n_r, n_a = 7, 18
    verts = []
    # dish in local XZ plane, concave toward -Y
    for ir in range(n_r + 1):
        r = radius * ir / n_r
        for ia in range(n_a):
            a = math.tau * ia / n_a
            px = r * math.cos(a)
            pz = r * math.sin(a)
            py = 0.32 * (r / radius) ** 2
            # rotate around Z for placement
            wx = x + px * math.cos(rot_z) - py * math.sin(rot_z)
            wy = y + px * math.sin(rot_z) + py * math.cos(rot_z)
            verts.append((wx, wy, z + pz))
    faces = []
    for ir in range(n_r):
        for ia in range(n_a):
            a = ir * n_a + ia
            b = ir * n_a + (ia + 1) % n_a
            c = (ir + 1) * n_a + (ia + 1) % n_a
            d = (ir + 1) * n_a + ia
            faces.append((a, b, c, d))
    add_mesh(name + '_面', verts, faces, M['white_metal'], '屋顶', smooth=True)
    # feed arm
    p0 = (x, y, z)
    p1 = (x - math.sin(rot_z) * 0.55, y + math.cos(rot_z) * 0.55, z + 0.03)
    tube_between(name + '_馈源杆', p0, p1, 0.018, M['metal_gray'], '屋顶')
    add_uvsphere(name + '_馈源', p1, 0.06, M['metal_gray'], '屋顶', segments=10, rings=6)
    add_cyl(name + '_支架', (x, y, z - 0.25), 0.04, 0.5, M['metal_gray'], '屋顶', vertices=8)
