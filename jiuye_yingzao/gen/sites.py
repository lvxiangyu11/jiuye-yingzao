# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Standalone foundations, sites and ruins: 台基/平台, 坛, 遗址残基, 旧码头残桩, 挡土墙/梯台, 临水基/石岸码头.

Rules 【原文】 《营造法式》:
  卷十五 坛: 共三层, 高广以石段层数, 自土衬上至平面为高; 每头子各露明五寸, 束腰露一尺, 格身版柱造
  卷三 筑临水基: 开深一丈八尺, 广随屋间数之广; 其外分作两摆手, 斜随马头; 布柴梢令厚一丈五尺;
       每岸长五尺钉桩一条, 长一丈七尺, 径五寸至六寸皆可用; 梢上用胶土打筑令实; 若造桥两岸马头准此
  卷十五 砖墙: 每高一尺底广五寸, 每面斜收一寸 (收分 10%, used for retaining walls)
Platform mouldings, steps and 钩阑 come from gen/foundation.py. Other values 【推定】.
Frame: front / water side at -Y, Z up. Ground = z 0; for pier_ruin and linshui z 0 is the water level.
"""
import math

from ..core import mesh as M
from . import foundation as FD
from .building import FOUND_MATS, COLUMN_BASE


def _fmats(kind, rng, body=None, cap=None):
    bodies, caps = FOUND_MATS.get(kind, (['stone'], ['stone_carved']))
    b = body or rng.choice(bodies); c = cap or rng.choice(caps)
    return {'body': b, 'cap': c, 'soil': 'stone', 'waist': 'stone_carved_dark' if kind in ('diezhe', 'xumi') else b,
            'step': c, 'rail': 'stone_carved', 'apron': 'paving', 'retain': 'wall_rubble', 'joint': 'stone'}


def offset_poly(pts, d):
    """Offset a convex counter-clockwise XY polygon outward by d (negative = inward)."""
    out = []; n = len(pts)
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        n1 = _normal(a, b); n2 = _normal(b, c); s = 1 + n1[0] * n2[0] + n1[1] * n2[1]
        out.append((b[0] + (n1[0] + n2[0]) / s * d, b[1] + (n1[1] + n2[1]) / s * d))
    return out


def _normal(p, q):
    dx, dy = q[0] - p[0], q[1] - p[1]; l = math.hypot(dx, dy) or 1.0
    return dy / l, -dx / l


def poly_batter(part, top, z0, z1, bat, mat):
    """Solid with a convex top outline at z1 whose sides lean out by bat at z0 (收分 masonry)."""
    bot = offset_poly(top, bat); n = len(top)
    vs = [(x, y, z0) for x, y in bot] + [(x, y, z1) for x, y in top]
    fs = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    part.add(vs, fs, mat)


def batter_wall(part, x0, x1, y, z0, z1, depth, bat, mat):
    """Straight retaining wall facing -Y: face at y at the foot, leaning back by bat at the top, depth thick."""
    vs = [(x0, y, z0), (x1, y, z0), (x1, y + depth, z0), (x0, y + depth, z0),
          (x0, y + bat, z1), (x1, y + bat, z1), (x1, y + depth, z1), (x0, y + depth, z1)]
    part.add(vs, M.BOX_FACES, mat)


def rot_z(q):
    return M.Matrix.Rotation(q, 4, 'Z')


def rubble(part, rng, cx, cy, z, radius, count, mats, size=(.25, .5), height=.6):
    """Heap of loose blocks (collapsed wall): random boxes, higher towards the centre."""
    for _ in range(count):
        a = rng.uniform(0, math.tau); d = radius * math.sqrt(rng.random())
        s = rng.uniform(*size); zz = z + max(0.0, height * (1 - d / radius)) * rng.uniform(.3, 1.0)
        M.box(part, (cx + math.cos(a) * d, cy + math.sin(a) * d, zz + s * .2), (s, s * rng.uniform(.45, .8), s * rng.uniform(.3, .55)), rng.choice(mats), rng.uniform(0, math.pi))


# ------------------------------------------------------------------ 台基 / 平台
def taiji(p, sp, st, rng):
    """Free-standing platform: any foundation kind, tiers, 月台, steps, 钩阑, slope retaining; optional 柱础 grid (ready for a hall or as a site)."""
    W, D, H, kind = sp['width'], sp['depth'], sp['height'], sp['kind']; mg = .6
    F = FD.Foundation(p, _fmats(kind, rng), sp['lod'], rng)
    yt = (W * .6, max(3.0, D * .4), min(.35, H * .3)) if sp['yuetai'] else None
    top = F.platform(W - 2 * mg, D - 2 * mg, H, kind, mg, tiers=sp['tiers'], yuetai=yt, steps=sp['steps'], side_steps=sp.get('side_steps', False),
                     balustrade=sp['balustrade'], slope=sp['slope'], chishou=kind in ('diezhe', 'xumi') and H >= 1.0)
    P = p['Platform']
    M.box_minmax(P, (-W / 2 + mg + .2, -D / 2 + mg + .2, top), (W / 2 - mg - .2, D / 2 - mg - .2, top + .012), 'paving')     # 地面石
    if sp['bases']:
        nb = max(3, round((W - 2 * mg) / 3.8)) | 1; nj = max(2, round((D - 2 * mg) / 3.0))
        kb = COLUMN_BASE.get(sp['style'], 'fupen')
        for i in range(nb + 1):
            for j in range(nj + 1):
                FD.column_base(P, -W / 2 + mg + (W - 2 * mg) * i / nb, -D / 2 + mg + (D - 2 * mg) * j / nj, top, .22, kb, 'stone_carved', sp['lod'])
    sp['top'] = round(top, 3)


# ------------------------------------------------------------------ 坛
def tan(p, sp, st, rng):
    """坛: square or round altar of 2–3 叠涩 tiers (头子五寸, 束腰一尺), 四出陛 on every tier, optional 钩阑 and 天心石."""
    S, H, n, shape = sp['size'], sp['height'], sp['tiers'], sp['shape']
    h = H / n; sb = max(1.6, 2 * h + .7)                         # set-back holds one flight (每阶高一尺作二踏)
    S = max(S, 2 * (2.6 + (n - 1) * sb))
    F = FD.Foundation(p, _fmats('diezhe', rng, body='stone_carved'), sp['lod'], rng); P = p['Platform']
    z = 0.0; kind = sp['balustrade']
    for k in range(n):
        r = S / 2 - k * sb; zt = z + h; sw = min(3.0, max(1.6, r * .3))
        if shape == 'round':
            for a, b, i0, i1, role in FD.profile('diezhe', h):
                M.tube(P, [(0, 0, z + a), (0, 0, z + b)], r, F.mat(role), 40, True, False, radii=[r - i0, r - i1])
        else:
            F.block(r, r, z, h, 'diezhe')
        for q in range(4):                                       # 四出陛
            m = P.mark(); F.steps(0, -r, sw, zt, z, 'tadao'); P.transform(m, rot_z(q * math.pi / 2))
        if kind != 'none':
            if shape == 'round':
                rr = r - .15; g = (sw / 2 + .35) / rr
                for q in range(4):
                    a0 = -math.pi / 2 + q * math.pi / 2 + g; a1 = a0 + math.pi / 2 - 2 * g; m_ = max(2, math.ceil(rr * (a1 - a0) / 1.9))
                    F.balustrade([(rr * math.cos(a0 + (a1 - a0) * t / m_), rr * math.sin(a0 + (a1 - a0) * t / m_), zt) for t in range(m_ + 1)], zt, kind)
            else:
                for q in range(4):
                    m = p['Railings'].mark(); e = r - .12
                    F.balustrade([(-e, -e, zt), (e, -e, zt)], zt, kind, gaps=[(-sw / 2 - .3, sw / 2 + .3, -e)])
                    p['Railings'].transform(m, rot_z(q * math.pi / 2))
        z = zt
    M.tube(P, [(0, 0, z), (0, 0, z + .015)], .7, 'stone_carved_dark', 24)       # 天心石
    sp['size'] = round(S, 2)


# ------------------------------------------------------------------ 遗址残基
def ruins(p, sp, st, rng):
    """Ruined house site: platform, scattered 柱础 with stumps, broken wall runs, fallen timbers, rubble and tile shards.
    cause: age | fire (charred stumps, ash) | flood (silt, posts leaning downstream, driftwood, upstream wall washed out)."""
    W, D, H, dec, cause, wm = sp['width'], sp['depth'], sp['height'], sp['decay'], sp['cause'], sp['walls']
    kind = rng.choice(['stone', 'rubble', 'tamped'] if cause == 'flood' else ['stone', 'brick', 'tamped'])
    F = FD.Foundation(p, _fmats(kind, rng, body='ashlar_moss' if kind == 'stone' and rng.random() < .6 else None), sp['lod'], rng)
    top = F.platform(W, D, H, kind, .5, steps='tadao' if rng.random() < .7 else 'none', sanshui=False)
    P = p['Platform']; flow = rng.choice([-1, 1])               # flood runs along ±X
    timber = 'lacquer_black' if cause == 'fire' else 'wood_dark'
    nb = max(3, round(W / 3.4)); nj = max(2, round(D / 3.0))
    for i in range(nb + 1):                                      # 柱础 and stumps
        for j in range(nj + 1):
            x = -W / 2 + W * i / nb; y = -D / 2 + D * j / nj
            if rng.random() < dec * .25:
                continue
            z = FD.column_base(P, x, y, top, .19, rng.choice(['su', 'fupen', 'gu']), 'stone_carved', sp['lod'])
            if rng.random() < .6 - dec * .35:
                hh = rng.uniform(.15, 2.4 * (1 - dec * .6))
                lean = (flow * rng.uniform(.05, .3) * hh, rng.uniform(-.04, .04) * hh) if cause == 'flood' else (rng.uniform(-.05, .05) * hh, rng.uniform(-.05, .05) * hh)
                M.column(p['Columns'], x, y, z, z + hh, .17, timber, 10, .04, 0, lean)
    t = .42 if wm in ('earth_rammed', 'wall_rubble') else .3; h0 = 3.0
    runs = [((-W / 2, D / 2), (W / 2, D / 2), False), ((-W / 2, -D / 2), (-W / 2, D / 2), flow > 0), ((W / 2, -D / 2), (W / 2, D / 2), flow < 0),
            ((-W / 2, -D / 2), (-W * .2, -D / 2), False), ((W * .2, -D / 2), (W / 2, -D / 2), False)]
    for (ax, ay), (bx, by), upstream in runs:                    # broken wall runs: random-walk top line, gaps
        L = math.hypot(bx - ax, by - ay); n = max(1, int(L / .45)); hc = h0 * (1 - dec * rng.uniform(.3, .8))
        loss = dec * (.95 if upstream and cause == 'flood' else .4); gap = rng.random() < loss
        for k in range(n):                                       # breaches come in runs (two-state chain, mean gap ~3 pieces)
            hc = min(h0, max(.12, hc + rng.uniform(-.3, .27) * (1 + dec)))
            gap = rng.random() < (.66 if gap else loss * .3)
            if gap:
                continue
            t0, t1 = k / n, (k + 1) / n; hh = hc * (.25 if upstream and cause == 'flood' else 1)
            M.beam(p['Walls'], (ax + (bx - ax) * t0, ay + (by - ay) * t0, top + hh / 2), (ax + (bx - ax) * t1, ay + (by - ay) * t1, top + hh / 2), t, hh, wm)
        for _ in range(max(1, round(dec * L / 4))):              # rubble at the wall foot, spilling outward
            u = rng.random(); cx, cy = ax + (bx - ax) * u, ay + (by - ay) * u
            nx, ny = _normal((ax, ay), (bx, by))
            if ay == by and ay > 0 or ax == bx and ax < 0:
                nx, ny = -nx, -ny
            out = rng.uniform(-.2, 1.2)
            zr = top if abs(cx + nx * out) < W / 2 + .4 and abs(cy + ny * out) < D / 2 + .4 else 0.0
            mats = [wm, 'brick_grey_old'] if wm.startswith('brick') else [wm, 'stone']
            rubble(P, rng, cx + nx * out, cy + ny * out, zr, rng.uniform(.8, 1.6), int(12 + 20 * dec), mats, height=.5 + dec * .5)
    for _ in range(int(3 + dec * 7)):                            # fallen beams / purlins
        x0 = rng.uniform(-W / 2, W / 2); y0 = rng.uniform(-D / 2, D / 2); a = rng.uniform(0, math.tau); L = rng.uniform(2.4, 4.6)
        if cause == 'flood':
            x0 = flow * rng.uniform(0, W / 2 + 2); a = rng.uniform(-.5, .5) + (math.pi / 2 if rng.random() < .5 else 0)
        x1, y1 = x0 + math.cos(a) * L, y0 + math.sin(a) * L
        z0 = top + .12 if abs(x0) < W / 2 + .5 and abs(y0) < D / 2 + .5 else .12
        z1 = top + .12 if abs(x1) < W / 2 + .5 and abs(y1) < D / 2 + .5 else .12
        M.beam(p['Beams'], (x0, y0, z0), (x1, y1, z1), .22, .24, timber)
    for _ in range(int(40 + 60 * dec)):                          # tile shards
        M.box(p['Roof'], (rng.uniform(-W / 2, W / 2), rng.uniform(-D / 2, D / 2), top + .02), (.24, .2, .018), rng.choice(['tile_grey_old', 'tile_grey']), rng.uniform(0, math.pi))
    if cause == 'flood':                                         # silt sheets and driftwood on the downstream side
        for _ in range(int(5 + 6 * dec)):
            cx = rng.uniform(-W / 2, W / 2) * .8 + flow * rng.uniform(0, 2); cy = rng.uniform(-D / 2, D / 2) * .8
            zz = top if abs(cx) < W / 2 and abs(cy) < D / 2 else 0.0
            M.box(P, (cx, cy, zz + .03), (rng.uniform(1.5, 3.5), rng.uniform(1.0, 2.5), .08), 'ground_dirt', rng.uniform(0, math.pi))
        for _ in range(int(4 + 6 * dec)):
            x0 = flow * (W / 2 + rng.uniform(.3, 3)); y0 = rng.uniform(-D / 2 - 1, D / 2 + 1); a = rng.uniform(0, math.tau); L = rng.uniform(1.5, 4)
            M.tube(p['Props'], [(x0, y0, .1), (x0 + math.cos(a) * L, y0 + math.sin(a) * L, .1 + rng.uniform(0, .3))], rng.uniform(.06, .14), 'wood_dark', 6)
    elif cause == 'fire':
        for _ in range(int(4 + 5 * dec)):
            M.box(P, (rng.uniform(-W / 2, W / 2), rng.uniform(-D / 2, D / 2), top + .02), (rng.uniform(1, 2.5), rng.uniform(.8, 2), .03), 'tile_black', rng.uniform(0, math.pi))


# ------------------------------------------------------------------ 旧码头残桩
def pier_ruin(p, sp, st, rng):
    """Old pier remains: broken and leaning piles, stringer and plank fragments near the shore, a slumped stone abutment and mooring stone (z 0 = water)."""
    L, w, dec = sp['length'], sp['width'], sp['decay']; h = 1.6; bed = -1.6
    G = p['Platform']; C = p['Columns']
    M.box_minmax(G, (-w / 2 - .9, 0, bed), (w / 2 + .9, 3.2, h - .1), 'ashlar_moss')          # 岸墩
    for _ in range(int(3 + 8 * dec)):                            # slumped blocks at the abutment foot
        M.box(G, (rng.uniform(-w / 2 - .8, w / 2 + .8), rng.uniform(-1.4, -.1), rng.uniform(-.35, .15)), (rng.uniform(.5, .9), .45, .35), 'ashlar_moss', rng.uniform(-.4, .4))
    for k in range(int(4 * (1 - dec)) + 2):                      # coping stones, some missing
        if rng.random() > dec * .6:
            M.box(G, (-w / 2 - .9 + (w + 1.8) * (k + .5) / (int(4 * (1 - dec)) + 2), .25, h - .02), ((w + 1.8) / (int(4 * (1 - dec)) + 2) - .03, .5, .16), 'stone_carved_dark')
    M.tube(G, [(w / 2 + .5, 2.0, h - .1), (w / 2 + .5, 2.0, h + .35)], .17, 'stone_carved_dark', 10)   # 系船石
    n = int(L / 2.2) + 1; tops = {}
    for i in range(n):
        y = -.3 - i * 2.2; far = i / max(1, n - 1)
        for sx in (-1, 1):
            if rng.random() < dec * (.25 + .4 * far):
                continue
            tz = h - rng.uniform(0, 1) * (dec * 1.4 + far * 1.0)
            tz = max(-.15, tz); lean = (rng.uniform(-.12, .12) * (1 + dec), rng.uniform(-.1, .1) * (1 + dec))
            M.column(C, sx * (w / 2 - .15), y, bed, tz, .14 * rng.uniform(.8, 1.05), 'wood_dark', 8, .1 * rng.random(), 0, lean)
            tops[(i, sx)] = tz
    reach = L * (1 - dec) * rng.uniform(.35, .8)                 # surviving deck near the shore
    for i in range(n - 1):
        y0, y1 = -.3 - i * 2.2, -.3 - (i + 1) * 2.2
        for sx in (-1, 1):                                       # stringers between surviving pile heads
            if tops.get((i, sx), -9) > h - .35 and tops.get((i + 1, sx), -9) > h - .35 and rng.random() > dec * .5:
                M.beam(p['Beams'], (sx * (w / 2 - .15), y0, h - .2), (sx * (w / 2 - .15), y1, h - .2), .16, .2, 'wood_dark')
    y = 0.0
    while y > -reach:
        y -= .3
        if rng.random() < dec * .35 + (-y / max(reach, .1)) * .3:
            continue
        drop = rng.uniform(.0, .7) if rng.random() < dec * .4 else 0.0
        M.beam(p['Platform'], (-w / 2, y + rng.uniform(-.04, .04), h - .06), (w / 2, y + rng.uniform(-.04, .04), h - .06 - drop), .27, .05, 'boards_weathered')
    for _ in range(int(2 + 4 * dec)):                            # boards stranded on the water / mud
        x0 = rng.uniform(-w * 2, w * 2); y0 = rng.uniform(-L, 0); a = rng.uniform(0, math.pi)
        M.beam(p['Props'], (x0, y0, .03), (x0 + math.cos(a) * 1.6, y0 + math.sin(a) * 1.6, .05), .25, .05, 'boards_weathered')


# ------------------------------------------------------------------ 挡土墙 / 梯台
def retaining(p, sp, st, rng):
    """Terraced retaining walls on a slope: battered masonry (收分 ~12%), 压顶 coping, 泄水孔, earth fill, optional flight per terrace."""
    L, n, th, mat = sp['length'], sp['terraces'], sp['tier_h'], sp['material']
    sb = max(sp['step_back'], th * 2.2 + .7); bat = .12 * (th + .3)
    cap = 'stone_carved_dark'; W = p['Walls']; G = p['Platform']
    F = FD.Foundation(p, {'body': mat, 'cap': cap, 'step': cap, 'rail': 'stone_carved'}, sp['lod'], rng)
    xs = rng.uniform(-L * .25, L * .25)
    for k in range(n):
        y = k * sb; z0 = k * th; z1 = z0 + th; last = k == n - 1
        batter_wall(W, -L / 2, L / 2, y, z0 - .3, z1, .75 + bat, bat, mat)
        M.box_minmax(W, (-L / 2, y + bat - .06, z1), (L / 2, y + bat + .5, z1 + .12), cap)                 # 压顶
        M.box_minmax(G, (-L / 2, y + bat + .5, -.3), (L / 2, y + (sb * 1.4 if last else sb) + .2, z1), 'ground_dirt')   # 填土
        fz = z0 + .35; fy = y + bat * (fz - z0 + .3) / (th + .3)
        for i in range(int(L / 2.4)):                            # 泄水孔
            x = -L / 2 + 1.2 + i * 2.4
            if abs(x - xs) > 1.4:
                M.box(W, (x, fy - .015, fz), (.14, .05, .14), 'tile_black')
        if sp['stair']:
            F.steps(xs, y, 1.4, z1, z0, 'tadao')
            M.box_minmax(G, (xs - .7, y - .01, z1 - .2), (xs + .7, y + bat + .5, z1 + .12), cap)             # landing through the coping


# ------------------------------------------------------------------ 临水基 / 石岸码头
def linshui(p, sp, st, rng):
    """筑临水基: battered stone quay with a projecting 马头 and splayed 两摆手, 桩 every 五尺 along the face,
    steps into the water, 系船石 bollards and 系缆环 (z 0 = water level)."""
    L, h, md, mw, dec = sp['length'], sp['height'], sp['matou'], sp['matou_w'], sp['decay']
    mat = 'ashlar_moss' if dec > 0 and sp['material'] == 'ashlar_grey' else sp['material']
    bed = -1.6; bat = .1 * (h - bed); cap = 'stone_carved_dark'; back = 5.0; a = md * .8
    W = p['Walls']; G = p['Platform']; C = p['Columns']
    F = FD.Foundation(p, {'body': mat, 'cap': cap, 'step': 'stone_carved', 'rail': 'stone_carved'}, sp['lod'], rng)
    poly_batter(W, [(-L / 2, 0), (L / 2, 0), (L / 2, back), (-L / 2, back)], bed, h - .14, bat, mat)          # 岸
    mt = [(-mw / 2, -md), (mw / 2, -md), (mw / 2 + a, .3), (-mw / 2 - a, .3)]                               # 马头 + 两摆手
    poly_batter(W, mt, bed, h - .14, bat, mat)
    M.box_minmax(G, (-L / 2 + .2, .45, h - .14), (L / 2 - .2, back - .2, h - .03), 'paving')
    M.prism(G, offset_poly(mt, -.45), h - .14, h - .03, 'paving')
    edges = [((-L / 2, 0), (-mw / 2 - a, 0)), ((-mw / 2 - a, 0), (-mw / 2, -md)), ((-mw / 2, -md), (mw / 2, -md)), ((mw / 2, -md), (mw / 2 + a, 0)), ((mw / 2 + a, 0), (L / 2, 0))]
    wl = bat * h / (h - bed)                                     # face offset at the water line
    for (ax, ay), (bx, by) in edges:
        nx, ny = _normal((ax, ay), (bx, by)); E = math.hypot(bx - ax, by - ay)
        k = 0.0
        while k < E - .05:                                       # 压阑 coping stones with joints
            s = min(rng.uniform(.9, 1.3), E - k)
            if rng.random() > dec * .35:
                u0, u1 = k / E, (k + s - .02) / E
                M.beam(G, (ax + (bx - ax) * u0 - nx * .22, ay + (by - ay) * u0 - ny * .22, h - .08), (ax + (bx - ax) * u1 - nx * .22, ay + (by - ay) * u1 - ny * .22, h - .08), .48, .16, cap)
            elif sp['lod'] < 2:                                  # fallen into the water
                u = (k + s / 2) / E
                M.box(G, (ax + (bx - ax) * u + nx * (bat + .6), ay + (by - ay) * u + ny * (bat + .6), -.1), (s, .48, .3), cap, math.atan2(by - ay, bx - ax) + rng.uniform(-.5, .5))
            k += s
        for i in range(int(E / (5 * FD.CUN * 10)) + 1):          # 每岸长五尺钉桩一条 (径五六寸)
            u = (i + .5) * 5 * FD.CUN * 10 / E
            if u < 1:
                M.column(C, ax + (bx - ax) * u + nx * (wl + .22), ay + (by - ay) * u + ny * (wl + .22), bed, .22 + rng.uniform(-.08, .06), .085, 'wood_dark', 8, 0)
    side = mw / 2 + a + 2.2
    if sp['steps'] in ('front', 'both'):
        F.steps(0, -md - .02, min(2.6, mw * .4), h, -.6, 'tadao', foot=bed)
    if sp['steps'] in ('side', 'both') and side + 1.2 < L / 2:
        F.steps(side * rng.choice([-1, 1]), -.02, 1.8, h, -.6, 'tadao', foot=bed)
    for x in (-mw / 2 + .7, mw / 2 - .7):                        # 系船石
        M.tube(G, [(x, -md + .55, h - .05), (x, -md + .55, h + .32), (x, -md + .55, h + .42)], .18, cap, 10, radii=[.18, .17, .12])
    zr = h * .55; yr = -bat * (h - zr) / (h - bed) - .04
    for x in (-L / 2 + 2, -mw / 2 - a - 1.2, mw / 2 + a + 1.2, L / 2 - 2):                  # 系缆环 on the bank face
        M.tube(G, [(x + .12 * math.cos(t * math.tau / 8), yr, zr + .12 * math.sin(t * math.tau / 8)) for t in range(9)], .025, 'iron', 6, False)
