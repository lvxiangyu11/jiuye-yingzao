# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Compounds (组群): courtyard and axial layouts assembled from single buildings and walls.

Convention: +Y north. A building's front faces -Y before rotation; rotation (radians about Z) turns it:
0 = faces south, pi = north, -pi/2 = west, +pi/2 = east. Layout rules 【推定】 from common northern courtyard
practice: 正房 north facing south, 厢房 east/west facing the yard, 倒座 south facing north, gate in the
south-east (巽位); 衙署/寺观 on a north-south axis (大门→仪门→大堂→二堂→后宅; 山门→钟鼓楼→大殿→后殿).
"""
import json
import math
import random

import bpy

from ..core import materials, mesh as M
from . import building as Bd
from . import specials as Sp


class Layout:
    def __init__(self, name, style, seed, lod, collection):
        self.style = style; self.seed = seed; self.lod = lod; self.k = 0
        self.col = collection or bpy.context.scene.collection
        self.root = bpy.data.objects.new(name, None); self.col.objects.link(self.root)
        self.ground = M.Part('Courtyard_ground'); self.items = []

    def _attach(self, ob, x, y, rot):
        ob.location = (x, y, 0); ob.rotation_euler = (0, 0, rot); ob.parent = self.root; self.items.append(ob)
        return ob

    def bldg(self, t, x, y, rot=0.0, style=None, **over):
        self.k += 1
        ob = Bd.generate(t, style or self.style, self.seed * 31 + self.k, self.col, lod=self.lod, **over)
        return self._attach(ob, x, y, rot)

    def special(self, key, x, y, rot=0.0, style=None, **over):
        self.k += 1
        ob = Sp.generate(key, style or self.style, self.seed * 31 + self.k, self.col, lod=self.lod, **over)
        return self._attach(ob, x, y, rot)

    def wall(self, x0, y0, x1, y1, h=2.8, gate=False):
        L = math.dist((x0, y0), (x1, y1))
        if L < .5:
            return
        ang = math.atan2(y1 - y0, x1 - x0)
        self.special('yard_wall', (x0 + x1) / 2, (y0 + y1) / 2, ang, length=L, height=h, gate=gate)

    def pave(self, x0, y0, x1, y1, mat='paving'):
        M.box_minmax(self.ground, (x0, y0, -.02), (x1, y1, .04), mat)

    def finish(self, kind):
        self.ground.finish(self.root, self.col, materials.library())
        self.root['lyz_type'] = kind; self.root['lyz_style'] = self.style
        self.root['lyz_tris'] = sum(int(o.get('lyz_tris', 0)) for o in self.items) + self.ground.tri_count()
        return self.root


def _wd(lay, t, **over):
    spec, _ = Bd.resolve(t, lay.style, lay.seed * 31 + lay.k + 1, **over)
    return spec['W'], spec['D']


def siheyuan(style='lanxi', seed=0, jin=1, lod=1, collection=None):
    """四合院: jin = 1 (单进), 2 (two yards with 垂花门), 3 (adds 后罩房)."""
    lay = Layout(f'四合院_{jin}进_{style}_{seed}', style, seed, lod, collection)
    Wm, Dm = _wd(lay, 'zhengfang', bays=3)
    Ww, Dw = _wd(lay, 'xiangfang', bays=3)
    cw = max(6.5, Wm * .8); cl = Ww + 2.5
    ym = cl / 2 + Dm / 2 + 1.0
    lay.bldg('zhengfang', 0, ym, 0.0, bays=3)
    for sx, rot in ((1, -math.pi / 2), (-1, math.pi / 2)):
        lay.bldg('xiangfang', sx * (cw / 2 + Dw / 2 + .6), 0, rot, bays=3)
    lay.pave(-cw / 2, -cl / 2, cw / 2, cl / 2)
    half_x = cw / 2 + Dw + 1.2; y_front = -cl / 2
    if jin >= 2:                                         # 垂花门 between the outer and inner yard
        lay.bldg('chuihuamen', 0, y_front - .3, 0.0)
        lay.wall(-half_x, y_front, -1.8, y_front); lay.wall(1.8, y_front, half_x, y_front)
        y_front -= 5.5
        lay.pave(-half_x + .5, y_front, half_x - .5, y_front + 5.2, 'paving')
    Wd, Dd = _wd(lay, 'daozuo', bays=4)
    yd = y_front - Dd / 2 - .8
    lay.bldg('daozuo', -2.0, yd, math.pi, bays=4)
    lay.bldg('menwu', half_x - 2.2, yd, 0.0, bays=1)       # 大门 at the south-east
    y_back = ym + Dm / 2 + 1.2
    if jin >= 3:                                         # 后罩房
        Wh, Dh = _wd(lay, 'xiangfang', bays=5)
        lay.bldg('xiangfang', 0, y_back + Dh / 2 + 2.0, 0.0, bays=5)
        y_back += Dh + 3.0
    y_s = yd - Dd / 2 - .3
    lay.wall(-half_x, y_s, -half_x, y_back); lay.wall(half_x, y_s, half_x, y_back); lay.wall(-half_x, y_back, half_x, y_back)
    return lay.finish('siheyuan')


def sanheyuan(style='north_folk', seed=0, lod=1, collection=None):
    """三合院: 正房 + two 厢房, front closed by a wall with a gate."""
    lay = Layout(f'三合院_{style}_{seed}', style, seed, lod, collection)
    Wm, Dm = _wd(lay, 'zhengfang'); Ww, Dw = _wd(lay, 'xiangfang')
    cw = max(6.0, Wm * .75); cl = Ww + 2.0
    lay.bldg('zhengfang', 0, cl / 2 + Dm / 2 + .8, 0.0)
    for sx, rot in ((1, -math.pi / 2), (-1, math.pi / 2)):
        lay.bldg('xiangfang', sx * (cw / 2 + Dw / 2 + .5), 0, rot)
    hx = cw / 2 + Dw + 1.0; yb = cl / 2 + Dm + 1.6; yf = -cl / 2 - 1.0
    lay.wall(-hx, yf, hx, yf, gate=True); lay.wall(-hx, yf, -hx, yb); lay.wall(hx, yf, hx, yb); lay.wall(-hx, yb, hx, yb)
    lay.pave(-cw / 2, -cl / 2, cw / 2, cl / 2, 'ground_dirt')
    return lay.finish('sanheyuan')


def tianjing(style='hui', seed=0, lod=1, collection=None):
    """天井院 (南方): two-storey front and back ranges around a narrow 天井, high side walls."""
    lay = Layout(f'天井院_{style}_{seed}', style, seed, lod, collection)
    W, D = _wd(lay, 'loufang', bays=3)
    tj = 3.2
    lay.bldg('loufang', 0, tj / 2 + D / 2, 0.0, bays=3)
    lay.bldg('loufang', 0, -tj / 2 - D / 2, math.pi, bays=3)
    for sx in (-1, 1):
        lay.wall(sx * (W / 2 + .3), -tj / 2 - .2, sx * (W / 2 + .3), tj / 2 + .2, h=6.5)
    lay.pave(-W / 2, -tj / 2, W / 2, tj / 2, 'stone')
    return lay.finish('tianjing')


def shop_house(style='lanxi', seed=0, lod=1, collection=None):
    """前店后宅: street shop, back yard, rear house, side walls."""
    lay = Layout(f'前店后宅_{style}_{seed}', style, seed, lod, collection)
    Ws, Ds = _wd(lay, 'shop'); Wh, Dh = _wd(lay, 'zhengfang', bays=3)
    yard = 5.0; W = max(Ws, Wh) + 1.0
    lay.bldg('shop', 0, -yard / 2 - Ds / 2, 0.0)
    lay.bldg('zhengfang', 0, yard / 2 + Dh / 2, 0.0, bays=3)
    for sx in (-1, 1):
        lay.wall(sx * W / 2, -yard / 2, sx * W / 2, yard / 2)
    lay.pave(-W / 2 + .3, -yard / 2, W / 2 - .3, yard / 2, 'ground_dirt')
    return lay.finish('shop_house')


def yamen(style='lanxi', seed=0, lod=1, collection=None):
    """衙署 (县衙): 照壁, 大门, 仪门, 大堂 with 吏房 rows, 二堂, 后宅 on one axis."""
    lay = Layout(f'县衙_{style}_{seed}', style, seed, lod, collection)
    y = 0.0
    lay.special('zhaobi', 0, y - 8, 0.0, length=10.0)
    lay.bldg('menwu', 0, y, 0.0, bays=3); y += 14
    lay.bldg('menwu', 0, y, 0.0, bays=3); y += 6
    W1, D1 = _wd(lay, 'xiangfang', bays=6)
    for sx, rot in ((1, -math.pi / 2), (-1, math.pi / 2)):
        lay.bldg('xiangfang', sx * 11, y + W1 / 2 + 2, rot, bays=6)
    W2, D2 = _wd(lay, 'yamen'); yh = y + W1 + 5 + D2 / 2
    lay.bldg('yamen', 0, yh, 0.0); y = yh + D2 / 2 + 6
    W3, D3 = _wd(lay, 'tingtang'); lay.bldg('tingtang', 0, y + D3 / 2, 0.0); y += D3 + 6
    W4, D4 = _wd(lay, 'zhengfang', bays=5); lay.bldg('zhengfang', 0, y + D4 / 2, 0.0, bays=5); y += D4 + 2
    hx = 16
    lay.wall(-hx, -2, -hx, y); lay.wall(hx, -2, hx, y); lay.wall(-hx, y, hx, y)
    lay.wall(-hx, -2, -4, -2); lay.wall(4, -2, hx, -2)
    lay.pave(-3, -6, 3, y - 2)
    return lay.finish('yamen')


def temple(style='song', seed=0, lod=1, collection=None, main='miaodian'):
    """寺观/城隍庙: 山门, 钟楼 + 鼓楼, 配殿, 大殿, 后殿 on one axis."""
    lay = Layout(f'庙观_{style}_{seed}', style, seed, lod, collection)
    lay.bldg('menwu', 0, 0, 0.0, bays=3)
    y = 9.0
    for sx in (-1, 1):
        lay.bldg('zhonglou', sx * 9, y + 2, 0.0, platform_h=3.0)
    W, D = _wd(lay, 'xiangfang', bays=3)
    for sx, rot in ((1, -math.pi / 2), (-1, math.pi / 2)):
        lay.bldg('xiangfang', sx * 11, y + 14, rot, bays=3)
    Wm, Dm = _wd(lay, main); ym = y + 22 + Dm / 2
    lay.bldg(main, 0, ym, 0.0)
    yb = ym + Dm / 2 + 10
    Wb, Db = _wd(lay, 'tingtang'); lay.bldg('tingtang', 0, yb + Db / 2, 0.0)
    ye = yb + Db + 3; hx = max(16, Wm / 2 + 8)
    lay.wall(-hx, -2, -hx, ye); lay.wall(hx, -2, hx, ye); lay.wall(-hx, ye, hx, ye)
    lay.wall(-hx, -2, -5, -2); lay.wall(5, -2, hx, -2)
    lay.pave(-3, -2, 3, ym - Dm / 2)
    return lay.finish('temple')


def yizhan(style='lanxi', seed=0, lod=1, collection=None):
    """驿站: gate, 正房 with sign, stable shed, side rooms, wall."""
    lay = Layout(f'驿站_{style}_{seed}', style, seed, lod, collection)
    Wm, Dm = _wd(lay, 'yizhan'); lay.bldg('yizhan', 0, 10 + Dm / 2, 0.0)
    lay.bldg('huopeng', -9, 2, math.pi / 2)
    lay.bldg('xiangfang', 9, 2, -math.pi / 2)
    lay.bldg('menwu', 0, -6, 0.0, bays=1)
    hx = 14; yb = 10 + Dm + 2
    lay.wall(-hx, -6, -2.5, -6); lay.wall(2.5, -6, hx, -6); lay.wall(-hx, -6, -hx, yb); lay.wall(hx, -6, hx, yb); lay.wall(-hx, yb, hx, yb)
    lay.pave(-hx + .5, -5.5, hx - .5, 9, 'ground_dirt')
    return lay.finish('yizhan')


def farm(style='north_folk', seed=0, lod=1, collection=None):
    """农家院: 茅屋 or 正房, shed, well, low earth wall."""
    lay = Layout(f'农家院_{style}_{seed}', style, seed, lod, collection)
    rng = random.Random(seed)
    W, D = _wd(lay, 'maowu')
    lay.bldg('maowu', 0, 3 + D / 2, 0.0)
    lay.bldg('chapeng', -6, -1, math.pi / 2, roof='danpo')
    lay.bldg('jingting', 4, -2, 0.0)
    lay.wall(-9, -6, -1.5, -6, h=1.8); lay.wall(1.5, -6, 9, -6, h=1.8); lay.wall(-9, -6, -9, 3 + D + 1, h=1.8); lay.wall(9, -6, 9, 3 + D + 1, h=1.8)
    lay.pave(-8.5, -5.5, 8.5, 3, 'ground_dirt')
    return lay.finish('farm')


COMPOUNDS = {
    'siheyuan1': (lambda **k: siheyuan(jin=1, **k), '四合院·一进', ['lanxi', 'north_folk', 'ming']),
    'siheyuan2': (lambda **k: siheyuan(jin=2, **k), '四合院·二进', ['lanxi', 'north_folk', 'ming']),
    'siheyuan3': (lambda **k: siheyuan(jin=3, **k), '四合院·三进', ['lanxi', 'ming']),
    'sanheyuan': (sanheyuan, '三合院', ['north_folk', 'lanxi', 'chuan']),
    'tianjing':  (tianjing, '天井院', ['hui', 'jiangnan', 'lingnan', 'minnan']),
    'shop_house': (shop_house, '前店后宅', ['lanxi', 'jiangnan', 'north_folk']),
    'yamen_c':   (yamen, '衙署（县衙）', ['lanxi', 'song', 'ming']),
    'temple':    (temple, '庙观（城隍庙/道观）', ['song', 'lanxi', 'daoguan', 'ming']),
    'yizhan_c':  (yizhan, '驿站', ['lanxi', 'north_folk']),
    'farm':      (farm, '农家院', ['north_folk', 'lanxi', 'loess']),
}


def generate(key, style_key=None, seed=0, collection=None, lod=1, **_):
    fn, label, styles = COMPOUNDS[key]
    if style_key in (None, 'auto'):
        style_key = random.Random(seed).choice(styles)
    return fn(style=style_key, seed=seed, lod=lod, collection=collection)
