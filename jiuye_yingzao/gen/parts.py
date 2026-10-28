# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Building components: 铺作 (bracket sets), doors, windows, shop fronts, railings, small props.

Proportions follow 《营造法式》材分 where the text gives them (卷四 栱/枓/铺作, 卷六–七 小木作); otherwise
【推定】. All geometry is in a local frame: X along the wall, -Y outward (front), Z up; callers place it
with mesh.place(...) via Part.mark()/transform().
"""
import math

from ..core import mesh as M


# ------------------------------------------------------------------ 铺作
def bracket(part, x, y, z, angle, levels, fen, mat, kind='song', corner=False, lod=1):
    """One bracket set standing on a column head (or 补间) at (x, y, z); angle rotates local -Y outward.

    song: 栌斗 32x32x20 分, 泥道栱 62 分 along the wall, 华栱 projecting 30 分 per 跳 (levels = 跳数, 铺作 = levels+3),
          交互斗 at each 跳 tip, 令栱 + 耍头 on the outer 跳. corner adds a 45 deg 角华栱.
    simple: 栌斗 + 一斗三升 (no projection).  Returns (height, projection) in metres.
    """
    start = part.mark(); f = fen
    if kind == 'none' or levels <= 0 and kind != 'simple':
        return 0.0, 0.0
    lu = (32 * f, 32 * f, 20 * f)
    M.box(part, (0, 0, lu[2] / 2), lu, mat)                                  # 栌斗
    zc = lu[2]; cai = 15 * f; zu = 21 * f                                     # 单材 / 足材 heights
    small = (16 * f, 16 * f, 10 * f)
    if kind == 'simple':
        M.box(part, (0, 0, zc + cai / 2), (62 * f, 10 * f, cai), mat)          # 栱
        for sx in (-1, 0, 1):
            M.box(part, (sx * 24 * f, 0, zc + cai + small[2] / 2), small, mat)  # 三升
        h = zc + cai + small[2]; proj = 0.0
    else:
        L = levels
        for k in range(L):
            zk = zc + k * zu
            M.box(part, (0, 0, zk + cai / 2), ((62 + k * 10) * f, 10 * f, cai), mat)     # 泥道栱 / 慢栱 along the wall
            reach = (k + 1) * 30 * f
            M.box(part, (0, -reach / 2, zk + zu / 2), (10 * f, reach + 16 * f, zu), mat)  # 华栱 (足材)
            M.box(part, (0, -reach, zk + zu + small[2] / 2), small, mat)                 # 交互斗
            if lod == 0 and k == L - 1 and L >= 2:                                         # 下昂 hint on outer 跳
                M.beam(part, (0, -reach - 8 * f, zk + zu * .6), (0, -reach + 30 * f, zk + zu * 1.9), 10 * f, 13 * f, mat)
        top = zc + L * zu; reach = L * 30 * f
        M.box(part, (0, -reach, top + cai / 2), (72 * f, 10 * f, cai), mat)               # 令栱
        for sx in (-1, 1):
            M.box(part, (sx * 30 * f, -reach, top + cai + small[2] / 2), small, mat)       # 散斗
        M.box(part, (0, -reach / 2 - 10 * f, top + cai / 2 + 2 * f), (8 * f, reach + 30 * f, cai), mat)  # 耍头
        if corner:
            for s in (-1, 1):
                d = L * 30 * f * 1.414
                M.beam(part, (0, 0, zc + zu / 2), (s * d * .707, -d * .707, zc + L * zu * .9), 10 * f, zu, mat)
        h = top + cai + small[2]; proj = reach
    part.transform(start, M.place(x, y, z, angle))
    return h, proj


def bracket_height(levels, fen, kind):
    if kind == 'none' or (levels <= 0 and kind != 'simple'):
        return 0.0
    if kind == 'simple':
        return (20 + 15 + 10) * fen
    return (20 + levels * 21 + 15 + 10) * fen


# ------------------------------------------------------------------ doors
def door_banmen(part, w, h, mats, lod=1, studs=True):
    """版门 【原文 卷六】: two plank leaves, 门簪 above, 门钉 rows. Local origin: opening bottom centre, wall plane y=0."""
    fr = .12; t = .08
    for sx in (-1, 1):
        M.box(part, (sx * (w / 2 + fr / 2), 0, h / 2), (fr, .2, h), mats['frame'])
    M.box(part, (0, 0, h + fr / 2), (w + 2 * fr, .2, fr), mats['frame'])
    M.box(part, (0, .02, -.04), (w + 2 * fr, .22, .08), mats['frame'])                 # 门限
    for sx in (-1, 1):
        M.box(part, (sx * w / 4, .05, h / 2), (w / 2 - .02, t, h - .02), mats['door'])
        if lod == 0 and studs:
            rows = max(3, int(h / .4)); cols = 3
            for i in range(rows):
                for j in range(cols):
                    M.box(part, (sx * (w / 4) + (j - 1) * w / 8, .0, .3 + i * (h - .5) / (rows - 1)), (.045, .04, .045), mats['metal'])
    if lod < 2:
        for sx in (-1, 1):
            M.box(part, (sx * w / 5, -.12, h + fr / 2), (.13, .22, .13), mats['frame'])   # 门簪


def door_geyan(part, w, h, mats, lod=1, leaves=4):
    """格子门 【原文 卷七】: leaves with 格眼 (lattice) over 障水版 (panel), paper behind."""
    fr = .1; lw = w / leaves
    for sx in (-1, 1):
        M.box(part, (sx * (w / 2 + fr / 2), 0, h / 2), (fr, .16, h), mats['frame'])
    M.box(part, (0, 0, h + fr / 2), (w + 2 * fr, .16, fr), mats['frame'])
    for i in range(leaves):
        cx = -w / 2 + lw * (i + .5); split = h * .62
        for zz in (0.02, h * .36, split - .02, h - .02):
            M.box(part, (cx, 0, zz), (lw - .02, .07, .06), mats['frame'])
        for sx in (-1, 1):
            M.box(part, (cx + sx * (lw / 2 - .04), 0, h / 2), (.06, .07, h), mats['frame'])
        M.box(part, (cx, .02, h * .18), (lw - .08, .03, h * .32), mats['door'])          # 障水版
        M.box(part, (cx, .035, (split + h) / 2), (lw - .08, .01, h - split - .05), mats['paper'])
        if lod < 2:
            lattice(part, cx, split + (h - split) / 2 - .01, lw - .1, h - split - .1, mats['frame'], 'geyan')
            lattice(part, cx, h * .49, lw - .1, h * .22, mats['frame'], 'geyan')


def lattice(part, cx, cz, w, h, mat, kind):
    """Window/door lattice grid in the wall plane (y ~ 0)."""
    if kind == 'pozi':        # 破子棂: triangular-section vertical slats (a square bar turned 45 deg)
        n = max(5, int(w / .1))
        for i in range(n):
            x = cx - w / 2 + w * (i + .5) / n
            M.beam(part, (x, 0, cz - h / 2), (x, 0, cz + h / 2), .045, .045, mat, up=(1, 1, 0))
        return
    if kind == 'zhiling':     # 直棂: square vertical bars
        n = max(4, int(w / .12))
        for i in range(n):
            M.box(part, (cx - w / 2 + w * (i + .5) / n, 0, cz), (.035, .045, h), mat)
        return
    step = .16 if kind == 'geyan' else .2
    nx = max(2, int(w / step)); nz = max(2, int(h / step))
    for i in range(1, nx):
        M.box(part, (cx - w / 2 + w * i / nx, 0, cz), (.025, .04, h), mat)
    for j in range(1, nz):
        M.box(part, (cx, 0, cz - h / 2 + h * j / nz), (w, .04, .025), mat)


def window(part, w, h, mats, kind='pozi', lod=1):
    """Window in the wall plane, local origin at opening bottom centre."""
    fr = .09
    if kind == 'round':
        n = 20; r = min(w, h) / 2
        pts = [(r * math.cos(math.tau * i / n), 0, h / 2 + r * math.sin(math.tau * i / n)) for i in range(n + 1)]
        M.tube(part, pts, .05, mats['frame'], 6)
        M.box(part, (0, .03, h / 2), (r * 1.6, .01, r * 1.6), mats['paper'])
        if lod < 2:
            lattice(part, 0, h / 2, r * 1.3, r * 1.3, mats['frame'], 'geyan')
        return
    for sx in (-1, 1):
        M.box(part, (sx * (w / 2 + fr / 2), 0, h / 2), (fr, .14, h + 2 * fr), mats['frame'])
    for sz in (0, 1):
        M.box(part, (0, 0, sz * h + (fr / 2 if sz else -fr / 2)), (w + 2 * fr, .14, fr), mats['frame'])
    M.box(part, (0, .04, h / 2), (w, .01, h), mats['paper'])
    if lod >= 2:
        return
    if kind == 'zhizhai':     # 支摘窗: two tiers, the upper one propped open
        lattice(part, 0, h * .27, w - .06, h * .5, mats['frame'], 'grid')
        st = part.mark(); lattice(part, 0, h * .76, w - .06, h * .46, mats['frame'], 'grid')
        part.transform(st, M.Matrix.Translation((0, -.12, 0)))
    elif kind == 'small':
        lattice(part, 0, h / 2, w - .04, h - .04, mats['frame'], 'zhiling')
    else:
        lattice(part, 0, h / 2, w - .04, h - .04, mats['frame'], kind)


def shop_front(part, w, h, mats, rng, lod=1):
    """铺面: 柜台 half wall + 排门板 boards stacked to the sides (opened shop) and a 门楣."""
    M.box(part, (0, -.25, .45), (w * .55, .45, .9), mats['frame'])                       # 柜台
    M.box(part, (0, -.25, .92), (w * .58, .55, .05), mats['door'])
    nb = max(4, int(w / .32)); bw = w / nb
    keep = sorted(rng.sample(range(nb), k=max(1, nb // 3)))
    for i in keep:
        x = -w / 2 + bw * (i + .5)
        if abs(x) < w * .3:
            continue
        M.box(part, (x, .02, h / 2), (bw - .015, .05, h - .05), mats['door'])
    M.box(part, (0, 0, h - .06), (w, .18, .12), mats['frame'])                           # 门楣


def railing(part, pts, h, mat, post_every=1.2, lod=1, seat=False):
    """Railing along a polyline: posts, 寻杖 (top rail), bottom rail, balusters; seat=True adds 美人靠 style seat board."""
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a[:2], b[:2])
        if L < .05:
            continue
        n = max(1, int(L / post_every))
        for i in range(n + 1):
            t = i / n; p = tuple(a[k] + (b[k] - a[k]) * t for k in range(3))
            M.box(part, (p[0], p[1], p[2] + h / 2), (.09, .09, h), mat)
        z0 = a[2]
        M.beam(part, (a[0], a[1], z0 + h), (b[0], b[1], z0 + h), .07, .07, mat)
        M.beam(part, (a[0], a[1], z0 + .1), (b[0], b[1], z0 + .1), .06, .08, mat)
        if seat:
            M.beam(part, (a[0], a[1], z0 + .45), (b[0], b[1], z0 + .45), .32, .05, mat)
        if lod == 0:
            m = max(2, int(L / .18))
            for i in range(1, m):
                t = i / m; p = tuple(a[k] + (b[k] - a[k]) * t for k in range(3))
                M.box(part, (p[0], p[1], p[2] + h * .5), (.03, .03, h * .8), mat)


# ------------------------------------------------------------------ props
def well(part, x, y, z, mats):
    n = 12; r0, r1 = .55, .75
    vs = [(x + r * math.cos(math.tau * i / n), y + r * math.sin(math.tau * i / n), z + zz) for zz in (0, .7) for r in (r1, r0) for i in range(n)]
    fs = []
    for i in range(n):
        j = (i + 1) % n
        fs += [(i, j, 2 * n + j, 2 * n + i), (n + j, n + i, 3 * n + i, 3 * n + j), (2 * n + i, 2 * n + j, 3 * n + j, 3 * n + i)]
    part.add(vs, fs, mats['stone'])
    for sx in (-1, 1):
        M.box(part, (x + sx * .8, y, z + 1.0), (.12, .12, 2.0), mats['frame'])
    M.tube(part, [(x - .8, y, z + 1.6), (x + .8, y, z + 1.6)], .09, mats['frame'], 8)


def stele(part, x, y, z, mats):
    M.box(part, (x, y, z + .25), (1.4, .9, .5), mats['stone'])                            # 龟趺 (simplified)
    M.box(part, (x, y, z + 1.6), (1.0, .28, 2.2), mats['stone'])
    M.box(part, (x, y, z + 2.85), (1.1, .34, .35), mats['stone'])


def tables(part, x0, x1, y0, y1, z, rng, mats):
    for _ in range(max(2, int((x1 - x0) * (y1 - y0) / 6))):
        x = rng.uniform(x0 + .8, x1 - .8); y = rng.uniform(y0 + .8, y1 - .8)
        M.box(part, (x, y, z + .72), (1.0, .7, .06), mats['door'])
        for sx in (-1, 1):
            for sy in (-1, 1):
                M.box(part, (x + sx * .42, y + sy * .27, z + .36), (.06, .06, .72), mats['frame'])
        for sy in (-1, 1):
            M.box(part, (x, y + sy * .6, z + .42), (1.0, .22, .05), mats['door'])


def crates(part, x0, x1, y0, y1, z, rng, mats):
    for _ in range(max(3, int((x1 - x0) * (y1 - y0) / 4))):
        x = rng.uniform(x0 + .6, x1 - .6); y = rng.uniform(y0 + .6, y1 - .6); s = rng.uniform(.5, .9)
        M.box(part, (x, y, z + s / 2), (s * 1.2, s, s), mats['door'], rng.uniform(-.3, .3))
        if rng.random() < .4:
            M.box(part, (x, y, z + s * 1.4), (s * .9, s * .8, s * .8), mats['frame'], rng.uniform(-.3, .3))


def sign_board(part, x, y, z, w, mats, vertical=False):
    if vertical:
        M.box(part, (x, y, z), (.12, .5, 1.6), mats['sign'])
    else:
        M.box(part, (x, y, z), (w, .1, .55), mats['sign'])
        M.box(part, (x, y - .03, z), (w * .86, .05, .4), mats['door'])


def lantern(part, x, y, z, mats):
    M.tube(part, [(x, y, z), (x, y, z + .18), (x, y, z + .4), (x, y, z + .55)], .2, mats['lantern'], 10,
           radii=[.1, .22, .21, .1])
    M.tube(part, [(x, y, z + .55), (x, y, z + .85)], .015, mats['metal'], 4)
