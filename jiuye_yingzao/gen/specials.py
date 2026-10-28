# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Special structures that are not a single rectangular timber hall.

Pagodas (refactored from lanxi_map_editor.generators.towers: 楼阁/密檐/望楼, extended with 亭阁/覆钵/砖楼阁),
经幢, 牌坊/乌头门/棂星门, bridges, piers, city wall/gate, yard walls, 照壁, 窑洞, 碉楼, 土楼, 华表, 望楼;
foundations/sites/ruins (台基, 坛, 遗址, 旧码头残桩, 挡土墙, 临水基) live in gen/sites.py;
street fixtures and boats in gen/street.py; 望火楼/水窗/窑 in gen/works.py.
Every generator: (spec dict, rng) -> fills Parts; registered in SPECIALS with defaults and parameter ranges.
"""
import math
import random

import bpy

from ..core import materials, mesh as M, rules as R
from . import parts as P
from .roof import RoofModel
from .building import STYLES, Builder, resolve
from . import sites, street, works


def drum(part, r0, r1, z0, z1, n, mat, rot=0.0):
    vs = [(r * math.cos(math.tau * (i + .5) / n + rot), r * math.sin(math.tau * (i + .5) / n + rot), z) for r, z in ((r0, z0), (r1, z1)) for i in range(n)]
    fs = [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)] + [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    part.add(vs, fs, mat)


def poly_eave(parts, apothem_wall, z, run, rise, n, st, lod, tile='tube', top=False, finial_mat='bronze'):
    """One polygon eave ring (or the top 攒尖 when top=True) sitting against a wall of given apothem."""
    e, f = .7, .4 if st['fly'] else 0.0
    b0 = apothem_wall + run
    if top:
        pts = R.song_juzhe(2 * b0, 2, 'dian'); pts[0] = (0, pts[0][1] * 1.45)
        sec = R.Section(pts, b0, e, f, kick=.06 if st['fly'] else 0); t_in = 0.0; z0 = z
    else:
        s_w = apothem_wall / b0; H = rise / max(1e-3, 1 - s_w)
        sec = R.Section([(0, H), (1, 0)], b0, e, f, kick=.05 if st['fly'] else 0); t_in = apothem_wall / sec.b; z0 = z - rise
    mats = {'tile': st['tile_mat'], 'ridge': st['ridge_mat'], 'timber': st['beam_mat'], 'soffit': 'wood', 'board': st['board_mat'], 'ornament': finial_mat}
    model = RoofModel('cuanjian', b0, b0, z0, sec, e + f, corner_lift=st['corner_lift'] * sec.b * 1.2, sides=n, tile=tile, lod=lod,
                      ridge='plain', ridge_h=.3, flat_t=t_in, materials=mats)
    model.build(parts['Roof'], parts['Roof_timber'], parts['Walls'])
    return model


def finial(part, z, scale=1.0, mat='bronze', rings=7):
    """塔刹: 覆钵 + 相轮 + 宝珠."""
    drum(part, .5 * scale, .55 * scale, z, z + .3 * scale, 12, mat)
    M.tube(part, [(0, 0, z + .3 * scale), (0, 0, z + .55 * scale), (0, 0, z + .75 * scale)], .4 * scale, mat, 12, radii=[.45 * scale, .5 * scale, .2 * scale])
    for k in range(rings):
        zz = z + (.8 + k * .22) * scale; r = (.32 - k * .025) * scale
        drum(part, r, r, zz, zz + .08 * scale, 12, mat)
    M.tube(part, [(0, 0, z + .75 * scale), (0, 0, z + (.85 + rings * .22) * scale)], .05 * scale, mat, 6)
    M.tube(part, [(0, 0, z + (.85 + rings * .22) * scale), (0, 0, z + (1.1 + rings * .22) * scale)], .1 * scale, mat, 10, radii=[.05 * scale, .16 * scale])


# ------------------------------------------------------------------ pagodas
def pagoda_wood(p, sp, st, rng):
    """楼阁式木塔: polygon storeys with 平坐 balconies and an eave per storey (应县木塔 type, simplified)."""
    n = sp['sides']; L = sp['levels']; r = sp['radius']; h = sp['storey_h']; lod = sp['lod']; taper = sp['taper']
    drum(p['Platform'], r + 1.6, r + 1.4, 0, .5, n, 'stone'); drum(p['Platform'], r + 1.4, r + 1.25, .5, 1.1, n, 'stone_light')
    z = 1.1
    for lv in range(L):
        rr = r * (1 - taper * lv / max(1, L - 1)); ap = rr * math.cos(math.pi / n)
        drum(p['Walls'], rr, rr * .99, z, z + h, n, st['wall'] if st['wall'] not in ('earth_rammed', 'adobe') else 'plaster_white')
        for k in range(n):                                   # columns at corners, door on alternate faces
            a = math.tau * (k + .5) / n
            M.column(p['Columns'], (rr + .05) * math.cos(a), (rr + .05) * math.sin(a), z, z + h, .16, st['column']['mat'], 8, .05, 0, (0, 0), False)
            if k % 2 == 0 and lod < 2:
                c = math.tau * (k + 1) / n; st0 = p['Openings'].mark()
                P.door_geyan(p['Openings'], min(1.4, 2 * ap * math.tan(math.pi / n) * .6), h * .7, _om(st), lod, 2)
                p['Openings'].transform(st0, M.place(ap * math.cos(c) + .02 * math.cos(c), ap * math.sin(c) + .02 * math.sin(c), z, c - math.pi / 2 + math.pi))
        top = lv == L - 1
        if not top:
            poly_eave(p, ap, z + h + .05, 1.3, .9, n, st, lod)
            zp = z + h + .45                                 # 平坐 with railing
            drum(p['Beams'], rr + .9, rr + .9, zp - .15, zp, n, 'wood_dark')
            ring = [((rr + .85) * math.cos(math.tau * (k + .5) / n), (rr + .85) * math.sin(math.tau * (k + .5) / n), zp) for k in range(n + 1)]
            P.railing(p['Railings'], ring, .9, st['beam_mat'], lod=lod)
            z = zp
        else:
            m = poly_eave(p, ap, z + h + .05, 1.4, 0, n, st, lod, top=True)
            finial(p['Finial'], m.z(0, 0, 0) + .2, 1.2, rings=7)


def pagoda_dense(p, sp, st, rng):
    """密檐式砖塔: tall 塔身 on a 须弥座, then dense 叠涩 eaves with short gaps (嵩岳寺塔 type: 檐数 != 楼层)."""
    n = sp['sides']; L = sp['levels']; r = sp['radius']; h = sp['storey_h']; taper = sp['taper']
    drum(p['Platform'], r * 1.35, r * 1.3, 0, .8, n, 'stone'); drum(p['Platform'], r * 1.15, r * 1.12, .8, 1.6, n, 'brick_grey')
    body = h * 1.8; z = 1.6
    drum(p['Walls'], r, r * .98, z, z + body, n, 'brick_grey')
    for k in range(0, n, max(1, n // 4)):
        a = math.tau * (k + 1) / n; ap = r * math.cos(math.pi / n)
        M.box(p['Openings'], (ap * math.cos(a), ap * math.sin(a), z + body * .35), (.9, .2, 1.8), 'wood_dark', a + math.pi / 2)
    z += body; gap = h * .32
    for lv in range(L):
        t = lv / max(1, L - 1); rr = r * (1 - taper * (t ** 1.4))           # 卷杀 profile
        for j in range(4):                                                     # 叠涩: corbelled brick courses
            drum(p['Roof'], rr + j * .09, rr + (j + 1) * .09, z + j * .07, z + (j + 1) * .07, n, 'brick_grey')
        drum(p['Roof'], rr + .36, rr * .98, z + .28, z + .42, n, st['tile_mat'])
        drum(p['Walls'], rr * .98, rr * .97, z + .42, z + gap, n, 'brick_grey')
        z += gap
    drum(p['Roof'], r * (1 - taper) + .3, .2, z, z + .9, n, 'brick_grey')
    finial(p['Finial'], z + .9, .9, rings=5)


def pagoda_brick(p, sp, st, rng):
    """楼阁式砖塔: brick storeys with brick-imitation eaves and 平坐 bands, square or octagonal."""
    n = sp['sides']; L = sp['levels']; r = sp['radius']; h = sp['storey_h']; taper = sp['taper']
    drum(p['Platform'], r * 1.3, r * 1.25, 0, 1.0, n, 'stone')
    z = 1.0
    for lv in range(L):
        rr = r * (1 - taper * lv / max(1, L - 1))
        drum(p['Walls'], rr, rr * .99, z, z + h, n, 'brick_grey' if st['wall'] != 'brick_red' else 'brick_red')
        for k in range(0, n, 2):
            a = math.tau * (k + 1) / n; ap = rr * math.cos(math.pi / n)
            M.box(p['Openings'], (ap * math.cos(a), ap * math.sin(a), z + h * .45), (.8, .16, h * .5), 'wood_dark', a + math.pi / 2)
        for j in range(3):
            drum(p['Roof'], rr + j * .12, rr + (j + 1) * .12, z + h + j * .08, z + h + (j + 1) * .08, n, 'brick_grey')
        drum(p['Roof'], rr + .45, rr, z + h + .24, z + h + .5, n, st['tile_mat'])
        z += h + .5
    drum(p['Roof'], r * (1 - taper) + .4, .25, z, z + 1.2, n, st['tile_mat'])
    finial(p['Finial'], z + 1.2, .9, rings=6)


def pagoda_pavilion(p, sp, st, rng):
    """亭阁式塔: single-storey square shrine-tower with stone base and pyramidal roof + 塔刹."""
    r = sp['radius']; h = sp['storey_h'] * 1.3
    M.box_minmax(p['Platform'], (-r - .8, -r - .8, 0), (r + .8, r + .8, 1.0), 'stone_light')
    M.box_minmax(p['Walls'], (-r, -r, 1.0), (r, r, 1.0 + h), 'brick_grey')
    M.box(p['Openings'], (0, -r - .02, 1.0 + h * .4), (1.0, .1, h * .6), 'wood_dark')
    m = poly_eave(p, r, 1.0 + h + .05, .5, 0, 4, st, sp['lod'], top=True)
    finial(p['Finial'], m.z(0, 0, 0) + .2, .8, rings=5)


def pagoda_stupa(p, sp, st, rng):
    """覆钵式塔 (元以后): 须弥座 + 覆钵 dome + 相轮 cone + 华盖."""
    r = sp['radius']
    for k, (a, b, zz) in enumerate([(1.5, 1.45, (0, .6)), (1.2, 1.2, (.6, 1.4)), (1.4, 1.35, (1.4, 1.8))]):
        M.box_minmax(p['Platform'], (-r * a, -r * a, zz[0]), (r * a, r * a, zz[1]), 'stone_light')
    rings = [(r * .9, 1.8), (r * 1.05, 2.3), (r * 1.1, 3.0), (r * 1.0, 3.8), (r * .75, 4.4), (r * .4, 4.7)]
    for (r0, z0), (r1, z1) in zip(rings, rings[1:]):
        drum(p['Walls'], r0, r1, z0, z1, 24, 'plaster_white')
    M.box_minmax(p['Walls'], (-r * .5, -r * .5, 4.7), (r * .5, r * .5, 5.2), 'plaster_white')
    for k in range(13):
        zz = 5.2 + k * .32; rr = r * .42 * (1 - k / 15)
        drum(p['Roof'], rr, rr * .92, zz, zz + .3, 16, 'plaster_white')
    drum(p['Finial'], r * .55, r * .3, 9.4, 9.8, 16, 'bronze')
    finial(p['Finial'], 9.8, .5, rings=2)


def jingchuang(p, sp, st, rng):
    """经幢: octagonal stone pillar on a lotus base with canopies."""
    M.box_minmax(p['Platform'], (-1, -1, 0), (1, 1, .5), 'stone_carved')
    drum(p['Walls'], .75, .55, .5, 1.1, 8, 'stone_carved'); drum(p['Walls'], .32, .3, 1.1, 3.4, 8, 'stone_carved')
    drum(p['Roof'], .7, .35, 3.4, 3.7, 8, 'stone_carved'); drum(p['Walls'], .26, .24, 3.7, 4.5, 8, 'stone_carved')
    drum(p['Roof'], .55, .2, 4.5, 4.8, 8, 'stone_carved'); finial(p['Finial'], 4.8, .35, mat='stone_carved', rings=2)


# ------------------------------------------------------------------ gates
def _bays(n, w0):
    """Bay widths for n openings: 明间 w0, 次间 0.82 w0, 梢间 0.7 w0."""
    ws = [w0 * (1.0 if abs(i - (n - 1) / 2) < .6 else .82 if abs(i - (n - 1) / 2) < 1.6 else .7) for i in range(n)]
    xs = [-sum(ws) / 2]
    for w in ws:
        xs.append(xs[-1] + w)
    return ws, xs


def _post_base(p, x, h, mat, kind):
    """夹杆石 (clamp stones around the post foot) or 抱鼓石 (drum stones front and back)."""
    if kind == 'baogu':
        M.box(p['Platform'], (x, 0, .45), (.6, 1.6, .9), mat)
        for sy in (-1, 1):
            M.tube(p['Platform'], [(x - .14, sy * .75, .95), (x + .14, sy * .75, .95)], .42, mat, 16)
    else:
        M.box(p['Platform'], (x, 0, h * .11), (.78, .78, h * .22), mat)
        M.box(p['Platform'], (x, 0, h * .22 + .05), (.86, .86, .1), mat)


def _beams(p, x0, x1, top, mat, plaque, stone, lod):
    """大额枋 + 花板/折柱 + 小额枋 between two posts, with 雀替 brackets at both ends."""
    w = x1 - x0; xc = (x0 + x1) / 2; bh = .42 if stone else .36
    M.box(p['Beams'], (xc, 0, top - bh / 2), (w, .34, bh), mat)
    M.box(p['Beams'], (xc, 0, top - bh - .62 - bh * .4), (w, .3, bh * .8), mat)
    M.box(p['Openings'], (xc, 0, top - bh - .31), (w - .2, .14, .56), plaque if not stone else mat)       # 花板
    if lod < 2:
        k_n = max(2, int(w / .9))
        for k in range(1, k_n):
            M.box(p['Beams'], (x0 + w * k / k_n, 0, top - bh - .31), (.1, .2, .6), mat)                       # 折柱
        for sx, x in ((1, x0), (-1, x1)):                                                                   # 雀替
            out = [(0, 0), (.7, 0), (.62, -.12), (.3, -.2), (0, -.42)]
            if sx < 0:
                out = list(reversed(out))
            M.extrude_profile(p['Beams'], [(sx * u, v) for u, v in out], .16, mat, M.place(x, 0, top - bh - .62 - bh * .8))


def _lou(p, xc, z, half_w, depth, st, mats, form, lod, lift=.22, dougong=True, dg_mat=None):
    """One 楼: a 斗栱 band on a 平板枋, then a small 庑殿/悬山 roof. Returns the ridge height."""
    if dougong:
        M.box(p['Beams'], (xc, 0, z + .06), (2 * half_w, depth * 1.1, .12), mats['timber'])                 # 平板枋
        n = max(2, int(2 * half_w / .55))
        for k in range(n):
            x = xc - half_w + 2 * half_w * (k + .5) / n
            for ang in (0.0, math.pi):
                P.bracket(p['Brackets'], x, 0, z + .12, ang, 1, .011, dg_mat or mats['timber'], 'song', False, lod)
        z += .12 + P.bracket_height(1, .011, 'song')
    sec = R.Section(R.song_juzhe(2 * depth, 1, 'ting'), depth, .35, .22, kick=.05)
    model = RoofModel(form, half_w, depth, z, sec, .57, corner_lift=lift * sec.b, lod=lod, ridge=mats.get('ridge_kind', 'shoutou'),
                      ridge_h=.28, chuji=.25, materials=mats)
    rp, tp, wp = M.Part('r'), M.Part('t'), M.Part('w'); model.build(rp, tp, wp)
    mt = M.Matrix.Translation((xc, 0, 0)); p['Roof'].extend(rp, mt); p['Roof_timber'].extend(tp, mt)
    return model.z(0, 0, 0) + .3


def paifang(p, sp, st, rng):
    """牌坊 (no 楼): 冲天柱 posts with 云冠/望柱头 caps, two-tier 额枋 with 花板 and a 字牌; stone or timber."""
    n = sp['openings']; h = sp['height']; stone = sp['material'] == 'stone'
    mat = 'stone_carved' if stone else st['column']['mat']; ws, xs = _bays(n, sp['span'])
    for i, x in enumerate(xs):
        top = h * (1.0 if i in (0, n) else 1.08) + 1.1
        M.box(p['Columns'], (x, 0, top / 2), (.46 if stone else .38, .46 if stone else .38, top), mat)
        M.box(p['Roof'], (x, 0, top + .12), (.62, .62, .24), mat)                                             # 云冠 base
        M.tube(p['Roof'], [(x, 0, top + .24), (x, 0, top + .5), (x, 0, top + .72)], .26, mat, 10, radii=[.24, .3, .08])
        _post_base(p, x, h, 'stone' if not stone else 'stone_carved', 'baogu' if stone and n == 1 else 'clamp')
    for i in range(n):
        top = h * (1.12 if (n > 1 and i == n // 2) or n == 1 else 1.0)
        _beams(p, xs[i] + .2, xs[i + 1] - .2, top, mat, 'lacquer_black', stone, sp['lod'])
        if i == n // 2:
            M.box(p['Openings'], ((xs[i] + xs[i + 1]) / 2, -.2, top + .55), (min(1.6, ws[i] * .45), .1, .8), 'lacquer_black' if not stone else 'stone_carved')
            M.box(p['Beams'], ((xs[i] + xs[i + 1]) / 2, 0, top + .15), (ws[i] * .5, .3, .3), mat)


def pailou(p, sp, st, rng):
    """牌楼: roofed archway. n openings carry n main 楼 (明楼 highest, 次楼/梢楼 stepping down); lou='full' adds 夹楼 over the
    inner posts and 边楼 over the outer posts, giving 3/7/11 楼 (一间二柱三楼, 三间四柱七楼, 五间六柱十一楼). chongtian=True keeps
    the posts above the roofs (冲天柱式, 楼 only over the bays). material: wood (戗杆 braces) | stone (stone tiles) | glazed (砖砌琉璃)."""
    n = sp['openings']; h = sp['height']; kind = sp['material']; chong = sp['chongtian']; full = sp['lou'] == 'full' and not chong
    ws, xs = _bays(n, sp['span']); lod = sp['lod']
    if kind == 'stone':
        post = beam = dg = 'stone_carved'
        mats = {'tile': 'stone_carved_dark', 'ridge': 'stone_carved_dark', 'timber': 'stone_carved', 'soffit': 'stone_carved', 'board': 'stone_carved', 'ornament': 'stone_carved_dark'}
    elif kind == 'glazed':
        post = beam = 'plaster_red'; dg = 'glaze_green'; glaze = rng.choice(['glaze_green', 'glaze_green', 'glaze_turquoise', 'glaze_yellow'])
        mats = {'tile': glaze, 'ridge': glaze, 'timber': 'glaze_green', 'soffit': 'glaze_green', 'board': 'glaze_green', 'ornament': glaze}
    else:
        post = st['column']['mat']; beam = st['beam_mat']; dg = beam
        mats = {'tile': st['tile_mat'], 'ridge': st['ridge_mat'], 'timber': 'wood_dark' if beam == post else beam, 'soffit': 'wood', 'board': st['board_mat'], 'ornament': st['ridge_mat']}
    mats['ridge_kind'] = 'chiwei' if st['ridge']['official'] == 'chiwei' else 'shoutou'
    tops = [h * (1.18 if i == n // 2 else 1.0 if abs(i - n // 2) == 1 else .86) if n > 1 else h * 1.1 for i in range(n)]
    if kind != 'glazed':
        for i, x in enumerate(xs):
            adj = [tops[j] for j in (i - 1, i) if 0 <= j < n]; ptop = max(adj) + (2.4 if chong else .2)
            ps = .5 if kind == 'stone' else .4
            M.box(p['Columns'], (x, 0, ptop / 2), (ps, ps, ptop), post)
            if chong:                                                                                         # 云冠
                M.box(p['Roof'], (x, 0, ptop + .1), (.6, .6, .2), post)
                M.tube(p['Roof'], [(x, 0, ptop + .2), (x, 0, ptop + .65)], .26, post, 10, radii=[.28, .1])
            _post_base(p, x, h, 'stone', 'clamp')
            if kind == 'wood':                                                                                # 戗杆
                for sy in (-1, 1):
                    M.beam(p['Beams'], (x, sy * 1.9, 0), (x, sy * .22, h * .58), .14, .14, 'wood_dark')
        for i in range(n):
            _beams(p, xs[i] + .22, xs[i + 1] - .22, tops[i], beam, 'lacquer_black', kind == 'stone', lod)
    else:                                                                                                     # brick body with 券门
        M.box_minmax(p['Platform'], (xs[0] - .8, -.9, 0), (xs[-1] + .8, .9, .6), 'stone_carved')
        for i in range(n):
            x0, x1 = xs[i], xs[i + 1]; aw = (x1 - x0) * (.55 if i == n // 2 else .45); ah = tops[i] * .58; xc = (x0 + x1) / 2
            for a, b in ((x0 - (.5 if i == 0 else 0), xc - aw / 2), (xc + aw / 2, x1 + (.5 if i == n - 1 else 0))):
                M.box_minmax(p['Walls'], (a, -.6, .6), (b, .6, tops[i]), 'plaster_red')
            M.box_minmax(p['Walls'], (xc - aw / 2, -.6, ah + aw / 2), (xc + aw / 2, .6, tops[i]), 'plaster_red')
            seg = 10
            for k in range(seg):
                a0 = math.pi * k / seg; a1 = math.pi * (k + 1) / seg
                xa, za = xc - math.cos(a0) * aw / 2, ah + math.sin(a0) * aw / 2; xb, zb = xc - math.cos(a1) * aw / 2, ah + math.sin(a1) * aw / 2
                M.box_minmax(p['Walls'], (min(xa, xb), -.6, max(za, zb)), (max(xa, xb), .6, ah + aw / 2 + .01), 'plaster_red')
                M.beam(p['Beams'], (xa, -.62, za), (xb, -.62, zb), .1, .14, 'stone_carved')
            M.box_minmax(p['Walls'], (x0, -.62, tops[i] - .9), (x1, .62, tops[i] - .1), 'glaze_green')         # 琉璃额枋 band
    form = 'xuanshan' if chong else 'wudian'
    for i in range(n):
        xc = (xs[i] + xs[i + 1]) / 2; hw = ws[i] / 2 - (.25 if chong else -.15)
        _lou(p, xc, tops[i], hw, .62, st, mats, form, lod, dg_mat=dg)
        if i == n // 2:                                                                                         # 字牌 under the 明楼
            M.box(p['Openings'], (xc, -.36, tops[i] - .25), (min(1.4, ws[i] * .4), .08, .7), 'lacquer_black' if kind != 'stone' else 'stone_carved')
    if full:
        for i, x in enumerate(xs):
            if i in (0, n):                                                                                     # 边楼 over the outer posts
                _lou(p, x, tops[0 if i == 0 else n - 1] - .55, .75, .5, st, mats, 'wudian', lod, dg_mat=dg)
            elif n > 1:                                                                                         # 夹楼 over the inner posts
                _lou(p, x, min(tops[i - 1], tops[i]) + .25, .7, .5, st, mats, 'wudian', lod, dg_mat=dg)


def wutoumen(p, sp, st, rng):
    """乌头门 【原文 卷六】: two tall posts with black caps (乌头), lintel, plank doors; Tang/Song gate of rank."""
    w = sp['span']; h = sp['height']
    for sx in (-1, 1):
        M.box(p['Columns'], (sx * w / 2, 0, h / 2), (.35, .35, h), 'ochre')
        M.box(p['Columns'], (sx * w / 2, 0, h + .35), (.42, .42, .7), 'lacquer_black')
        M.box(p['Platform'], (sx * w / 2, 0, .3), (.9, .9, .6), 'stone')
    M.box(p['Beams'], (0, 0, h * .78), (w + .6, .3, .3), 'ochre')
    st0 = p['Openings'].mark(); P.door_banmen(p['Openings'], w - .4, h * .7, _om(st), sp['lod']); p['Openings'].transform(st0, M.Matrix.Identity(4))
    P.lattice(p['Openings'], 0, h * .74 + .25, w - .5, .4, 'ochre', 'zhiling')


def lingxingmen(p, sp, st, rng):
    """棂星门: three openings, 冲天柱 with cloud caps, lattice transoms (庙学/坛庙)."""
    sp = dict(sp, openings=3, material='stone'); paifang(p, sp, st, rng)


# ------------------------------------------------------------------ bridges / water
def bridge_arch(p, sp, st, rng):
    """石拱桥: 1/3/5 segmental arches, humped deck, railings."""
    n = sp['arches']; span = sp['span']; width = sp['width']; rise = span * .45
    L = n * span + (n - 1) * 1.2; hump = rise * (.5 if n == 1 else .35)
    def deck_z(x):
        return rise + .8 + hump * (1 - (2 * x / (L + 4)) ** 2)
    xs = [-L / 2 + i * (span + 1.2) for i in range(n)]
    for x0 in xs:                                   # arch ring and spandrel
        segs = 12
        for k in range(segs):
            a0 = math.pi * k / segs; a1 = math.pi * (k + 1) / segs
            for a, b in ((a0, a1),):
                xa = x0 + span / 2 - math.cos(a) * span / 2; xb = x0 + span / 2 - math.cos(b) * span / 2
                za = math.sin(a) * rise; zb = math.sin(b) * rise
                for x_, z_ in ((xa, za),):
                    pass
                vs = [(xa, y, za) for y in (-width / 2, width / 2)] + [(xb, y, zb) for y in (-width / 2, width / 2)]
                top_a = deck_z(xa) - .3; top_b = deck_z(xb) - .3
                vs2 = [(xa, -width / 2, za), (xb, -width / 2, zb), (xb, -width / 2, top_b), (xa, -width / 2, top_a)]
                vs3 = [(x, width, z) for x, _, z in vs2]
                quad = vs2 + [(x, width / 2, z) for x, _, z in vs2]
                p['Walls'].add(quad, M.BOX_FACES, 'stone')
    for x0, x1 in [(-L / 2 - 4, xs[0])] + [(xs[i] + span, xs[i + 1]) for i in range(n - 1)] + [(xs[-1] + span, L / 2 + 4)]:
        pts = [(x0, deck_z(x0) - .3), (x1, deck_z(x1) - .3)]
        quad = [(x0, -width / 2, 0), (x1, -width / 2, 0), (x1, -width / 2, pts[1][1]), (x0, -width / 2, pts[0][1])]
        p['Walls'].add(quad + [(x, width / 2, z) for x, _, z in quad], M.BOX_FACES, 'stone')
    deck = [(-L / 2 - 4 + (L + 8) * i / 30) for i in range(31)]
    M.sweep(p['Platform'], [(-width / 2 - .1, -.3), (width / 2 + .1, -.3), (width / 2 + .1, 0), (-width / 2 - .1, 0)], [(x, 0, deck_z(x)) for x in deck], 'paving')
    for sy in (-1, 1):
        rail = [(x, sy * (width / 2), deck_z(x)) for x in deck[::3]]
        P.railing(p['Railings'], rail, .8, 'stone_light', post_every=1.6, lod=sp['lod'])


def bridge_beam(p, sp, st, rng, roofed=False):
    """石梁桥 / 木梁桥 (and 廊桥 when roofed): piers with flat beams."""
    n = sp['arches']; span = sp['span']; width = sp['width']; h = sp.get('deck_h', 2.2); L = n * span
    for i in range(n + 1):
        x = -L / 2 + i * span
        M.box_minmax(p['Walls'], (x - .5, -width / 2 - .4, 0), (x + .5, width / 2 + .4, h - .4), 'stone')
    M.box_minmax(p['Platform'], (-L / 2 - .5, -width / 2, h - .4), (L / 2 + .5, width / 2, h), 'stone_light' if not roofed else 'wood_dark')
    for sy in (-1, 1):
        P.railing(p['Railings'], [(-L / 2, sy * width / 2, h), (L / 2, sy * width / 2, h)], .85, 'stone_light' if not roofed else 'wood_dark', post_every=span / 2, lod=sp['lod'])
    if roofed:                                     # 廊桥: corridor roof over the deck
        spec, stt = resolve('lang', sp['style'], sp['seed'], bays=max(2, int(L / 3)), bay_w=L / max(2, int(L / 3)), jia=2, jia_len=width / 2 + .1, lod=sp['lod'])
        spec['platform_h'] = 0; spec['railing'] = False
        sub = Builder(spec, stt, None); sub.p = p
        z = h
        sub.columns(z, 2.7, True, 0); sub.lintels(z + 2.7, True)
        model = sub.roof(z + 2.75, 0)


def bridge_lang(p, sp, st, rng):
    bridge_beam(p, sp, st, rng, roofed=True)


def pier(p, sp, st, rng):
    """栈桥/码头: timber piles and plank deck reaching into water, with mooring posts (第一回 三座木栈桥)."""
    L = sp['length']; w = sp['width']; h = sp.get('deck_h', 1.6)
    for i in range(int(L / 2.2) + 1):
        y = -i * 2.2
        for sx in (-1, 1):
            M.column(p['Columns'], sx * (w / 2 - .15), y, -1.5, h, .14, 'wood_dark', 8, 0, 0, (0, 0), False)
    M.box_minmax(p['Platform'], (-w / 2, -L, h - .12), (w / 2, 0, h), 'planks')
    for i in range(int(L / 4) + 1):
        M.column(p['Columns'], w / 2 + .1, -i * 4 - 1, h, h + .8, .1, 'wood_dark', 8, 0, 0, (0, 0), False)


# ------------------------------------------------------------------ walls / fortifications
def wall_cap(p, x0, x1, y, z, t, st, double=True):
    M.box_minmax(p['Roof'], (x0, y - t / 2 - .18, z), (x1, y + t / 2 + .18, z + .1), st['tile_mat'])
    if double:
        M.beam(p['Roof'], (x0, y, z + .22), (x1, y, z + .22), .25, .22, st['ridge_mat'])


def yard_wall(p, sp, st, rng):
    """院墙: wall with 下碱, tile coping, and a 随墙门 in the middle."""
    L = sp['length']; h = sp['height']; t = .45; mat = st['wall'] if st['wall'] not in ('plaster_white',) or rng.random() < .5 else 'plaster_white'
    gw = 2.0 if sp.get('gate', True) else 0
    for x0, x1 in ((-L / 2, -gw / 2), (gw / 2, L / 2)) if gw else ((-L / 2, L / 2),):
        M.box_minmax(p['Walls'], (x0, -t / 2, 0), (x1, t / 2, h), mat)
        if st['wall_low_h']:
            M.box_minmax(p['Walls'], (x0, -t / 2 - .03, 0), (x1, t / 2 + .03, min(.9, st['wall_low_h'])), st['wall_low'])
        wall_cap(p, x0, x1, 0, h, t, st)
    if gw:
        for sx in (-1, 1):
            M.box_minmax(p['Walls'], (sx * gw / 2 - .25 if sx > 0 else -gw / 2 - .25, -t, 0), (sx * gw / 2 + .25 if sx > 0 else -gw / 2 + .25, t, h + .6), 'brick_grey')
        M.box_minmax(p['Walls'], (-gw / 2 - .25, -t, h - .1), (gw / 2 + .25, t, h + .6), 'brick_grey')
        wall_cap(p, -gw / 2 - .5, gw / 2 + .5, 0, h + .6, t * 2, st)
        st0 = p['Openings'].mark(); P.door_banmen(p['Openings'], gw - .2, h - .4, _om(st), sp['lod'])


def zhaobi(p, sp, st, rng):
    """照壁: free-standing screen wall with base, framed panel and a small tiled roof."""
    L = sp['length']; h = sp['height']; t = .7
    M.box_minmax(p['Platform'], (-L / 2 - .3, -t / 2 - .3, 0), (L / 2 + .3, t / 2 + .3, .8), 'stone')
    M.box_minmax(p['Walls'], (-L / 2, -t / 2, .8), (L / 2, t / 2, h), 'brick_grey')
    M.box_minmax(p['Openings'], (-L * .35, -t / 2 - .03, 1.4), (L * .35, -t / 2, h - .7), 'plaster_white')
    sec = R.Section([(0, .55), (1, 0)], t / 2 + .2, .3, .15, kick=.04)
    mats = {'tile': st['tile_mat'], 'ridge': st['ridge_mat'], 'timber': 'wood_dark', 'soffit': 'brick_grey', 'board': 'brick_grey'}
    RoofModel('wudian' if L > 4 else 'xuanshan', L / 2 + .1, t / 2 + .2, h, sec, .45, corner_lift=.12, lod=sp['lod'], ridge='raised', ridge_h=.3, chuji=.3, materials=mats).build(p['Roof'], p['Roof_timber'], p['Walls'])


def city_wall(p, sp, st, rng, gate=False):
    """城墙段: battered rammed-earth core with brick facing, 垛口 crenels, 女墙; gate=True adds an arched passage + gate tower."""
    L = sp['length']; h = sp['height']; top_w = sp.get('top_w', 6.0); base_w = top_w + h * .5
    face = 'brick_grey' if sp.get('brick', True) else 'earth_rammed'
    def section(x0, x1):
        vs = [(x, y, z) for x in (x0, x1) for y, z in ((-base_w / 2, 0), (base_w / 2, 0), (top_w / 2, h), (-top_w / 2, h))]
        p['Walls'].add(vs, [(0, 1, 2, 3)[::-1], (4, 5, 6, 7), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], face)
    gw = 5.0 if gate else 0
    if gate:
        section(-L / 2, -gw / 2); section(gw / 2, L / 2)
        ah = min(h * .6, 6.0)
        for x0, x1 in ((-gw / 2 - .1, -gw / 2 + .2), (gw / 2 - .2, gw / 2 + .1)):
            pass
        M.box_minmax(p['Walls'], (-gw / 2, -base_w / 2 + h * .1, ah), (gw / 2, base_w / 2 - h * .1, h), face)
        n = 12
        for k in range(n):
            a0 = math.pi * k / n; a1 = math.pi * (k + 1) / n
            x0, z0 = -math.cos(a0) * gw / 2, ah - gw / 2 + math.sin(a0) * gw / 2; x1, z1 = -math.cos(a1) * gw / 2, ah - gw / 2 + math.sin(a1) * gw / 2
            M.box_minmax(p['Walls'], (min(x0, x1), -base_w / 2 + h * .1, min(z0, z1)), (max(x0, x1), base_w / 2 - h * .1, ah), face)
        st0 = p['Openings'].mark(); P.door_banmen(p['Openings'], gw - .4, ah - gw / 2, _om(st), sp['lod'])
        p['Openings'].transform(st0, M.Matrix.Translation((0, -base_w / 2 + h * .1 + .3, 0)))
    else:
        section(-L / 2, L / 2)
    # 女墙 inside and 垛口 outside
    for x0 in [-L / 2 + i * 1.6 for i in range(int(L / 1.6))]:
        M.box_minmax(p['Walls'], (x0, -top_w / 2, h), (x0 + 1.0, -top_w / 2 + .5, h + 1.6), face)
        M.box_minmax(p['Walls'], (x0 + 1.0, -top_w / 2, h), (x0 + 1.6, -top_w / 2 + .5, h + .9), face)
    M.box_minmax(p['Walls'], (-L / 2, top_w / 2 - .4, h), (L / 2, top_w / 2, h + 1.0), face)
    M.box_minmax(p['Platform'], (-L / 2, -top_w / 2, h - .05), (L / 2, top_w / 2, h + .02), 'paving')
    if gate:                                           # 城门楼 on top
        spec, stt = resolve('zhonglou', sp['style'], sp['seed'], bays=3, lod=sp['lod'])
        spec['base_tower'] = False; spec['platform_h'] = 0.0; spec['railing'] = True
        sub = Builder(spec, stt, None); sub.p = {k: M.Part(k) for k in p}
        sub.build_rect()
        mt = M.Matrix.Translation((0, 0, h + .02))
        for k in p:
            p[k].extend(sub.p[k], mt)


def city_gate(p, sp, st, rng):
    city_wall(p, sp, st, rng, gate=True)


# ------------------------------------------------------------------ dwellings that are not timber halls
def yaodong(p, sp, st, rng):
    """窑洞 (靠崖窑): earth cliff with 2–5 arched cave fronts, timber lattice facades, flat top with parapet."""
    n = sp['caves']; w = 3.4; L = n * (w + 1.2) + 1.2; H = 5.5; Dp = 9.0
    M.box_minmax(p['Walls'], (-L / 2, 0, 0), (L / 2, Dp, H), 'earth_rammed')
    for i in range(n):
        x = -L / 2 + 1.2 + w / 2 + i * (w + 1.2); spring = 2.2
        M.box_minmax(p['Openings'], (x - w / 2, -.05, 0), (x + w / 2, .05, spring), 'wood_dark')
        k = 10
        for j in range(k):
            a0 = math.pi * j / k; a1 = math.pi * (j + 1) / k
            pts = [(x - math.cos(a0) * w / 2, spring + math.sin(a0) * w / 2), (x - math.cos(a1) * w / 2, spring + math.sin(a1) * w / 2)]
            M.box_minmax(p['Openings'], (min(pts[0][0], pts[1][0]), -.05, spring), (max(pts[0][0], pts[1][0]), .05, max(pts[0][1], pts[1][1])), 'paper')
            M.beam(p['Roof_timber'], (pts[0][0], -.1, pts[0][1]), (pts[1][0], -.1, pts[1][1]), .12, .12, 'brick_grey')
        P.lattice(p['Openings'], x, spring + .5, w * .8, 1.0, 'wood_dark', 'grid')
        st0 = p['Openings'].mark(); P.door_banmen(p['Openings'], 1.0, 1.95, _om(st), sp['lod'], studs=False)
        p['Openings'].transform(st0, M.Matrix.Translation((x - w / 4, -.1, 0)))
    M.box_minmax(p['Roof'], (-L / 2, -.4, H), (L / 2, .3, H + .7), 'brick_grey')
    M.box_minmax(p['Platform'], (-L / 2 - 1, -6, -.05), (L / 2 + 1, 0, .05), 'ground_dirt')


def diaolou(p, sp, st, rng):
    """碉楼/望楼: tall square tower, small windows, top gallery and hip or flat roof."""
    a = sp['radius']; L = sp['levels']; h = sp['storey_h']; Htot = L * h
    M.box_minmax(p['Platform'], (-a - .4, -a - .4, 0), (a + .4, a + .4, .5), 'stone')
    M.box_minmax(p['Walls'], (-a, -a, .5), (a, a, .5 + Htot), sp.get('wall', 'brick_grey'))
    for lv in range(L):
        for ang in (0, math.pi / 2, math.pi, -math.pi / 2):
            st0 = p['Openings'].mark(); P.window(p['Openings'], .5, .7, _om(st), 'small', sp['lod'])
            p['Openings'].transform(st0, M.place(math.sin(ang) * a * 0 + 0, 0, .5 + lv * h + h * .5, 0) @ M.Matrix.Translation((0, 0, 0)))
            p['Openings'].transform(st0, M.Matrix.Rotation(ang, 4, 'Z') @ M.Matrix.Translation((0, -a - .02, 0)))
    z = .5 + Htot
    M.box_minmax(p['Beams'], (-a - .7, -a - .7, z), (a + .7, a + .7, z + .25), 'wood_dark')
    P.railing(p['Railings'], [(-a - .65, -a - .65, z + .25), (a + .65, -a - .65, z + .25), (a + .65, a + .65, z + .25), (-a - .65, a + .65, z + .25), (-a - .65, -a - .65, z + .25)], .9, 'wood_dark', lod=sp['lod'])
    for sx in (-1, 1):
        for sy in (-1, 1):
            M.column(p['Columns'], sx * (a + .55), sy * (a + .55), z + .25, z + 2.6, .12, 'wood_dark', 8, 0, 0, (0, 0), False)
    sec = R.Section(R.song_juzhe(2 * a + 1.1, 2, 'ting'), a + .55, .6, .35, kick=.05)
    mats = {'tile': st['tile_mat'], 'ridge': st['ridge_mat'], 'timber': 'wood_dark', 'soffit': 'wood', 'board': st['board_mat']}
    RoofModel('wudian', a + .55, a + .55, z + 2.65, sec, .95, corner_lift=st['corner_lift'] * 2, lod=sp['lod'], ridge='shoutou', ridge_h=.3, materials=mats).build(p['Roof'], p['Roof_timber'], p['Walls'])


def tulou(p, sp, st, rng):
    """土楼 (圆楼/方楼): thick rammed-earth outer ring, inner timber galleries, ring roof, single gate."""
    R0 = sp['radius']; L = sp['levels']; h = 2.9; t = 1.4; ring_d = 6.0; round_ = sp.get('round', True); n = 48 if round_ else 4
    H = L * h
    def ring(r_out, r_in, z0, z1, mat, nn=n):
        rot = 0 if round_ else 0.0
        for k in range(nn):
            a0 = math.tau * (k + .5) / nn; a1 = math.tau * (k + 1.5) / nn
            if not round_:
                pass
            vs = [(r * math.cos(a), r * math.sin(a), z) for z in (z0, z1) for r, a in ((r_out, a0), (r_out, a1), (r_in, a1), (r_in, a0))]
            p['Walls' if mat != 'wood_dark' else 'Beams'].add(vs, M.BOX_FACES, mat)
    rr = R0 if round_ else R0 * 1.41
    ring(rr, rr - t, 0, H, 'earth_rammed')
    ring(rr + .05, rr - t - .05, 0, 1.4, 'stone')
    for lv in range(1, L):                                # inner galleries
        ring(rr - t, rr - ring_d, lv * h - .15, lv * h, 'wood_dark')
        for k in range(0, n, 2 if round_ else 1):
            a = math.tau * (k + .5) / n; r = rr - ring_d + .2
            if lv == L - 1 or True:
                M.column(p['Columns'], r * math.cos(a), r * math.sin(a), (lv - 1) * h, lv * h + h, .1, 'wood_dark', 6, 0, 0, (0, 0), False)
    if round_:
        for k in range(n):
            if k % 3 == 0:
                a = math.tau * (k + 1) / n; z = (L - 1) * h + 1.2
                M.box(p['Openings'], ((rr + .02) * math.cos(a), (rr + .02) * math.sin(a), z), (.5, .1, .7), 'wood_dark', a + math.pi / 2)
    # ring roof: outer slope over the earth wall, inner slope over the gallery
    for k in range(n):
        a0 = math.tau * (k + .5) / n; a1 = math.tau * (k + 1.5) / n
        pts = [(rr + 1.2, H - .3), (rr - ring_d / 2 - .3, H + 2.2), (rr - ring_d - 1.0, H - .2)]
        for (r_a, z_a), (r_b, z_b) in zip(pts, pts[1:]):
            vs = [(r_a * math.cos(a0), r_a * math.sin(a0), z_a), (r_a * math.cos(a1), r_a * math.sin(a1), z_a), (r_b * math.cos(a1), r_b * math.sin(a1), z_b), (r_b * math.cos(a0), r_b * math.sin(a0), z_b)]
            p['Roof'].add(vs + [(x, y, z - .15) for x, y, z in vs], M.BOX_FACES, st['tile_mat'])
    M.box(p['Openings'], (0, -rr - .05, 1.4), (1.8, .3, 2.8), 'wood_dark')
    drum(p['Platform'], rr - ring_d - .5, rr - ring_d - .5, -.02, .05, 24, 'paving')


def huabiao(p, sp, st, rng):
    """华表/旗杆: column with cloud board, capital disc and beast on top (simplified)."""
    h = sp['height']
    M.box_minmax(p['Platform'], (-1, -1, 0), (1, 1, .6), 'stone_carved')
    drum(p['Columns'], .35, .3, .6, h, 8, 'stone_carved')
    M.box(p['Columns'], (0, 0, h * .8), (1.6, .14, .45), 'stone_carved')
    drum(p['Roof'], .7, .7, h, h + .25, 16, 'stone_carved')
    M.box(p['Finial'], (0, 0, h + .6), (.35, .5, .6), 'stone_carved')


def _om(st):
    return {'frame': st['window_mat'], 'door': 'wood_dark', 'paper': st['paper'], 'metal': 'iron', 'stone': 'stone', 'sign': 'lacquer_black', 'lantern': 'cloth_red'}


SPECIALS = {
    'pagoda_wood':   (pagoda_wood,   '塔·楼阁式木塔', '塔', {'sides': [6, 8], 'levels': [3, 7], 'radius': [3.5, 5.5], 'storey_h': [3.6, 4.4], 'taper': [.15, .3]}, ['song', 'liaojin', 'tang', 'daoguan']),
    'pagoda_dense':  (pagoda_dense,  '塔·密檐式砖塔', '塔', {'sides': [4, 12], 'levels': [7, 15], 'radius': [2.6, 4.0], 'storey_h': [3.2, 3.8], 'taper': [.25, .45]}, ['tang', 'song', 'liaojin']),
    'pagoda_brick':  (pagoda_brick,  '塔·楼阁式砖塔', '塔', {'sides': [4, 8], 'levels': [5, 9], 'radius': [2.4, 3.6], 'storey_h': [3.0, 3.6], 'taper': [.2, .35]}, ['song', 'ming', 'lanxi']),
    'pagoda_pavilion': (pagoda_pavilion, '塔·亭阁式', '塔', {'radius': [1.8, 2.6], 'storey_h': [2.8, 3.4]}, ['tang', 'song']),
    'pagoda_stupa':  (pagoda_stupa,  '塔·覆钵式', '塔', {'radius': [2.0, 2.8]}, ['song', 'ming']),
    'jingchuang':    (jingchuang,    '经幢', '塔', {}, ['song', 'tang']),
    'paifang':       (paifang,       '牌坊（冲天柱，无楼）', '门', {'openings': [1, 5], 'span': [2.8, 3.6], 'height': [4.2, 5.6], 'material': ['stone', 'wood']}, ['ming', 'lanxi', 'song']),
    'pailou':        (pailou,        '牌楼（有楼）', '门', {'openings': [1, 5], 'span': [3.2, 4.4], 'height': [4.6, 6.0], 'material': ['wood', 'wood', 'stone', 'glazed'], 'chongtian': [False, False, True], 'lou': ['basic', 'full', 'full']}, ['ming', 'lanxi', 'song', 'daoguan']),
    'wutoumen':      (wutoumen,      '乌头门', '门', {'span': [3.0, 3.8], 'height': [4.0, 5.0]}, ['song', 'tang', 'lanxi']),
    'lingxingmen':   (lingxingmen,   '棂星门', '门', {'span': [2.8, 3.4], 'height': [4.0, 4.8]}, ['ming', 'song']),
    'bridge_arch':   (bridge_arch,   '桥·石拱桥', '桥', {'arches': [1, 3], 'span': [5.0, 8.0], 'width': [3.2, 4.4]}, ['lanxi', 'jiangnan', 'song']),
    'bridge_beam':   (bridge_beam,   '桥·石梁平桥', '桥', {'arches': [3, 6], 'span': [3.0, 4.0], 'width': [2.4, 3.2]}, ['lanxi', 'north_folk']),
    'bridge_lang':   (bridge_lang,   '桥·廊桥', '桥', {'arches': [2, 4], 'span': [4.0, 5.0], 'width': [3.0, 3.6]}, ['ganlan', 'jiangnan', 'chuan']),
    'pier':          (pier,          '码头·木栈桥', '码头', {'length': [12.0, 30.0], 'width': [2.2, 3.4]}, ['lanxi']),
    'yard_wall':     (yard_wall,     '院墙·随墙门', '墙', {'length': [10.0, 20.0], 'height': [2.6, 3.4]}, ['lanxi', 'north_folk', 'hui', 'jiangnan']),
    'zhaobi':        (zhaobi,        '照壁', '墙', {'length': [5.0, 9.0], 'height': [3.4, 4.6]}, ['lanxi', 'ming', 'north_folk']),
    'city_wall':     (city_wall,     '城墙段', '城防', {'length': [20.0, 40.0], 'height': [7.0, 9.0]}, ['lanxi']),
    'city_gate':     (city_gate,     '城门·城楼', '城防', {'length': [30.0, 40.0], 'height': [8.0, 10.0]}, ['lanxi', 'song', 'ming']),
    'yaodong':       (yaodong,       '窑洞', '民居', {'caves': [2, 5]}, ['loess']),
    'diaolou':       (diaolou,       '碉楼/望楼', '城防', {'radius': [2.4, 3.4], 'levels': [3, 5], 'storey_h': [3.0, 3.4]}, ['lanxi', 'lingnan', 'north_folk']),
    'tulou':         (tulou,         '土楼·圆楼', '民居', {'radius': [16.0, 24.0], 'levels': [3, 4]}, ['hakka']),
    'huabiao':       (huabiao,       '华表', '公用', {'height': [6.0, 9.0]}, ['ming', 'song']),
    'taiji':         (sites.taiji,   '台基·平台（无屋身）', '台基', {'width': [8.0, 22.0], 'depth': [6.0, 15.0], 'height': [.5, 1.8], 'kind': ['stone', 'brick', 'diezhe', 'xumi', 'tamped', 'rubble'], 'tiers': [1, 1, 2], 'steps': ['tadao', 'tadao', 'two', 'ruyi', 'mandao', 'brick'], 'balustrade': ['none', 'dan', 'chong'], 'slope': [0.0, 0.0, 0.0, 1.0, 1.8], 'yuetai': [False, False, True], 'bases': [True, True, False]}, ['song', 'tang', 'liaojin', 'ming', 'lanxi', 'north_folk']),
    'tan':           (sites.tan,     '坛（叠涩三层，四出陛）', '台基', {'size': [12.0, 26.0], 'height': [1.5, 2.7], 'shape': ['square', 'square', 'round'], 'balustrade': ['dan', 'dan', 'none'], 'tiers': [3, 3, 3, 2]}, ['song', 'tang', 'ming', 'lanxi']),
    'retaining':     (sites.retaining, '挡土墙·梯台', '台基', {'length': [10.0, 28.0], 'terraces': [1, 4], 'tier_h': [1.0, 2.4], 'step_back': [3.0, 6.0], 'material': ['wall_rubble', 'ashlar_grey', 'stone_block', 'wall_slate_dry', 'ashlar_moss', 'wall_pebble'], 'stair': [True, True, False]}, ['lanxi', 'north_folk', 'chuan', 'hui', 'loess']),
    'linshui':       (sites.linshui, '临水基·石岸码头（马头、两摆手）', '码头', {'length': [14.0, 30.0], 'height': [1.2, 2.4], 'matou': [3.0, 7.0], 'matou_w': [5.0, 10.0], 'steps': ['front', 'side', 'both'], 'decay': [0.0, 0.0, 0.0, .5], 'material': ['ashlar_grey', 'ashlar_moss', 'stone_block', 'wall_rubble']}, ['lanxi', 'song', 'jiangnan']),
    'ruins':         (sites.ruins,   '遗址·残基（旧损/火毁/水毁）', '遗址', {'width': [7.0, 16.0], 'depth': [5.0, 11.0], 'height': [.3, .9], 'decay': [.3, .9], 'cause': ['age', 'fire', 'flood', 'flood'], 'walls': ['brick_grey_old', 'earth_rammed', 'wall_rubble', 'plaster_old']}, ['lanxi', 'song', 'north_folk', 'jiangnan']),
    'pier_ruin':     (sites.pier_ruin, '旧码头残桩', '遗址', {'length': [10.0, 26.0], 'width': [2.2, 3.4], 'decay': [.4, .9]}, ['lanxi']),
    'luli':          (street.luli,   '露篱（版屋篱）', '街巷', {'length': [6.0, 18.0], 'height': [1.9, 3.1], 'bay': [2.5, 3.7], 'infill': ['wattle', 'wattle', 'reed', 'open']}, ['lanxi', 'song', 'north_folk']),
    'zhuzha':        (street.zhuzha, '竹栅', '街巷', {'length': [6.0, 18.0], 'height': [1.4, 3.6], 'pattern': ['dense', 'dense', 'grid']}, ['lanxi', 'ganlan', 'chuan', 'jiangnan']),
    'matai':         (street.matai,  '马台（上马石）', '街巷', {'material': ['stone', 'stone', 'brick'], 'decor': ['su', 'diezhe'], 'post': [False, True]}, ['lanxi', 'song', 'north_folk']),
    'macao':         (street.macao,  '马槽·水槽子', '街巷', {'length': [2.5, 4.5], 'material': ['brick', 'brick', 'stone'], 'fill': ['hay', 'water', 'none'], 'posts': [True, False]}, ['lanxi', 'north_folk', 'song']),
    'jingkou':       (street.jingkou, '井口石·井台（井屋子/辘轳）', '街巷', {'top': ['su', 'fupen', 'lian'], 'lid': [False, True], 'cover': ['none', 'jingwuzi', 'lulu', 'lulu']}, ['lanxi', 'song', 'north_folk']),
    'zao':           (street.zao,    '灶（立灶/釜镬灶/茶炉）', '街巷', {'kind': ['li_zhuanyan', 'li_zhiba', 'fu', 'huo', 'chalu'], 'pot': [1.0, 1.0, 1.2, 1.4], 'chimney': [True, True, False], 'roof_h': [2.8, 3.6]}, ['lanxi', 'north_folk', 'song']),
    'boat':          (street.boat,   '船（渡船/舟/小船）', '码头', {'kind': ['ferry', 'ferry', 'zhou', 'xiao'], 'length': [8.0, 12.0], 'beam': [2.6, 3.4], 'awning': [True, True, False], 'plank': [True, False]}, ['lanxi', 'jiangnan']),
    'wanghuolou':    (works.wanghuolou, '望火楼', '城防', {'height': [7.8, 10.4], 'braces': [True, False], 'rail': [False, True], 'bell': [True, False]}, ['lanxi', 'song', 'north_folk']),
    'shuichuang':    (works.shuichuang, '卷輂水窗（城下/路下过水券洞）', '城防', {'openings': [1, 1, 2, 3], 'span': [2.0, 4.0], 'over': ['wall', 'road', 'none'], 'height': [6.0, 8.5], 'grille': [True, False]}, ['lanxi', 'song']),
    'yao':           (works.yao,     '砖瓦窑（垒造窑）', '作坊', {'scale': [.75, 1.0, 1.0], 'count': [1, 1, 2], 'yard': [True, True, False]}, ['lanxi', 'north_folk', 'song']),
}


def generate(key, style_key=None, seed=0, collection=None, **over):
    fn, label, group, ranges, styles = SPECIALS[key]
    rng = random.Random(seed * 104729 + sum(map(ord, key)))
    if style_key in (None, 'auto'):
        style_key = rng.choice([s for s in styles if not STYLES[s].get('deemphasized')])
    st = STYLES[style_key]
    sp = {'style': style_key, 'seed': seed, 'lod': over.get('lod', 1)}
    for k, r in ranges.items():
        if k in over:
            sp[k] = over[k]
        elif isinstance(r[0], bool) or isinstance(r[0], str) or len(r) > 2:
            sp[k] = rng.choice(r)
        elif isinstance(r[0], int) and isinstance(r[1], int):
            v = rng.randint(r[0], r[1])
            if k == 'sides':
                v = rng.choice([s for s in (4, 6, 8, 12) if r[0] <= s <= r[1]])
            if k in ('openings', 'arches') and key in ('paifang', 'pailou', 'bridge_arch'):
                v = v if v % 2 else v + 1
            sp[k] = v
        else:
            sp[k] = rng.uniform(*r)
    sp.update({k: v for k, v in over.items() if k not in sp})
    col = collection or bpy.context.scene.collection
    root = bpy.data.objects.new(f'{label}_{style_key}_{seed}', None); col.objects.link(root)
    parts = {k: M.Part(k) for k in ('Platform', 'Columns', 'Beams', 'Walls', 'Openings', 'Brackets', 'Roof', 'Roof_timber', 'Railings', 'Props', 'Finial')}
    fn(parts, sp, st, rng)
    mats = materials.library()
    for p in parts.values():
        p.finish(root, col, mats)
    import json
    root['lyz_spec'] = json.dumps({k: v for k, v in sp.items() if isinstance(v, (int, float, str, bool))}, ensure_ascii=False)
    root['lyz_type'] = key; root['lyz_style'] = style_key; root['lyz_tris'] = sum(p.tri_count() for p in parts.values())
    return root
