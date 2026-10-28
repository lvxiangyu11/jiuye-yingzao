# -*- coding: utf-8 -*-
"""Ground floor: neighbourhood shops, stair entrances, signage and street-level clutter."""
import bpy
import math
import random
from mathutils import Vector
from scene_lib import *
import parts_building as B

M = {}
rand = random.Random(8417)

# x ranges of the ground-floor modules
STAIRS = [
    dict(center=-15.6, width=2.8, no='1', name='一单元'),
    dict(center=0.0, width=4.0, no='2', name='二单元'),
    dict(center=15.6, width=2.8, no='3', name='三单元'),
]
SHOPS = [
    dict(x0=-13.9, x1=-8.9, name='老陈烟酒', sub='烟 · 酒 · 副食 · 饮料',
         sign='#2b5743', fg='#f2e6bb', awning='#9b3b32', kind='grocery', side=-1),
    dict(x0=-8.6, x1=-3.6, name='阿香理发', sub='剪发 · 烫染 · 修面',
         sign='#31586a', fg='#f3ead1', awning='#d4c5a2', kind='barber', side=1),
    dict(x0=2.3, x1=7.3, name='兰州牛肉面', sub='牛肉面 · 盖浇饭 · 小菜',
         sign='#8e2d26', fg='#f4d77d', awning='#b44432', kind='noodle', side=-1),
    dict(x0=7.6, x1=12.6, name='老周修车', sub='修车 · 配钥匙 · 换锁',
         sign='#365268', fg='#efe4c3', awning='#5b6d69', kind='repair', side=1),
]

def init_materials():
    global M
    M = B.MATS
    M['plaster_green'] = mat_basic('店内浅绿墙', '#98a693', rough=0.85)
    M['plaster_cream'] = mat_basic('店内米色墙', '#c1b69e', rough=0.85)
    M['plaster_blue'] = mat_basic('店内浅蓝墙', '#9fb0b1', rough=0.85)
    M['plaster_pink'] = mat_basic('店内粉墙', '#b9a099', rough=0.88)
    M['shop_floor'] = mat_concrete('店面地砖', '#8b8376', '#625d54', rough=0.72)
    M['shop_ceiling'] = mat_basic('店面吊顶', '#a9a495', rough=0.9)
    M['shop_wood'] = mat_basic('店内木饰', '#7a5536', rough=0.7)
    M['shop_wood_dark'] = mat_basic('深色木柜', '#4e3a29', rough=0.75)
    M['shelf_metal'] = mat_basic('货架铁', '#7b7d76', rough=0.55, metal=0.4)
    M['fridge_white'] = mat_basic('冰柜白', '#d1cec2', rough=0.4, metal=0.2)
    M['fridge_glow'] = mat_basic('冰柜灯', '#bcd7c9', rough=0.25,
                                 emission=H('#9fd8c9'), emission_strength=1.8)
    M['menu_black'] = mat_basic('黑板', '#222622', rough=0.85)
    M['chalk_white'] = mat_basic('粉笔字', '#d5d2bd', rough=0.9)
    M['barber_red'] = mat_basic('理发红', '#9e2e29', rough=0.45)
    M['barber_blue'] = mat_basic('理发蓝', '#2e4f75', rough=0.45)
    M['chrome'] = mat_basic('镀铬', '#bcc0bd', rough=0.16, metal=0.9)
    M['mirror'] = mat_basic('镜面', '#b9c2c0', rough=0.05, metal=1.0)
    M['stool_red'] = mat_basic('红塑料凳', '#a63c31', rough=0.55)
    M['stool_blue'] = mat_basic('蓝塑料凳', '#315b76', rough=0.55)
    M['stool_yellow'] = mat_basic('黄塑料凳', '#b88f37', rough=0.6)
    M['beer_green'] = mat_basic('啤酒瓶绿', '#294a36', rough=0.25,
                                emission=H('#203c2a'), emission_strength=0.05)
    M['bottle_brown'] = mat_basic('酱油瓶', '#4d2c1b', rough=0.3)
    M['snack_red'] = mat_basic('零食红', '#b03c31', rough=0.65)
    M['snack_yellow'] = mat_basic('零食黄', '#c3a33e', rough=0.65)
    M['snack_blue'] = mat_basic('零食蓝', '#3d6584', rough=0.65)
    M['snack_green'] = mat_basic('零食绿', '#4d7045', rough=0.65)
    M['rice_sack'] = mat_basic('米袋', '#b8a77d', rough=0.92)
    M['steel_pot'] = mat_basic('不锈钢锅', '#a9aca6', rough=0.25, metal=0.9)
    M['vegetable'] = mat_basic('青菜', '#4f6b2d', rough=0.6)
    M['watermelon'] = mat_basic('西瓜', '#3f6d32', rough=0.55)
    M['meat'] = mat_basic('卤味', '#7e3a23', rough=0.5)
    M['tile_red'] = mat_basic('店面红砖', '#8d4e39', rough=0.82)
    M['tile_gray'] = mat_basic('店面灰砖', '#77756b', rough=0.8)
    M['yellow_gas'] = mat_basic('黄色燃气管', '#b59a32', rough=0.5, metal=0.1)
    M['notice_glass'] = mat_glass('公告栏玻璃', (0.26, 0.35, 0.33, 1.0), 0.1, 0.8)
    M['bulb'] = mat_basic('灯泡', '#f0cf8e', rough=0.3,
                          emission=H('#ffc36b'), emission_strength=8.0)
    M['hall_glow'] = mat_basic('门厅暖光', '#c89a62', rough=0.7,
                               emission=H('#ffc27e'), emission_strength=1.6)
    M['awning_stripe_red'] = mat_striped('红白条纹布', '#9f3d32', '#d1c5a7',
                                          scale=9.0, axis='X')
    M['awning_stripe_green'] = mat_striped('绿白条纹布', '#486150', '#cfc6b0',
                                            scale=9.0, axis='X')

def add_point(name, loc, energy, color=(1.0, 0.78, 0.5), radius=0.12, coll='灯光'):
    data = bpy.data.lights.new(name, 'POINT')
    data.energy = energy
    data.color = color
    data.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, data)
    C(coll).objects.link(ob)
    ob.location = loc
    return ob

def add_area_light(name, loc, size, energy, color=(1.0, 0.82, 0.62),
                   rot=(0, 0, 0), coll='灯光'):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = energy
    data.color = color
    data.shape = 'RECTANGLE'
    data.size = size[0]
    data.size_y = size[1]
    ob = bpy.data.objects.new(name, data)
    C(coll).objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    return ob

# ---------------------------------------------------------------------------
# front base band and opening shell
# ---------------------------------------------------------------------------
def build_ground_shell():
    # continuous upper band and plinth over the shop/entrance openings
    add_box('一层店面过梁', (0, -5.86, 3.675), (36.0, 0.30, 1.35),
            M['wall_warm'], '一层商铺')
    add_box('一层勒脚', (0, -5.95, 0.175), (36.0, 0.34, 0.35),
            M['tile_gray'], '一层商铺')
    add_box('一层勒脚线', (0, -6.14, 0.36), (36.0, 0.06, 0.07),
            M['concrete'], '一层商铺')
    # shop floors, ceiling and back wall
    add_box('店内地面', (0, -5.3, 0.24), (35.6, 1.5, 0.12), M['shop_floor'], '一层商铺')
    add_box('店内吊顶', (0, -5.3, 2.98), (35.6, 1.5, 0.10), M['shop_ceiling'], '一层商铺')
    add_box('店内后墙', (0, -4.58, 1.62), (35.6, 0.16, 2.85), M['plaster_cream'], '一层商铺')
    # ceiling beams visible through the glass
    for x in (-13.5, -8.4, -2.2, 2.4, 7.5, 12.5):
        add_box('店内梁' + str(x), (x, -5.32, 2.87), (0.16, 1.4, 0.16),
                M['concrete'], '一层商铺')
    # divider piers between units
    for x in (-14.05, -8.75, -3.45, 2.15, 7.45, 12.75, 14.05):
        add_box('店铺隔墙' + str(x), (x, -5.3, 1.58), (0.24, 1.5, 2.8),
                M['wall_warm'], '一层商铺')
    # wall panels in leftover structural gaps
    for x0, x1, z0, z1 in [
        (-18.0, -17.0, 0.35, 3.0), (-14.2, -13.9, 0.35, 3.0),
        (-3.6, -2.0, 0.35, 3.0), (12.6, 14.2, 0.35, 3.0),
        (17.0, 18.0, 0.35, 3.0),
    ]:
        add_box('一层补墙%.2f' % x0, ((x0 + x1) / 2, -5.86, (z0 + z1) / 2),
                (x1 - x0, 0.30, z1 - z0), M['wall_warm'], '一层商铺')
    # downpipes at the shop piers
    for x in (-14.06, 7.46, 14.06):
        add_cyl('一层落水管' + str(x), (x, -6.11, 1.65), 0.055, 2.9,
                M['pipe'], '一层商铺', vertices=10)
        add_curve('一层落水管弯' + str(x), [(x, -6.11, 0.22), (x, -6.24, 0.10),
                  (x, -6.3, 0.02)], 0.055, M['pipe'], '一层商铺')
        for z in (0.7, 1.7, 2.7):
            add_box('一层管卡' + str(x) + str(z), (x, -6.06, z),
                    (0.14, 0.12, 0.07), M['pipe_gray'], '一层商铺')
    # conduit and meter boxes along the band
    add_curve('一层线槽', [(-17.6, -6.04, 3.05), (-2.1, -6.04, 3.05),
              (2.1, -6.04, 3.05), (17.6, -6.04, 3.05)], 0.026,
              M['pipe_gray'], '一层商铺', resolution=2)
    for x in (-6.4, 5.3, 13.8):
        add_box('电表箱' + str(x), (x, -6.13, 2.55), (0.42, 0.18, 0.55),
                M['pipe_gray'], '一层商铺', bevel=0.01)
        add_box('电表窗' + str(x), (x, -6.23, 2.63), (0.28, 0.02, 0.26),
                M['glass_frost'], '一层商铺')
        add_text('电表字' + str(x), '电表', (x, -6.245, 2.39), 0.075,
                 M['ink'], '标识', font=FONT_SANS)
    # gas riser pipes
    for x in (-10.8, 9.4):
        add_cyl('燃气管' + str(x), (x, -6.11, 2.1), 0.025, 2.3,
                M['yellow_gas'], '一层商铺', vertices=8)
        add_curve('燃气横管' + str(x), [(x, -6.11, 3.2), (x - 1.2, -6.11, 3.28),
                  (x - 1.2, -6.11, 3.8)], 0.023, M['yellow_gas'], '一层商铺')
        for z in (1.3, 2.5):
            add_box('燃气表' + str(x) + str(z), (x + 0.2, -6.15, z),
                    (0.26, 0.16, 0.34), M['yellow_paint'], '一层商铺', bevel=0.01)

# ---------------------------------------------------------------------------
# shop builder
# ---------------------------------------------------------------------------
def build_shop(s):
    x0, x1 = s['x0'], s['x1']
    cx = (x0 + x1) / 2
    width = x1 - x0
    yfront = -6.0
    # interior wall colour
    wallmat = dict(grocery=M['plaster_green'], barber=M['plaster_blue'],
                   noodle=M['plaster_cream'], repair=M['plaster_pink'])[s['kind']]
    add_box('店内墙_' + s['name'], (cx, -4.69, 1.6), (width - 0.1, 0.03, 2.72),
            wallmat, '一层商铺')
    # small interior back counter / shelf strip
    add_box('店内踢脚_' + s['name'], (cx, -5.98, 0.42), (width - 0.1, 0.05, 0.5),
            M['shop_wood_dark'], '一层商铺')
    # front frame: lower sill under windows, posts at both ends, door frame
    door_w = 1.05
    door_side = s['side']  # -1 door on left, 1 door on right
    door_cx = x0 + 0.56 if door_side < 0 else x1 - 0.56
    win_x0 = x0 + 0.10 if door_side < 0 else x0 + 0.55
    win_x1 = x1 - 0.55 if door_side < 0 else x1 - 0.10
    win_cx = (win_x0 + win_x1) / 2
    win_w = win_x1 - win_x0
    # frame
    frame_mat = M['aluminum'] if s['kind'] != 'noodle' else M['shop_wood']
    add_boxes('店面框_' + s['name'], [
        ((x0 + 0.09, yfront, 1.66), (0.14, 0.12, 2.66)),
        ((x1 - 0.09, yfront, 1.66), (0.14, 0.12, 2.66)),
        ((cx, yfront, 2.96), (width, 0.12, 0.12)),
        ((cx, yfront, 2.38), (width, 0.10, 0.07)),
        ((door_cx - door_w / 2, yfront, 1.6), (0.07, 0.1, 2.6)),
        ((door_cx + door_w / 2, yfront, 1.6), (0.07, 0.1, 2.6)),
        ((win_x1, yfront, 1.6), (0.06, 0.1, 2.6)),
        ((win_x0, yfront, 1.6), (0.06, 0.1, 2.6)),
    ], frame_mat, '一层商铺')
    # window sill
    add_box('窗台_' + s['name'], (win_cx, yfront - 0.1, 0.88), (win_w + 0.12, 0.25, 0.08),
            M['concrete'], '一层商铺', bevel=0.01)
    # big display glass and interior view
    add_plane('橱窗玻璃_' + s['name'], (win_cx, yfront - 0.005, 1.9), win_w - 0.05,
              1.94, M['glass'], '一层商铺', rot=(math.pi / 2, 0, 0))
    add_plane('门玻璃_' + s['name'], (door_cx, yfront - 0.005, 1.55), door_w - 0.08,
              2.22, M['glass'], '一层商铺', rot=(math.pi / 2, 0, 0))
    # door handles, hinge line and Chinese push/pull sticker
    add_cyl('门把手_' + s['name'], (door_cx + door_side * 0.36, yfront - 0.08, 1.35),
            0.016, 0.32, M['chrome'], '一层商铺', vertices=8, rot=(0, math.pi / 2, 0))
    add_text('推拉_' + s['name'], '拉', (door_cx - door_side * 0.1, yfront - 0.032, 1.55),
             0.14, M['white_paint'], '标识', font=FONT_BOLD)
    # poster strips on the glass
    for k in range(rand.randint(1, 3)):
        px = win_x0 + rand.uniform(0.2, win_w - 0.4)
        pz = rand.uniform(1.0, 2.55)
        add_box('玻璃贴纸_' + s['name'] + str(k), (px, yfront - 0.02, pz),
                (rand.uniform(0.18, 0.34), 0.01, rand.uniform(0.24, 0.5)),
                [M['snack_red'], M['snack_yellow'], M['paper']][rand.randrange(3)],
                '一层商铺')
    # sign board
    sign_z = 3.48
    add_box('招牌_' + s['name'], (cx, -6.11, sign_z), (width - 0.12, 0.14, 0.92),
            mat_basic('招牌_' + s['name'], s['sign'], rough=0.55), '招牌', bevel=0.02)
    add_box('招牌边_' + s['name'], (cx, -6.19, sign_z), (width - 0.26, 0.04, 0.78),
            mat_basic('招牌边_' + s['name'], '#c9b98f', rough=0.65), '招牌')
    name_size = min(0.55, (width - 0.8) / max(2.0, len(s['name'])))
    add_text('招牌字_' + s['name'], s['name'], (cx, -6.225, sign_z + 0.06),
             name_size, mat_basic('招牌字_' + s['name'], s['fg'], rough=0.5),
             '招牌', font=FONT_BOLD, extrude=0.015)
    add_text('招牌副_' + s['name'], s['sub'], (cx, -6.225, sign_z - 0.36),
             0.145, mat_basic('招牌副_' + s['name'], s['fg'], rough=0.65),
             '招牌', font=FONT_SANS)
    # awning, with a subtle sag and scalloped valance
    if s['kind'] in ('grocery', 'noodle', 'repair'):
        aw_y0, aw_y1 = -6.02, -7.45
        aw_z0, aw_z1 = 3.05, 2.78
        verts = [(x0 + 0.15, aw_y0, aw_z0), (x1 - 0.15, aw_y0, aw_z0),
                 (x1 - 0.15, aw_y1, aw_z1), (x0 + 0.15, aw_y1, aw_z1)]
        add_mesh('雨棚_' + s['name'], verts, [(3, 2, 1, 0)],
                 M['awning_stripe_red'] if s['kind'] != 'repair' else M['awning_stripe_green'],
                 '一层商铺', smooth=True)
        # valance
        av = []
        nu = 30
        for i in range(nu + 1):
            u = i / nu
            x = x0 + 0.15 + (x1 - x0 - 0.3) * u
            z = aw_z1 - 0.02 - 0.06 * math.sin(u * math.pi * 14) ** 2
            av.append((x, aw_y1 - 0.01, z))
        for i in range(nu + 1):
            u = i / nu
            x = x0 + 0.15 + (x1 - x0 - 0.3) * u
            z = aw_z1 - 0.25 - 0.04 * math.sin(u * math.pi * 14) ** 2
            av.append((x, aw_y1 - 0.01, z))
        faces = []
        for i in range(nu):
            faces.append((i, nu + 1 + i, nu + 1 + i + 1, i + 1))
        add_mesh('雨棚帘_' + s['name'], av, faces,
                 M['awning_stripe_red'] if s['kind'] != 'repair' else M['awning_stripe_green'],
                 '一层商铺')
        # support arms
        for xx in (x0 + 0.35, x1 - 0.35):
            tube_between('雨棚撑_' + s['name'] + str(xx),
                         (xx, -6.04, 3.75), (xx, -7.32, 2.82), 0.018,
                         M['metal_gray'], '一层商铺')
            add_box('雨棚座_' + s['name'] + str(xx), (xx, -6.04, 3.76),
                    (0.08, 0.06, 0.08), M['rust'], '一层商铺')
    # shop-specific interior and exterior
    func = dict(grocery=shop_grocery, barber=shop_barber,
                noodle=shop_noodle, repair=shop_repair)[s['kind']]
    func(s, cx, width, door_cx, win_cx, win_w)

def _hanging_bulb(name, loc, mat=None):
    mat = mat or M['bulb']
    x, y, z = loc
    add_curve(name + '_线', [(x, y, 2.96), (x, y, z + 0.1)], 0.004,
              M['black_paint'], '一层商铺')
    add_uvsphere(name + '_泡', (x, y, z), 0.055, mat, '一层商铺', segments=12, rings=8)
    add_cyl(name + '_口', (x, y, z + 0.06), 0.028, 0.05, M['metal_gray'],
            '一层商铺', vertices=10)

def _shelf_with_goods(name, x0, x1, y, z0, levels=3, seed=1):
    r = random.Random(seed)
    add_box(name + '_背', ((x0 + x1) / 2, y, z0 + 0.9), (x1 - x0, 0.04, 1.8),
            M['shop_wood_dark'], '一层商铺')
    for l in range(levels):
        z = z0 + 0.35 + l * 0.55
        add_box(name + f'_板{l}', ((x0 + x1) / 2, y - 0.16, z),
                (x1 - x0, 0.36, 0.045), M['shop_wood'], '一层商铺')
        n = max(3, int((x1 - x0) / 0.22))
        for i in range(n):
            if r.random() < 0.18:
                continue
            px = x0 + 0.12 + (x1 - x0 - 0.24) * (i + 0.5) / n
            h = r.uniform(0.16, 0.28)
            w = r.uniform(0.10, 0.18)
            mat = [M['bottle_brown'], M['beer_green'], M['snack_red'],
                   M['snack_yellow'], M['snack_blue'], M['snack_green']][r.randrange(6)]
            if l == 0 and r.random() < 0.4:
                add_cyl(name + f'_瓶{l}_{i}', (px, y - 0.16, z + 0.12 + h / 2),
                        0.04, h, mat, '一层商铺', vertices=8)
            else:
                add_box(name + f'_货{l}_{i}', (px, y - 0.16, z + 0.025 + h / 2),
                        (w, 0.22, h), mat, '一层商铺')

def shop_grocery(s, cx, width, door_cx, win_cx, win_w):
    name = s['name']
    # shelves and fridge
    _shelf_with_goods('货架_' + name, cx - 1.4, cx + 1.2, -4.78, 0.3, 3, seed=11)
    add_box('冰柜_' + name, (cx - 2.05, -5.3, 1.05), (1.2, 0.9, 1.5),
            M['fridge_white'], '一层商铺', bevel=0.02)
    add_box('冰柜玻璃_' + name, (cx - 2.05, -5.77, 1.25), (1.04, 0.03, 0.9),
            M['fridge_glow'], '一层商铺')
    add_box('冰柜顶_' + name, (cx - 2.05, -5.3, 1.82), (1.24, 0.94, 0.06),
            M['metal_gray'], '一层商铺')
    for i in range(4):
        add_cyl('饮料_' + name + str(i), (cx - 2.4 + i * 0.22, -5.68, 1.0),
                0.055, 0.28, [M['snack_red'], M['snack_green'], M['snack_yellow'], M['bottle_brown']][i],
                '一层商铺', vertices=8)
    # counter
    add_box('柜台_' + name, (cx + 1.9, -5.25, 1.0), (1.5, 0.8, 1.15),
            M['shop_wood'], '一层商铺', bevel=0.02)
    add_box('柜台面_' + name, (cx + 1.9, -5.25, 1.59), (1.6, 0.9, 0.08),
            M['shop_wood_dark'], '一层商铺')
    # cigarette display behind the counter
    add_box('烟架_' + name, (cx + 1.6, -4.82, 2.05), (1.3, 0.1, 0.9),
            M['shop_wood_dark'], '一层商铺')
    for r in range(3):
        for c in range(5):
            add_box('烟盒_' + name + str(r) + str(c),
                    (cx + 1.05 + c * 0.23, -4.9, 1.8 + r * 0.22),
                    (0.18, 0.07, 0.16),
                    [M['snack_red'], M['snack_yellow'], M['snack_blue']][(r + c) % 3],
                    '一层商铺')
    _hanging_bulb('吊灯_' + name, (cx - 0.1, -5.2, 2.45))
    add_point('店内灯_' + name, (cx, -5.2, 2.55), 55, (1.0, 0.78, 0.5), 0.18)
    # price board near the door
    add_box('价目板_' + name, (door_cx - 0.8 * s['side'], -5.9, 1.45),
            (0.7, 0.04, 0.9), M['white_paint'], '一层商铺')
    add_text('价目字_' + name, '烟酒\n副食', (door_cx - 0.8 * s['side'], -5.925, 1.55),
             0.12, M['ink'], '一层商铺', font=FONT_BOLD)
    # outside: beer crates, cardboard boxes, an advertisement umbrella
    ox = cx - width / 2 + 0.45
    for i in range(3):
        add_box('啤酒箱_' + name + str(i), (ox + 0.3 * i, -6.65, 0.34 + i * 0.3),
                (0.42, 0.35, 0.28), M['beer_green'] if i % 2 else M['snack_red'],
                '街道细节', bevel=0.01)
    for i in range(4):
        add_box('纸箱_' + name + str(i), (ox + 1.0 + 0.3 * (i % 2),
                -6.8 - 0.3 * (i // 2), 0.28 + 0.42 * (i // 2)),
                (0.5, 0.42, 0.45), M['cardboard'], '街道细节',
                rot=(0, 0, rand.uniform(-0.12, 0.12)))
    add_cyl('冰柜招牌_' + name, (cx + 2.1, -6.85, 1.0), 0.24, 0.8,
            M['fridge_white'], '街道细节', vertices=20)
    add_box('冰柜贴_' + name, (cx + 2.1, -7.09, 1.12), (0.34, 0.02, 0.36),
            M['snack_red'], '街道细节')
    add_text('冰柜字_' + name, '冰', (cx + 2.1, -7.105, 1.12), 0.22,
             M['white_paint'], '标识', font=FONT_BOLD)

def shop_barber(s, cx, width, door_cx, win_cx, win_w):
    name = s['name']
    # mirror wall, chair, counter
    add_box('镜墙_' + name, (cx - 0.6, -4.8, 1.75), (1.8, 0.06, 1.4),
            M['mirror'], '一层商铺')
    for i in range(3):
        add_box('镜框_' + name + str(i), (cx - 1.5 + i * 0.9, -4.76, 1.75),
                (0.05, 0.04, 1.5), M['chrome'], '一层商铺')
    # barber chairs
    for i in range(2):
        chx = cx - 0.9 + i * 1.05
        add_cyl('椅座_' + name + str(i), (chx, -5.35, 0.85), 0.3, 0.16,
                M['barber_red'], '一层商铺', vertices=20)
        add_box('椅背_' + name + str(i), (chx, -5.58, 1.25), (0.52, 0.12, 0.8),
                M['barber_red'], '一层商铺', bevel=0.06)
        add_cyl('椅杆_' + name + str(i), (chx, -5.35, 0.5), 0.05, 0.55,
                M['chrome'], '一层商铺', vertices=10)
        add_cyl('椅底盘_' + name + str(i), (chx, -5.35, 0.22), 0.22, 0.05,
                M['chrome'], '一层商铺', vertices=16)
        add_box('扶手_' + name + str(i), (chx, -5.35, 1.02), (0.7, 0.08, 0.05),
                M['chrome'], '一层商铺')
    # basin counter
    add_box('洗头池_' + name, (cx + 1.7, -5.22, 0.95), (1.15, 0.7, 0.8),
            M['plaster_blue'], '一层商铺')
    add_cyl('洗头盆_' + name, (cx + 1.7, -5.3, 1.38), 0.28, 0.08,
            M['chrome'], '一层商铺', vertices=18)
    add_cyl('水龙头_' + name, (cx + 1.7, -5.42, 1.5), 0.012, 0.24,
            M['chrome'], '一层商铺', vertices=8, rot=(math.pi / 2, 0, 0))
    _hanging_bulb('理发灯_' + name, (cx + 0.3, -5.2, 2.5), M['light_cool'])
    add_point('理发店灯_' + name, (cx, -5.1, 2.6), 65, (0.85, 0.93, 1.0), 0.2)
    # posters, price list
    add_box('价目表_' + name, (cx + 2.05, -4.76, 1.65), (0.65, 0.03, 1.0),
            M['white_paint'], '一层商铺')
    add_text('价目表字_' + name, '洗剪吹\n15元', (cx + 2.05, -4.785, 1.65),
             0.12, M['ink'], '一层商铺', font=FONT_BOLD)
    add_box('发型海报_' + name, (cx - 2.1, -4.76, 1.75), (0.55, 0.03, 0.8),
            M['snack_pink'] if 'snack_pink' in M else M['paper'], '一层商铺')
    # exterior barber pole
    px = s['x0'] + 0.22
    add_cyl('理发转灯_' + name, (px, -6.24, 2.3), 0.09, 0.62,
            M['barber_red'], '一层商铺', vertices=18, rot=(0, 0, 0))
    # stripe rings on pole
    for i in range(6):
        add_cyl('理发灯环_' + name + str(i), (px, -6.24, 2.02 + i * 0.11), 0.093, 0.035,
                M['white_paint'] if i % 2 else M['barber_blue'], '一层商铺', vertices=18)
    add_cyl('理发灯帽_' + name, (px, -6.24, 2.65), 0.11, 0.06, M['chrome'],
            '一层商铺', vertices=18)
    add_box('理发灯座_' + name, (px, -6.19, 2.3), (0.12, 0.15, 0.5),
            M['metal_gray'], '一层商铺')
    # a folding chair and small table outside
    add_box('等候椅_' + name, (s['x1'] - 0.55, -6.55, 0.45), (0.42, 0.42, 0.05),
            M['stool_blue'], '街道细节', bevel=0.01)
    for dx, dy in ((-0.16, -0.16), (0.16, -0.16), (-0.16, 0.16), (0.16, 0.16)):
        add_box('等候椅腿_' + name + str(dx) + str(dy),
                (s['x1'] - 0.55 + dx, -6.55 + dy, 0.28),
                (0.03, 0.03, 0.34), M['metal_gray'], '街道细节')

def shop_noodle(s, cx, width, door_cx, win_cx, win_w):
    name = s['name']
    # warm interior: counter, kitchen pass, huge stock pot
    add_box('面案_' + name, (cx - 1.0, -5.15, 1.08), (2.3, 0.75, 1.1),
            M['shop_wood'], '一层商铺', bevel=0.02)
    add_box('面案台_' + name, (cx - 1.0, -5.15, 1.66), (2.45, 0.88, 0.08),
            M['steel_pot'], '一层商铺')
    add_cyl('大汤锅_' + name, (cx - 1.55, -5.1, 1.95), 0.36, 0.42,
            M['steel_pot'], '一层商铺', vertices=24)
    add_cyl('汤锅盖_' + name, (cx - 1.55, -5.1, 2.18), 0.37, 0.03,
            M['steel_pot'], '一层商铺', vertices=24)
    # steam wisps (thin translucent ribbons, reads well at distance)
    for k in range(4):
        pts = [(cx - 1.55 + 0.1 * math.sin(i * 0.9 + k), -5.05,
                2.22 + i * 0.18) for i in range(8)]
        add_curve('蒸汽_' + name + str(k), pts, 0.02 + 0.01 * k,
                  mat_basic('蒸汽' + str(k), '#cfd3c8', rough=0.5,
                            emission=H('#cfd3c8'), emission_strength=0.15),
                  '一层商铺', resolution=4)
    # menu board on back wall
    add_box('菜单_' + name, (cx + 1.7, -4.78, 1.9), (1.6, 0.04, 1.1),
            M['menu_black'], '一层商铺')
    add_text('菜单字_' + name, '牛 肉 面\n小 菜\n盖 浇 饭', (cx + 1.7, -4.805, 1.95),
             0.15, M['chalk_white'], '一层商铺', font=FONT_SANS)
    # kitchen hatch with warm light
    add_box('厨房口_' + name, (cx + 1.7, -4.82, 1.0), (1.4, 0.1, 0.55),
            M['light_warm'], '一层商铺')
    add_box('厨房框_' + name, (cx + 1.7, -4.75, 1.0), (1.55, 0.05, 0.7),
            M['shop_wood_dark'], '一层商铺')
    for k in range(3):
        _hanging_bulb('面馆灯_' + name + str(k), (cx - 1.7 + k * 1.5, -5.05, 2.42))
    add_point('面馆灯_' + name, (cx, -5.0, 2.5), 85, (1.0, 0.66, 0.36), 0.2)
    # exterior red lanterns
    for sx in (-1, 1):
        lx = cx + sx * 1.2
        add_cyl('面馆灯笼钩_' + name + str(sx), (lx, -6.3, 2.9), 0.012, 0.3,
                M['metal_gray'], '一层商铺', vertices=6)
        add_uvsphere('面馆灯笼_' + name + str(sx), (lx, -6.3, 2.63), 0.19,
                     M['red_banner'], '一层商铺', segments=20, rings=12)
        add_cyl('面馆灯穗_' + name + str(sx), (lx, -6.3, 2.41), 0.012, 0.2,
                M['gold'], '一层商铺', vertices=6)
    # vent duct on the facade
    add_cyl('排烟管_' + name, (s['x0'] + 0.6, -6.28, 3.0), 0.14, 2.0,
            M['metal_gray'], '一层商铺', vertices=14, rot=(0, 0, 0))
    add_cyl('排烟弯_' + name, (s['x0'] + 0.6, -6.4, 2.05), 0.14, 0.3,
            M['metal_gray'], '一层商铺', vertices=14, rot=(math.pi / 2, 0, 0))
    # outside: folding table, stools, menu stand
    tx = s['x1'] - 1.15
    add_box('面馆桌_' + name, (tx, -6.75, 0.72), (0.9, 0.8, 0.05),
            M['shop_wood'], '街道细节', bevel=0.01)
    for dx, dy in ((-0.36, -0.3), (0.36, -0.3), (-0.36, 0.3), (0.36, 0.3)):
        add_box('面馆桌腿_' + name + str(dx) + str(dy),
                (tx + dx, -6.75 + dy, 0.36), (0.04, 0.04, 0.72),
                M['metal_gray'], '街道细节')
    for i, (sx, sy, mat) in enumerate([(-0.8, 0.1, M['stool_red']),
                                       (0.75, 0.25, M['stool_blue']),
                                       (0.1, -0.7, M['stool_red'])]):
        _plastic_stool('面馆凳_' + name + str(i), (tx + sx, -6.75 + sy, 0.08), mat)
    add_box('面馆菜单架_' + name, (s['x0'] + 0.7, -6.9, 0.85), (0.55, 0.06, 1.1),
            M['menu_black'], '街道细节', rot=(0, 0, 0.1), bevel=0.01)
    add_text('面馆菜单字_' + name, '牛 肉 面\n10元', (s['x0'] + 0.7, -6.935, 0.95),
             0.10, M['chalk_white'], '标识', font=FONT_SANS, rot=(math.pi/2, 0, 0.1))
    # a stack of bowls
    for i in range(4):
        add_cyl('碗_' + name + str(i), (tx - 0.15, -6.6, 0.8 + i * 0.035),
                0.14, 0.035, M['white_paint'], '街道细节', vertices=16)

def shop_repair(s, cx, width, door_cx, win_cx, win_w):
    name = s['name']
    # workbench, tools, tires
    add_box('工作台_' + name, (cx + 0.8, -5.2, 0.95), (2.0, 0.75, 1.0),
            M['shop_wood_dark'], '一层商铺', bevel=0.02)
    add_box('台钳_' + name, (cx + 1.1, -5.3, 1.55), (0.22, 0.3, 0.18),
            M['metal_gray'], '一层商铺')
    for i in range(5):
        add_box('工具_' + name + str(i), (cx + 0.2 + i * 0.25, -5.05, 1.48),
                (0.05, 0.05, rand.uniform(0.12, 0.3)), M['rust'], '一层商铺',
                rot=(0, 0, rand.uniform(-0.3, 0.3)))
    # pegboard with tools
    add_box('工具板_' + name, (cx + 0.8, -4.77, 1.9), (1.9, 0.04, 1.1),
            M['shop_wood_dark'], '一层商铺')
    for i in range(12):
        add_box('挂件_' + name + str(i),
                (cx + 0.1 + (i % 6) * 0.3, -4.8, 1.55 + (i // 6) * 0.42),
                (0.04, 0.02, rand.uniform(0.12, 0.32)),
                M['metal_gray'], '一层商铺')
    # tire stack near window
    for i in range(4):
        add_cyl('轮胎_' + name + str(i), (cx - 1.7, -5.2, 0.34 + i * 0.24),
                0.34, 0.2, M['black_paint'], '一层商铺', vertices=24)
        add_cyl('轮毂_' + name + str(i), (cx - 1.7, -5.2, 0.34 + i * 0.24),
                0.17, 0.22, M['metal_gray'], '一层商铺', vertices=16)
    add_box('钥匙机_' + name, (cx - 2.0, -5.25, 1.0), (0.42, 0.5, 0.75),
            M['metal_gray'], '一层商铺', bevel=0.02)
    add_cyl('钥匙机轮_' + name, (cx - 2.0, -5.52, 1.12), 0.15, 0.05,
            M['rust'], '一层商铺', vertices=16, rot=(math.pi / 2, 0, 0))
    _hanging_bulb('修理灯_' + name, (cx, -5.1, 2.45))
    add_point('修理灯_' + name, (cx, -5.0, 2.55), 55, (1.0, 0.78, 0.48), 0.2)
    # wall sign "配钥匙"
    add_box('修车小牌_' + name, (s['x0'] + 0.3, -6.28, 2.45), (0.5, 0.06, 0.9),
            M['sign_yellow'], '招牌')
    add_text('修车小字_' + name, '配\n钥\n匙', (s['x0'] + 0.3, -6.32, 2.45),
             0.2, M['ink'], '招牌', font=FONT_BOLD)
    # exterior clutter: bike wheels, pump, toolbox
    wx = s['x1'] - 0.6
    for i in range(3):
        add_cyl('立轮_' + name + str(i), (wx - i * 0.35, -6.62, 0.55),
                0.34, 0.05, M['black_paint'], '街道细节', vertices=24,
                rot=(math.pi / 2, 0, 0.2))
        add_cyl('立轮毂_' + name + str(i), (wx - i * 0.35, -6.62, 0.55),
                0.07, 0.06, M['metal_gray'], '街道细节', vertices=12,
                rot=(math.pi / 2, 0, 0.2))
    add_box('工具箱_' + name, (s['x0'] + 0.9, -6.7, 0.38), (0.5, 0.3, 0.3),
            M['snack_red'], '街道细节', bevel=0.01)
    add_cyl('打气筒_' + name, (s['x0'] + 1.5, -6.6, 0.5), 0.035, 0.7,
            M['metal_gray'], '街道细节', vertices=8)

def _plastic_stool(name, loc, mat):
    x, y, z = loc
    add_box(name + '_面', (x, y, z + 0.30), (0.28, 0.28, 0.035), mat,
            '街道细节', bevel=0.012)
    for dx, dy in ((-0.1, -0.1), (0.1, -0.1), (-0.1, 0.1), (0.1, 0.1)):
        add_box(name + '_腿', (x + dx, y + dy, z + 0.15), (0.028, 0.028, 0.3),
                mat, '街道细节')

# ---------------------------------------------------------------------------
# entrances
# ---------------------------------------------------------------------------
def build_entrance(st):
    cx = st['center']
    width = st['width']
    name = st['name']
    # portal side walls / lintel within opening
    add_box('门洞侧墙L_' + name, (cx - width / 2 + 0.12, -5.3, 1.65),
            (0.24, 1.4, 2.65), M['wall_warm'], '单元入口')
    add_box('门洞侧墙R_' + name, (cx + width / 2 - 0.12, -5.3, 1.65),
            (0.24, 1.4, 2.65), M['wall_warm'], '单元入口')
    add_box('门洞顶_' + name, (cx, -5.3, 2.98), (width, 1.4, 0.06),
            M['concrete'], '单元入口')
    add_box('门洞地_' + name, (cx, -5.3, 0.30), (width, 1.4, 0.1),
            M['concrete_dark'], '单元入口')
    add_box('门斗后墙_' + name, (cx, -4.55, 1.65), (width, 0.1, 2.65),
            M['dark_warm'], '单元入口')
    # warm glow at the back of the hall, seen through the frosted door glass
    add_box('门厅暖墙_' + name, (cx, -4.63, 2.2), (width * 0.66, 0.02, 1.05),
            M['hall_glow'], '单元入口')
    # staircase as seen through the door
    for i in range(7):
        add_box('门内台阶_' + name + str(i), (cx - 0.5, -5.18 + i * 0.13,
                0.42 + i * 0.18), (1.5, 0.26, 0.18), M['concrete'], '单元入口')
    add_curve('门内扶手_' + name, [(cx - 1.1, -5.3, 0.7), (cx - 1.1, -4.7, 2.2)],
              0.025, M['green_metal'], '单元入口')
    # steps up from pavement
    for i in range(3):
        add_box('门前台阶_' + name + str(i), (cx, -6.3 - i * 0.26,
                0.08 + (2 - i) * 0.09), (width - 0.4 - i * 0.12, 0.28, 0.18),
                M['concrete'], '单元入口', bevel=0.012)
    # threshold / mat
    add_box('门垫_' + name, (cx, -5.6, 0.36), (1.7, 0.6, 0.025),
            M['cloth_gray'], '单元入口')
    # green double door, slightly ajar
    dw, dh = min(2.1, width - 0.55), 2.3
    dz = 0.36
    add_boxes('单元门框_' + name, [
        ((cx, -5.35, dz + dh / 2), (dw + 0.1, 0.1, 0.08)),
        ((cx, -5.35, dz), (dw + 0.1, 0.1, 0.08)),
        ((cx - dw / 2, -5.35, dz + dh / 2), (0.08, 0.1, dh)),
        ((cx + dw / 2, -5.35, dz + dh / 2), (0.08, 0.1, dh)),
        ((cx, -5.35, dz + dh / 2), (0.05, 0.1, dh)),
    ], M['green_metal'], '单元入口')
    # door leaves with frosted glass tops
    for side in (-1, 1):
        leaf_cx = cx + side * (dw / 4)
        add_box('单元门板_' + name + str(side), (leaf_cx, -5.33, dz + dh / 2),
                (dw / 2 - 0.03, 0.06, dh - 0.05), M['green_metal'], '单元入口')
        add_box('单元门玻璃_' + name + str(side), (leaf_cx, -5.37, dz + dh * 0.68),
                (dw / 2 - 0.22, 0.02, dh * 0.4), M['glass_frost'], '单元入口')
        add_box('门玻璃格_' + name + str(side), (leaf_cx, -5.39, dz + dh * 0.68),
                (0.035, 0.03, dh * 0.42), M['green_metal'], '单元入口')
        add_cyl('门把手_' + name + str(side), (cx + side * 0.12, -5.41,
                dz + 1.05), 0.02, 0.22, M['chrome'], '单元入口',
                vertices=8, rot=(0, math.pi / 2, 0))
    add_text('单元门牌_' + name, st['no'], (cx + 0.0, -5.41, dz + dh * 0.84),
             0.22, M['gold'], '标识', font=FONT_BOLD)
    # canopy
    add_box('单元雨棚_' + name, (cx, -6.45, 3.05), (width + 0.7, 1.35, 0.16),
            M['concrete'], '单元入口', bevel=0.02)
    add_box('单元雨棚沿_' + name, (cx, -7.13, 2.96), (width + 0.7, 0.12, 0.22),
            M['wall_warm'], '单元入口')
    for sx in (-1, 1):
        tube_between('雨棚拉杆_' + name + str(sx),
                     (cx + sx * (width / 2 - 0.1), -6.05, 3.8),
                     (cx + sx * (width / 2 - 0.1), -7.05, 3.1), 0.02,
                     M['metal_gray'], '单元入口')
    # house number board above door
    add_box('单元号牌_' + name, (cx, -6.23, 3.42), (1.35, 0.08, 0.42),
            M['white_paint'], '标识', bevel=0.01)
    add_text('单元号字_' + name, st['name'], (cx, -6.285, 3.42), 0.2,
             M['red_paint'], '标识', font=FONT_BOLD)
    # mailboxes
    my = -5.82
    mx0 = cx + width / 2 - 0.05
    for r in range(6):
        for c in range(3):
            bx = mx0 - 0.1 - c * 0.23
            bz = 1.55 + r * 0.2
            add_box('信报箱_' + name + str(r) + str(c), (bx, my, bz),
                    (0.20, 0.18, 0.18), M['green_metal'], '单元入口')
            add_box('信报箱缝_' + name + str(r) + str(c), (bx, my - 0.10, bz + 0.03),
                    (0.12, 0.01, 0.015), M['dark'], '单元入口')
    # intercom and meter panel
    add_box('可视对讲_' + name, (cx + width / 2 - 0.38, -6.12, 1.45),
            (0.22, 0.06, 0.3), M['metal_gray'], '单元入口')
    add_box('对讲屏_' + name, (cx + width / 2 - 0.38, -6.16, 1.47),
            (0.14, 0.01, 0.14), M['light_cool'], '单元入口')
    add_box('总表箱_' + name, (cx - width / 2 + 0.36, -6.11, 1.7),
            (0.38, 0.16, 0.75), M['pipe_gray'], '单元入口', bevel=0.01)
    for i in range(4):
        add_box('总表窗_' + name + str(i),
                (cx - width / 2 + 0.36, -6.2, 1.45 + i * 0.16),
                (0.24, 0.01, 0.11), M['glass_frost'], '单元入口')
    # central entrance gets a red community banner and lanterns
    if st['no'] == '2':
        _community_banner(cx, width)
        for sx in (-1, 1):
            lx = cx + sx * (width / 2 - 0.55)
            add_uvsphere('大门灯笼_' + name + str(sx), (lx, -6.35, 2.72), 0.24,
                         M['red_banner'], '单元入口', segments=22, rings=14)
            add_cyl('灯笼顶_' + name + str(sx), (lx, -6.35, 2.94), 0.08, 0.06,
                    M['gold'], '单元入口', vertices=12)
            add_cyl('灯笼穗_' + name + str(sx), (lx, -6.35, 2.42), 0.012, 0.25,
                    M['gold'], '单元入口', vertices=6)
            add_curve('灯笼线_' + name + str(sx), [(lx, -6.35, 2.96),
                      (lx, -6.35, 3.1)], 0.006, M['black_paint'], '单元入口')
    else:
        # a single smaller lantern for the side entrances
        lx = cx + width / 2 - 0.4
        add_uvsphere('侧门灯笼_' + name, (lx, -6.2, 2.6), 0.16,
                     M['red_banner'], '单元入口', segments=18, rings=10)
        add_cyl('侧门灯笼穗_' + name, (lx, -6.2, 2.42), 0.01, 0.2,
                M['gold'], '单元入口', vertices=6)
    # entrance light, tucked under the canopy
    add_box('门灯_' + name, (cx, -6.32, 2.84), (0.20, 0.10, 0.09),
            M['white_paint'], '单元入口')
    add_point('门灯点_' + name, (cx, -6.28, 2.79), 14, (1.0, 0.78, 0.52), 0.22)
    # stairs seen through door: warm interior light
    add_area_light('门内光_' + name, (cx, -5.0, 1.9), (1.2, 0.8), 42,
                   (1.0, 0.72, 0.44), rot=(math.pi / 2, 0, 0))
    add_point('门厅灯_' + name, (cx, -4.95, 2.55), 35, (1.0, 0.74, 0.46), 0.25)
    # a broom and a doormat prop
    bx = cx - width / 2 + 0.3
    add_cyl('门边扫帚_' + name, (bx, -6.35, 0.75), 0.025, 1.4,
            M['wood'], '街道细节', vertices=6, rot=(0.1, 0.08, 0))
    add_box('门边簸箕_' + name, (bx + 0.1, -6.35, 0.22), (0.25, 0.05, 0.3),
            M['metal_gray'], '街道细节')

def _community_banner(cx, width):
    # red banner stretched under the canopy, with white characters
    z0 = 2.92
    y = -7.18
    verts, faces = [], []
    nx, nz = 26, 3
    for j in range(nz + 1):
        for i in range(nx + 1):
            u = i / nx
            x = cx - width / 2 - 0.5 + u * (width + 1.0)
            zz = z0 - j / nz * 0.52 - 0.035 * math.sin(u * math.pi * 2) * (j / nz)
            yy = y + 0.025 * math.sin(u * math.pi * 6) * (j / nz)
            verts.append((x, yy, zz))
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + nx + 1, a + nx + 2, a + 1))
    add_mesh('社区横幅', verts, faces, M['red_banner'], '标识', smooth=True)
    add_text('社区横幅字', '共建文明社区  共享美好生活',
             (cx, y - 0.03, z0 - 0.27), 0.25, M['white_paint'], '标识',
             font=FONT_BOLD, spacing=1.05)
    # tie strings at both ends
    for sx in (-1, 1):
        x = cx + sx * (width / 2 + 0.5)
        add_curve('横幅绳' + str(sx), [(x, y, z0), (x + sx * 0.2, y + 0.05, z0 + 0.15)],
                  0.006, M['black_paint'], '标识')

# ---------------------------------------------------------------------------
# notice board, wall stencils, satellite details
# ---------------------------------------------------------------------------
def build_wall_details():
    # central notice board in the 1.6m pier next to the entrance
    bx = -2.82
    add_box('公告栏框', (bx, -6.12, 2.0), (1.5, 0.12, 1.35),
            M['sign_blue'], '标识', bevel=0.015)
    add_box('公告栏面', (bx, -6.19, 2.0), (1.32, 0.03, 1.15),
            M['paper_old'], '标识')
    add_box('公告栏玻璃', (bx, -6.23, 2.0), (1.3, 0.01, 1.13),
            M['notice_glass'], '标识')
    add_text('公告栏题', '社 区 公 告', (bx, -6.245, 2.49), 0.11,
             M['red_paint'], '标识', font=FONT_BOLD)
    for i in range(5):
        px = bx - 0.48 + (i % 3) * 0.47
        pz = 2.22 - (i // 3) * 0.38
        add_box('公告纸' + str(i), (px, -6.225, pz), (0.35, 0.01, 0.28),
                M['paper'], '标识', rot=(0, 0, rand.uniform(-0.05, 0.05)))
        for j in range(3):
            add_box('公告字' + str(i) + str(j), (px, -6.232, pz + 0.08 - j * 0.06),
                    (0.26 - j * 0.035, 0.005, 0.012), M['ink'], '标识')
    # red community plaque
    add_box('文明牌', (-2.82, -6.14, 3.05), (1.3, 0.06, 0.38),
            M['sign_red'], '标识', bevel=0.01)
    add_text('文明牌字', '文 明 楼 院', (-2.82, -6.19, 3.05), 0.18,
             M['gold'], '标识', font=FONT_BOLD)
    # hand-written ads / stencils on the piers
    ads = [
        ('疏通下水道', '138 3702 8815', -3.1, 1.25),
        ('专业开锁', '130 0761 2244', 13.45, 1.55),
        ('回收旧家电', '159 6442 9081', 13.4, 2.02),
    ]
    for i, (a, b, x, z) in enumerate(ads):
        add_text('小广告' + str(i), a, (x, -6.045, z), 0.085, M['red_paint'],
                 '标识', font=FONT_BOLD, rot=(math.pi / 2, 0, 0))
        add_text('小广告电话' + str(i), b, (x, -6.045, z - 0.1), 0.052,
                 M['ink'], '标识', font=FONT_SANS)
    # stencil numbers near door: "3-2"
    add_text('楼栋牌', '3 幢', (17.25, -6.05, 3.3), 0.22, M['white_paint'],
             '标识', font=FONT_BOLD)
    # old fire hose box on the wall
    add_box('消防箱', (13.42, -6.12, 1.05), (0.55, 0.18, 0.85),
            M['sign_red'], '标识', bevel=0.01)
    add_box('消防箱玻璃', (13.42, -6.23, 1.12), (0.4, 0.015, 0.55),
            M['glass_frost'], '标识')
    add_text('消防字', '消火栓', (13.42, -6.245, 1.48), 0.09,
             M['white_paint'], '标识', font=FONT_BOLD)

# ---------------------------------------------------------------------------
# ground-level facade extras
# ---------------------------------------------------------------------------
def build_front_details():
    # gas and water pipes climbing the facade, kept at the bay divisions
    for x in (-13.67, -3.92, 3.92, 13.67):
        add_cyl('立面气管' + str(x), (x, -6.16, 12.3), 0.024, 16.0,
                M['yellow_gas'], '立面设备', vertices=8)
        for z in (5.0, 8.0, 11.0, 14.0, 17.0, 20.0):
            add_box('气管卡' + str(x) + str(z), (x, -6.11, z),
                    (0.09, 0.08, 0.05), M['pipe_gray'], '立面设备')
    # cable bundle draped from the utility pole (the other end is in the street file)
    for k in range(4):
        yoff = -6.28 - k * 0.025
        add_curve('入户电缆' + str(k),
                  catenary((-3.4, yoff, 8.9 + k * 0.10), (2.1, -6.04, 9.6 + k * 0.08),
                           sag=0.45, n=18), 0.012 + 0.003 * k,
                  M['black_paint'], '立面设备', resolution=2)
    # wall-mounted building name plaque at the central bay
    add_box('楼栋铭牌', (3.93, -6.1, 4.7), (0.72, 0.06, 0.3),
            M['white_paint'], '标识', bevel=0.01)
    add_text('楼栋铭牌字', '3 号 楼', (3.93, -6.145, 4.7), 0.13,
             M['ink'], '标识', font=FONT_BOLD)
    # small wall lamp beside the stairs
    for x in (-15.6, 0, 15.6):
        add_box('壁灯座' + str(x), (x + 1.45, -6.14, 3.16), (0.16, 0.15, 0.2),
                M['black_paint'], '立面设备')
    # AC drain stains and a few rust streaks are modelled as thin dark geometry
    for x, z, w in [(-11.5, 9.5, 0.06), (-5.2, 13.4, 0.05), (5.5, 16.0, 0.07),
                    (11.0, 8.4, 0.04)]:
        add_box('墙面水渍' + str(x), (x, -6.015, z), (w, 0.008, 1.8),
                M['moss'], '立面细节')
