# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Small public works: 望火楼, 卷輂水窗, 砖瓦窑.

Rules 【原文】:
  卷十九 望火楼功限: 一坐四柱各高三十尺, 上方五尺, 下方一丈一尺; 榥三十六条, 梯脚二条, 平栿二条, 蜀柱二枚,
       搏风版二片, 角柱四条, 厦屋版二十片, 护缝二十二条, 压脊一条, 坐版六片
  卷三 卷輂水窗: 用长三尺广二尺厚六寸石; 两壁开掘至硬地, 各用地钉打筑, 上铺衬石方三路; 方上并二横砌石涩一重,
       涩上随岸顺砌并二厢壁版; 水窗当心平铺石地面一重; 上下出入水处侧砌线道三重, 其前密钉擗石桩二路;
       两边厢壁上相对卷輂, 用斧刃石鬭卷合, 斧刃石上用缴背一重, 其背上又平铺石段二重;
       若当河道卷輂, 卷輂之外上下水随河岸斜分四摆手, 地面之外侧砌线道石三重, 其前密钉擗石桩三路
  卷十五 垒造窑: 大窑高二丈二尺四寸, 径一丈八尺; 门高五尺六寸广二尺六寸; 平坐高五尺六寸; 上垒五帀高七尺;
       收顶七帀高九尺八寸; 窑床长一丈五尺高一尺四寸; 门两壁各广五尺四寸高五尺六寸, 仍垒脊子; 门两壁各广五尺二寸高八尺;
       外围径二丈九尺高二丈; 池径一丈高二尺; 踏道长三丈八尺四寸; 窑眼暗突出烟
Other values 【推定】. Frame: front at -Y, Z up; ground = 0 (水窗: z 0 = water level).
"""
import math

from ..core import mesh as M
from ..core import rules as R
from .roof import RoofModel

CHI = R.CHI_SONG; CUN = CHI / 10


# ------------------------------------------------------------------ 望火楼
def wanghuolou(p, sp, st, rng):
    """Fire-watch tower: four battered posts (30 尺, 下方一丈一尺 → 上方五尺), 9 tiers of 榥 on every face (36),
    a ladder (梯脚二条 + rungs), 平栿 + 坐版 floor, four 角柱, a two-slope board roof of 20 厦屋版 with 22 护缝, 搏风版 and 压脊."""
    H = sp['height']; k = H / (30 * CHI); lo = 11 * CHI * k / 2; hi = 5 * CHI * k / 2
    C = p['Columns']; B = p['Beams']; Rf = p['Roof']; wood = rng.choice(['wood_dark', 'wood'])
    corner = lambda z, sx, sy: (sx * (lo + (hi - lo) * z / H), sy * (lo + (hi - lo) * z / H))
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, y0 = corner(0, sx, sy); x1, y1 = corner(H, sx, sy)
            M.box_minmax(p['Platform'], (x0 - .3, y0 - .3, 0), (x0 + .3, y0 + .3, .25), 'stone_carved')     # footing 【推定】
            M.column(C, x0, y0, .25, H, .16, wood, 10, .15, 0, (x1 - x0, y1 - y0))
    for i in range(1, 10):                                      # 榥 9 x 4 = 36
        z = H * i / 10
        pts = [corner(z, -1, -1), corner(z, 1, -1), corner(z, 1, 1), corner(z, -1, 1)]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            M.beam(B, (a[0], a[1], z), (b[0], b[1], z), .1, .12, wood)
    if sp['braces']:                                            # 斜撑 on the lower faces 【推定】
        for sy in (-1, 1):
            for z0, z1 in ((0.3, H * .3), (H * .3, H * .6)):
                a = corner(z0, -1, sy); b = corner(z1, 1, sy)
                M.beam(B, (a[0], a[1], z0), (b[0], b[1], z1), .08, .08, wood)
    for sx in (-1, 1):                                          # 梯脚 二条 + rungs on the front face
        a = (sx * .28, -lo - 1.6, 0); b = (sx * .28, -hi - .1, H)
        M.beam(C, a, b, .07, .12, wood)
    n = int(H / .32)
    for i in range(1, n):
        t = i / n; y = -lo - 1.6 + (-hi - .1 + lo + 1.6) * t
        M.beam(C, (-.28, y, H * t), (.28, y, H * t), .04, .04, wood)
    fl = hi + .25                                               # 平栿 二条 + 坐版 六片
    for sx in (-1, 1):
        M.beam(B, (sx * hi, -fl, H + .08), (sx * hi, fl, H + .08), .14, .16, wood)
    for i in range(6):
        y0 = -fl + 2 * fl * i / 6
        M.box_minmax(p['Platform'], (-fl, y0 + .005, H + .16), (fl, y0 + 2 * fl / 6 - .005, H + .2), 'planks_old')
    ch = 1.9; zc = H + .2
    for sx in (-1, 1):                                          # 角柱 四条
        for sy in (-1, 1):
            M.box_minmax(C, (sx * (fl - .06) - .05, sy * (fl - .06) - .05, zc), (sx * (fl - .06) + .05, sy * (fl - .06) + .05, zc + ch), wood)
    if sp['rail']:                                              # 【推定】 low rail
        for sy in (-1, 1):
            M.beam(B, (-fl, sy * fl, zc + .9), (fl, sy * fl, zc + .9), .06, .06, wood)
        M.beam(B, (fl, -fl, zc + .9), (fl, fl, zc + .9), .06, .06, wood); M.beam(B, (-fl, -fl, zc + .9), (-fl, fl, zc + .9), .06, .06, wood)
    zt = zc + ch; rise = .75; ov = .45; run = fl + ov; drop = rise * run / fl; L2 = fl + .35
    for sx in (-1, 1):                                          # 蜀柱 二枚 carrying the 压脊
        M.box_minmax(C, (sx * (fl - .06) - .05, -.05, zt), (sx * (fl - .06) + .05, .05, zt + rise), wood)
    M.beam(B, (-fl, -fl + .06, zt), (fl, -fl + .06, zt), .1, .12, wood); M.beam(B, (-fl, fl - .06, zt), (fl, fl - .06, zt), .1, .12, wood)
    for sy in (-1, 1):                                          # 厦屋版 10 per slope + 护缝 11 per slope
        for i in range(10):
            x0 = -L2 + 2 * L2 * i / 10; x1 = x0 + 2 * L2 / 10 - .01
            vs = [(x0, 0, zt + rise), (x1, 0, zt + rise), (x1, sy * run, zt + rise - drop), (x0, sy * run, zt + rise - drop)]
            Rf.add(vs + [(x, y, z - .03) for x, y, z in vs], M.BOX_FACES, 'planks_old')
        for i in range(11):
            x = -L2 + 2 * L2 * i / 10
            M.beam(Rf, (x, 0, zt + rise + .02), (x, sy * run, zt + rise - drop + .02), .05, .025, wood)
    M.beam(Rf, (-L2 - .02, 0, zt + rise + .05), (L2 + .02, 0, zt + rise + .05), .12, .1, wood)          # 压脊
    for sx in (-1, 1):                                          # 搏风版 二片
        for sy in (-1, 1):
            M.beam(Rf, (sx * (L2 + .02), 0, zt + rise + .03), (sx * (L2 + .02), sy * (run + .03), zt + rise - drop - .02), .03, .18, wood)
    if sp['bell']:                                              # 警钟 / 鼓 under the roof 【推定】
        M.tube(p['Props'], [(0, 0, zt - .15), (0, 0, zt - .65)], .2, 'bronze', 14, True, True, radii=[.12, .22])
        M.beam(p['Props'], (0, 0, zt), (0, 0, zt - .15), .03, .03, 'iron')


# ------------------------------------------------------------------ 卷輂水窗
def _wedge(part, cx, y0, y1, zs, r0, r1, a0, a1, mat):
    vs = []
    for y in (y0, y1):
        for rr, a in ((r0, a0), (r0, a1), (r1, a1), (r1, a0)):
            vs.append((cx + rr * math.cos(a), y, zs + rr * math.sin(a)))
    part.add(vs, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], mat)


def shuichuang(p, sp, st, rng):
    """Arched water gate / culvert: 厢壁 abutments, 斧刃石 voussoirs, 缴背, 石段二重, 地面石, 线道三重, 擗石桩, 四摆手;
    over = wall (city wall with 垛口) | road (embankment with parapets) | none; optional iron 水栅."""
    n = sp['openings']; span = sp['span']; r = span / 2; over = sp['over']
    W = p['Walls']; G = p['Platform']; C = p['Columns']
    zf = -1.2; zs = .25; vd = 20 * CUN; jb = 6 * CUN; sd = 12 * CUN    # floor, springing, 斧刃石 depth (2 尺), 缴背, 石段二重
    crown = zs + r; zb = crown + vd + jb + sd                   # bank / top of the stonework
    pw = max(1.2, span * .45); Wt = n * span + (n - 1) * pw; ab = 1.2
    hw = sp['height'] if over == 'wall' else 0.0
    T = {'wall': 6.0 + hw * .3, 'road': 7.0, 'none': 3.2}[over]
    stone = rng.choice(['ashlar_grey', 'ashlar_moss', 'stone_block']); cap = 'stone_carved_dark'
    cxs = [-Wt / 2 + r + i * (span + pw) for i in range(n)]
    for sx in (-1, 1):                                          # end abutments (厢壁) up to the bank
        M.box_minmax(W, (sx * Wt / 2 if sx > 0 else -Wt / 2 - ab, -T / 2, zf), (Wt / 2 + ab if sx > 0 else -Wt / 2, T / 2, zb), stone)
    for i in range(n - 1):                                      # piers between eyes
        x0 = cxs[i] + r; M.box_minmax(W, (x0, -T / 2, zf), (x0 + pw, T / 2, zs), stone)
        M.box_minmax(W, (x0 - .02, -T / 2 - .6, zf), (x0 + pw + .02, -T / 2, zs * .5), stone)       # cutwater 【推定】
    m = 14
    for cx in cxs:
        for k in range(m):                                      # barrel (斧刃石 ring through the length)
            a0 = math.pi * k / m; a1 = math.pi * (k + 1) / m
            _wedge(W, cx, -T / 2, T / 2, zs, r, r + vd, a0, a1, stone)
        nv = max(7, round(math.pi * r / (6 * CUN * 1.6)))       # face voussoirs 鬭卷合, slightly proud, with joints
        for face in (-1, 1):
            y0, y1 = (face * T / 2, face * (T / 2 + .04))
            for k in range(nv):
                a0 = math.pi * k / nv + .004; a1 = math.pi * (k + 1) / nv - .004
                _wedge(W, cx, min(y0, y1), max(y0, y1), zs, r - .005, r + vd, a0, a1, cap)
                _wedge(W, cx, min(y0, y1), max(y0, y1), zs, r + vd + .005, r + vd + jb, a0, a1, stone)   # 缴背
        xs = [cx - r - vd + (2 * (r + vd)) * j / 16 for j in range(17)]     # spandrel fill above the ring
        for xa, xb in zip(xs, xs[1:]):
            def zo(x):
                d = abs(x - cx); return zs + math.sqrt(max(0.0, (r + vd + jb) ** 2 - d * d)) if d < r + vd + jb else zs
            z0 = max(zo(xa), zo(xb)) - .02
            M.box_minmax(W, (xa, -T / 2, z0), (xb, T / 2, zb - sd), stone)
    for i in range(n - 1):
        x0 = cxs[i] + r; M.box_minmax(W, (x0, -T / 2, zs), (x0 + pw, T / 2, zb - sd), stone)
    for face in (-1, 1):                                        # 石段二重 courses on both faces
        for c in range(2):
            ya, yb = sorted((face * (T / 2 - .03), face * (T / 2 + .03 + .02 * c)))
            M.box_minmax(W, (-Wt / 2 - ab, ya, zb - sd + c * sd / 2), (Wt / 2 + ab, yb, zb - sd + (c + 1) * sd / 2 - .01), cap)
    wl = 3.2 if n > 1 or over != 'none' else 2.2; ang = math.radians(35)                   # 四摆手
    yend = T / 2 + wl * math.cos(ang); xw = Wt / 2 + ab + wl * math.sin(ang)
    for face in (-1, 1):
        for sx in (-1, 1):
            a = (sx * (Wt / 2 + ab * .5), face * T / 2); b = (sx * (xw - ab * .3), face * yend)
            M.beam(W, (a[0], a[1], (zf + zb) / 2), (b[0], b[1], (zf + zb) / 2), ab, zb - zf, stone)
            M.beam(W, (a[0], a[1], zb + .07), (b[0], b[1], zb + .07), ab + .1, .14, cap)
        M.box_minmax(G, (-xw, min(face * T / 2, face * yend), zf - .3), (xw, max(face * T / 2, face * yend), zf), cap)   # 地面石 between the wings
        for k in range(3):                                      # 线道 三重
            y = face * (yend - .16 - k * .33)
            M.box_minmax(G, (-xw + .4 * (k + 1), y - .15, zf), (xw - .4 * (k + 1), y + .15, zf + .03), 'stone_carved')
        rows = 3 if n > 1 else 2                                # 擗石桩 二路 / 三路 (河道)
        for k in range(rows):
            y = face * (yend + .25 + k * .3); x = -xw
            while x <= xw:
                M.column(C, x, y, zf - 1.0, zf + .2 + rng.uniform(-.05, .05), .08, 'wood_dark', 8, 0)
                x += .32
    M.box_minmax(G, (-Wt / 2, -T / 2, zf - .3), (Wt / 2, T / 2, zf), cap)                  # 当心 地面石
    if sp['grille']:                                            # iron 水栅 at mid-length 【推定】
        for cx in cxs:
            x = cx - r + .15
            while x < cx + r - .1:
                ztop = zs + math.sqrt(max(0.0, r * r - (x - cx) ** 2)) - .02
                M.tube(C, [(x, 0, zf), (x, 0, ztop)], .025, 'iron', 6); x += .22
            M.beam(C, (cx - r, 0, zs), (cx + r, 0, zs), .06, .06, 'iron')
    Lx = xw + 4.0
    for sx in (-1, 1):                                          # bank fill beside the abutments
        M.box_minmax(G, (sx * (Wt / 2 + ab) if sx > 0 else -Lx, -T / 2, zf), (Lx if sx > 0 else -(Wt / 2 + ab), T / 2, zb), 'ground_dirt')
    if over == 'wall':
        face = rng.choice(['brick_grey', 'brick_grey_old', 'ashlar_grey'])
        M.box_minmax(W, (-Lx, -T / 2, zb), (Lx, T / 2, zb + hw), face)
        M.box_minmax(G, (-Lx, -T / 2, zb + hw - .05), (Lx, T / 2, zb + hw + .02), 'paving')
        x0 = -Lx
        while x0 + 1.6 <= Lx:                                   # 垛口 outside, 女墙 inside (as gen/specials.city_wall)
            M.box_minmax(W, (x0, -T / 2, zb + hw), (x0 + 1.0, -T / 2 + .5, zb + hw + 1.6), face)
            M.box_minmax(W, (x0 + 1.0, -T / 2, zb + hw), (x0 + 1.6, -T / 2 + .5, zb + hw + .9), face)
            x0 += 1.6
        M.box_minmax(W, (-Lx, T / 2 - .4, zb + hw), (Lx, T / 2, zb + hw + 1.0), face)
    elif over == 'road':
        M.box_minmax(G, (-Lx, -T / 2, zb), (Lx, T / 2, zb + .25), 'ground_dirt')
        M.box_minmax(G, (-Lx, -T / 2 + .6, zb + .25), (Lx, T / 2 - .6, zb + .3), 'paving')
        for face in (-1, 1):                                    # parapets over the opening
            M.beam(W, (-Wt / 2 - ab, face * (T / 2 - .2), zb + .7), (Wt / 2 + ab, face * (T / 2 - .2), zb + .7), .35, .9, cap)


# ------------------------------------------------------------------ 砖瓦窑
def yao(p, sp, st, rng):
    """砖瓦窑 (垒造窑): 外围 cylinder 29 尺 x 20 尺, kiln crown 22.4 尺, 窑池 on top 【位置推定】, firing door with 门两壁 and 脊子,
    踏道 38.4 尺 up to the top, 窑眼 flues; yard with brick / tile stacks and greenware rows."""
    k = sp['scale']; C = p['Columns']; W = p['Walls']; G = p['Platform']; Pr = p['Props']
    Ro = 14.5 * CHI * k; Ho = 20 * CHI * k; Ri = 9 * CHI * k; Ht = 22.4 * CHI * k
    brick = rng.choice(['brick_grey_old', 'brick_red_old', 'brick_grey']); mud = rng.choice(['earth_rammed', 'mud_smooth', 'earth_loess'])
    kilns = [(0.0, 1)] if sp['count'] == 1 else [(-Ro - 1.2, -1), (Ro + 1.2, 1)]
    for cx, side in kilns:
        M.tube(W, [(cx, 0, 0), (cx, 0, Ho * .5), (cx, 0, Ho)], Ro, brick, 32, True, False, radii=[Ro * 1.05, Ro * 1.02, Ro])   # 外围
        hc = Ht - Ho
        M.tube(W, [(cx, 0, Ho - .05), (cx, 0, Ho + hc * .45), (cx, 0, Ho + hc * .8), (cx, 0, Ht)], Ri, mud, 24, True, True,
               radii=[Ri * 1.02, Ri * .85, Ri * .55, Ri * .2])  # 收顶 crown
        pr = 5 * CHI * k                                        # 窑池 径一丈 高二尺
        M.tube(W, [(cx, 0, Ht - .25), (cx, 0, Ht - .25 + 2 * CHI * k)], pr, brick, 24, True, False)
        M.tube(W, [(cx, 0, Ht - .26 + 2 * CHI * k), (cx, 0, Ht - .25 + 2 * CHI * k + .01)], pr - .12, 'glaze_black', 24, True, False)
        for a in (math.radians(140), math.radians(180), math.radians(220)):      # 窑眼 / 暗突出烟 at the back
            x = cx + math.cos(a + math.pi / 2) * (Ri + .6); y = math.sin(a + math.pi / 2) * (Ri + .6)
            M.box_minmax(W, (x - .22, y - .22, Ho), (x + .22, y + .22, Ho + .7), brick)
            M.box_minmax(W, (x - .14, y - .14, Ho + .7), (x + .14, y + .14, Ho + .71), 'tile_black')
        dw = 2.6 * CHI * k; dh = 5.6 * CHI * k; wt = .45; y0 = -Ro * .97        # 窑门 + 门两壁 (二对)
        l1 = 5.4 * CHI * k; l2 = 5.2 * CHI * k; h2 = 8 * CHI * k
        for sx in (-1, 1):
            xa = cx + sx * (dw / 2 + wt / 2)
            M.box_minmax(W, (xa - wt / 2, y0 - l1, 0), (xa + wt / 2, y0 + .3, dh), brick)
            M.box_minmax(W, (xa - wt / 2 + sx * .3, y0 - l1 - l2, 0), (xa + wt / 2 + sx * .3, y0 - l1, h2), brick)
        M.box_minmax(W, (cx - dw / 2, y0 - .02, 0), (cx + dw / 2, y0 + .02, dh), 'tile_black')
        for sy in (-1, 1):                                      # 脊子 over the door passage
            M.beam(W, (cx - dw / 2 - wt, y0 - l1 / 2 + sy * l1 / 2, dh + .05), (cx + dw / 2 + wt, y0 - l1 / 2 + sy * l1 / 2, dh + .05), .2, .1, brick)
        vs = [(cx - dw / 2 - wt - .1, y0 + .3, dh), (cx + dw / 2 + wt + .1, y0 + .3, dh), (cx + dw / 2 + wt + .1, y0 - l1, dh), (cx - dw / 2 - wt - .1, y0 - l1, dh),
              (cx - .05, y0 + .3, dh + .55), (cx + .05, y0 + .3, dh + .55), (cx + .05, y0 - l1, dh + .55), (cx - .05, y0 - l1, dh + .55)]
        W.add(vs, M.BOX_FACES, 'tile_grey_old')
        L = 38.4 * CHI * k; run = math.sqrt(max(1.0, L * L - Ho * Ho)); w = 1.6     # 踏道 to the top of the 外围
        x0 = cx + side * (Ro * .82); x1 = x0 + side * run
        vs = [(x0, -w / 2, 0), (x1, -w / 2, 0), (x1, w / 2, 0), (x0, w / 2, 0), (x0, -w / 2, Ho), (x1 - side * .01, -w / 2, .02), (x1 - side * .01, w / 2, .02), (x0, w / 2, Ho)]
        W.add(vs, M.BOX_FACES, brick)
        for sy in (-1, 1):
            M.beam(W, (x0, sy * (w / 2 + .1), Ho + .35), (x1, sy * (w / 2 + .1), .35), .2, .7, brick)
        M.box_minmax(G, (cx - Ro - .5, -Ro - .5, -.02), (cx + Ro + .5, Ro + .5, .02), 'ground_dirt')
    if sp['yard']:                                              # 砖垛 / 瓦垛 / 坯 rows 【推定】
        xs0 = -Ro * (2.4 if sp['count'] == 2 else 1.2) - 3.5
        for i in range(int(4 + rng.random() * 4)):
            x = xs0 - (i % 3) * 1.6; y = -Ro + (i // 3) * 1.8
            h = rng.uniform(.8, 1.6); mat = brick if rng.random() < .65 else 'tile_grey_old'
            M.box_minmax(Pr, (x - .6, y - .7, 0), (x + .6, y + .7, h), mat)
        for j in range(3):                                      # greenware rows under straw covers
            y = Ro * .4 + j * 1.2
            M.box_minmax(Pr, (xs0 - 4, y - .3, 0), (xs0, y + .3, .55), 'adobe')
            vs = [(xs0 - 4.1, y - .45, .5), (xs0 + .1, y - .45, .5), (xs0 + .1, y + .45, .5), (xs0 - 4.1, y + .45, .5),
                  (xs0 - 4.1, y - .02, .8), (xs0 + .1, y - .02, .8), (xs0 + .1, y + .02, .8), (xs0 - 4.1, y + .02, .8)]
            Pr.add(vs, M.BOX_FACES, 'thatch_old')
        M.tube(Pr, [(xs0 - 2, -Ro - 3.5, 0), (xs0 - 2, -Ro - 3.5, .25), (xs0 - 2, -Ro - 3.5, .9)], 1.8, 'earth_loess', 14, True, True, radii=[1.9, 1.5, .4])  # clay heap
