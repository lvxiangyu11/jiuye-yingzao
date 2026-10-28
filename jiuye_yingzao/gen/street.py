# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Street and yard fixtures and boats: 露篱, 竹栅, 马台, 马槽/水槽子, 井口石 (+井屋子/辘轳), 灶 (立灶/釜镬灶/茶炉), 船.

Rules 【原文】 (宋尺 R.CHI_SONG; "每…一尺" = proportional to that dimension):
  卷六 露篱: 高六尺至一丈, 广八尺至一丈二尺; 下用地栿、横钤、立旌, 上用榻头木施版屋; 每一间分作三小间;
       立旌每高一尺则广四分厚二分五厘; 榻头木 广五分厚三分, 屋子版 广一寸二分, 山子版 长一寸六分, 沥水版 广二分五厘,
       曲棖 长一寸五分 (以上每间广一尺); 相连造则每间减立旌一条; 两头施搏风版及垂鱼惹草
  卷十二 竹栅: 每高一丈分作四格; 高一丈以上竹径八分, 不及一丈者径四分
  卷三 马台: 高二尺二寸, 长三尺八寸, 广二尺二寸; 其面方外余一尺八寸, 下面分作两踏; 身内或通素或叠涩造
  卷十五 砖马台: 高一尺六寸, 分作两踏, 上踏方二尺四寸, 下踏广一尺
  卷十五 马槽: 高二尺六寸, 广三尺, 长随间广; 下以五砖相并垒高六砖, 上四边垒砖一周高三砖, 槽内四壁侧倚方砖, 槽底铺方砖
  卷三 水槽子: 长七尺, 方二尺; 每广一尺唇厚二寸, 每高一尺底厚二寸五分
  卷三 井口石: 每方二尺五寸则厚一尺, 心内开凿井口径一尺; 素平面、素覆盆或起突莲华瓣造; 盖子径一尺二寸, 上凿二窍
  卷十五 甃井: 以水面径四尺为法
  卷六 井屋子: 自地至脊共高八尺, 四柱, 柱外方五尺, 柱头高五尺八寸, 下施井匮高一尺二寸; 两际施垂鱼惹草; 举分准大木作
  卷十三 立灶: 并台共高二尺五寸, 以锅口径一尺为祖; 门高七寸广五寸; 身方出锅口径四周各三寸; 台高一尺二寸至一尺五寸;
       转烟连二 / 直拔; 烟匮子高出灶身一尺五寸, 广六寸; 山华子斜高一尺五寸至二尺; 灶突高视屋身出屋外三尺, 方六寸
  卷十三 釜镬灶: 釜灶高六寸 (安甑者加至三尺), 釜口径一尺六寸, 门高六寸广五寸; 镬灶高一尺五寸, 镬口径三尺, 门高一尺二寸广九寸;
       后驼项突方一尺五寸, 斜高二尺五寸, 曲长一丈七尺; 面取圜泥造, 口径四周各出六寸
  卷十三 茶炉: 高一尺五寸, 面方七寸五分, 口圜径三寸五分深四寸, 吵眼高六寸广三寸, 底方六寸
  长物志 卷十 舟: 形如剗船, 底惟平, 长可三丈有余, 头阔五尺, 分为四仓; 幔以板不以蓬簟, 两傍不用栏楯, 以布绢作帐
  长物志 卷十 小船: 长丈余, 阔三尺许; 以蓝布作一长幔, 两边走檐, 前以二竹为柱, 后缚船尾
Other values 【推定】. Frame: X along the long side, front at -Y, Z up, ground = 0 (boats: z 0 = water).
"""
import math

from ..core import mesh as M
from ..core import rules as R
from . import foundation as FD

CHI = R.CHI_SONG; CUN = CHI / 10
MING_CHI = 0.32                                                 # 明尺, for 长物志


# ------------------------------------------------------------------ helpers
def square_hole(part, cx, cy, z0, z1, half, r, mat, n=32, top=None):
    """Square slab (half side) with a round hole of radius r; top = [(t, dz)] profile from hole (t=0) to edge (t=1)."""
    top = top or [(0, 0), (1, 0)]
    def p(t, a, z):
        c, s = math.cos(a), math.sin(a); k = half / max(abs(c), abs(s))
        rr = r + (k - r) * t
        return (cx + rr * c, cy + rr * s, z)
    ang = [math.tau * i / n for i in range(n)]               # n divisible by 8 keeps the square corners
    rings = [[p(t, a, z1 + dz) for a in ang] for t, dz in top]
    rings_bot = [[p(1, a, z0) for a in ang], [p(0, a, z0) for a in ang]]
    allr = rings + [rings_bot[0], rings_bot[1]]               # top profile, outer bottom, inner bottom
    vs = [v for ring in allr for v in ring]; fs = []; m = len(allr)
    for a, b in zip(range(m), range(1, m)):
        for i in range(n):
            j = (i + 1) % n; fs.append((a * n + i, a * n + j, b * n + j, b * n + i))
    for i in range(n):                                         # hole wall: inner bottom -> hole top ring
        j = (i + 1) % n; fs.append(((m - 1) * n + i, (m - 1) * n + j, j, i))
    part.add(vs, fs, mat)


def disc(part, x, y, z0, z1, r, mat, n=20):
    M.tube(part, [(x, y, z0), (x, y, z1)], r, mat, n, True, False)


def shell(part, pts_outer, thick, mat, close=True):
    """Thin closed sheet from a grid of points [[row of (x, y, z)]], thickened downward-inward by thick (two-sided in Unity)."""
    rows = len(pts_outer); cols = len(pts_outer[0])
    inner = [[(x, y, z - thick) for x, y, z in row] for row in pts_outer]
    vs = [v for row in pts_outer for v in row] + [v for row in inner for v in row]; off = rows * cols; fs = []
    for i in range(rows - 1):
        for j in range(cols - 1):
            a, b, c, d = i * cols + j, i * cols + j + 1, (i + 1) * cols + j + 1, (i + 1) * cols + j
            fs += [(a, b, c, d), (off + d, off + c, off + b, off + a)]
    for i in range(rows - 1):                                  # edges
        for j in (0, cols - 1):
            a, d = i * cols + j, (i + 1) * cols + j; fs.append((a, d, off + d, off + a))
    for j in range(cols - 1):
        for i in (0, rows - 1):
            a, b = i * cols + j, i * cols + j + 1; fs.append((a, b, off + b, off + a))
    part.add(vs, fs, mat)


# ------------------------------------------------------------------ 露篱 / 竹栅
def luli(p, sp, st, rng):
    """露篱: 地栿 + 横钤 + 立旌 frame per 间 of three 小间, 榻头木, a small board roof (版屋) with 搏风/垂鱼惹草 at the ends; infill 【推定】."""
    H = sp['height']; L = sp['length']; n = max(1, round(L / sp['bay'])); bw = L / n
    W = p['Walls']; C = p['Columns']; Rf = p['Roof']; wood = sp.get('wood') or rng.choice(['wood_dark', 'planks_old', 'boards_weathered'])
    pw, pt = .04 * H, .025 * H                                  # 立旌 每高一尺广四分厚二分五厘
    th_w, th_t = .05 * bw, .03 * bw                             # 榻头木
    wb = .12 * bw; rise = min(.06 * bw * 1.6, .3); half = math.sqrt(max(.01, wb * wb - rise * rise)) * .95
    zt = H - rise - .03                                         # top of 榻头木
    posts = [-L / 2 + k * bw / 3 for k in range(3 * n + 1)]   # 相连造: shared posts
    for x in posts:
        M.box_minmax(C, (x - pw / 2, -pt / 2, -.3), (x + pw / 2, pt / 2, zt - th_w), wood)
    M.beam(W, (-L / 2, 0, pw / 2), (L / 2, 0, pw / 2), pt * 1.2, pw, wood)                     # 地栿
    rails = [zt * .38, zt * .72]
    for z in rails:                                             # 横钤
        M.beam(W, (-L / 2, 0, z), (L / 2, 0, z), pt, pw * .9, wood)
    M.beam(W, (-L / 2 - .05, 0, zt - th_w / 2), (L / 2 + .05, 0, zt - th_w / 2), th_t * 2, th_w, wood)   # 榻头木
    inf = sp['infill']
    if inf != 'open':
        mat = 'wattle' if inf == 'wattle' else 'thatch_old'
        for a, b in zip(posts, posts[1:]):
            M.box_minmax(W, (a + pw / 2, -.015, pw), (b - pw / 2, .015, zt - th_w), mat)
    elif sp['lod'] < 2:                                         # 曲棖 braces under the 榻头木
        cl = .15 * bw
        for x in posts:
            for sx in (-1, 1):
                if -L / 2 < x + sx * cl < L / 2:
                    M.beam(C, (x, 0, zt - th_w - cl * .9), (x + sx * cl * .9, 0, zt - th_w), pt * .6, .03 * bw * .6, wood)
    zr = zt + rise
    for sy in (-1, 1):                                          # 屋子版 + 沥水版
        vs = [(-L / 2 - .12, 0, zr + .01), (L / 2 + .12, 0, zr + .01), (L / 2 + .12, sy * half, zt), (-L / 2 - .12, sy * half, zt)]
        vs += [(x, y, z - .012 * bw) for x, y, z in vs]
        Rf.add(vs, M.BOX_FACES, wood)
        M.beam(Rf, (-L / 2 - .12, sy * half, zt - .02), (L / 2 + .12, sy * half, zt - .02), .015, .025 * bw, wood)
    M.beam(Rf, (-L / 2 - .14, 0, zr + .03), (L / 2 + .14, 0, zr + .03), .06, .06, wood)         # 压脊
    for x in posts[::3]:                                        # 山子版 on each 间 post
        Rf.add([(x - .01, -half * .9, zt), (x + .01, -half * .9, zt), (x + .01, half * .9, zt), (x - .01, half * .9, zt),
                (x - .01, 0, zr - .01), (x + .01, 0, zr - .01), (x + .01, 0, zr - .01), (x - .01, 0, zr - .01)], M.BOX_FACES, wood)
    if sp['lod'] < 2:
        for sx in (-1, 1):                                      # 搏风版 + 垂鱼/惹草
            x = sx * (L / 2 + .13)
            for sy in (-1, 1):
                M.beam(Rf, (x, 0, zr + .02), (x, sy * (half + .04), zt - .02), .03, .07, wood)
                M.box(Rf, (x, sy * half * .55, zt + rise * .3), (.02, .1, .1), wood)
            M.box(Rf, (x, 0, zr - .1), (.02, .1, .18), wood)


def zhuzha(p, sp, st, rng):
    """竹栅: 每高一丈分作四格; canes 径八分 (≥ 一丈) or 四分; posts and double cane rails at each 格 line; dense or grid."""
    H = sp['height']; L = sp['length']; C = p['Columns']; W = p['Walls']
    d = (.8 if H >= 10 * CHI else .4) * CUN                  # 竹径八分 / 四分 (分 = 1/10 寸)
    cells = max(2, round(H / (10 * CHI) * 4)); lines = [H * k / cells for k in range(1, cells)] + [H - .05]
    np_ = max(2, round(L / 2.4)) + 1
    for k in range(np_):                                        # 立柱 (thick bamboo / timber) 【推定】
        x = -L / 2 + L * k / (np_ - 1)
        M.column(C, x, 0, -.4, H + .12, .045, 'bamboo', 8, .1, 0)
    for z in lines:
        for sy in (-1, 1):
            M.tube(W, [(-L / 2, sy * (d + .01), z), (L / 2, sy * (d + .01), z)], d * .7, 'bamboo', 6)
    if sp['lod'] >= 2:
        M.box_minmax(W, (-L / 2, -.01, 0), (L / 2, .01, H), 'bamboo'); return
    gap = d * 2.2 if sp['pattern'] == 'dense' else H / cells / 2
    x = -L / 2 + gap / 2
    while x < L / 2:
        top = H + (rng.uniform(-.04, .06) if sp['pattern'] == 'dense' else 0)
        M.tube(W, [(x, 0, -.2), (x, 0, top)], d / 2, 'bamboo', 6)
        x += gap
    if sp['pattern'] == 'grid':
        for z in [H * (k + .5) / cells for k in range(cells)]:
            M.tube(W, [(-L / 2, 0, z), (L / 2, 0, z)], d / 2, 'bamboo', 6)


# ------------------------------------------------------------------ 马台 / 马槽 / 水槽子
def matai(p, sp, st, rng):
    """马台 (上马石): stone 2.2 x 3.8 x 2.2 尺 with two steps in the extra 1.8 尺, plain or 叠涩; brick 1.6 尺 high, two steps."""
    P = p['Platform']
    if sp['material'] == 'brick':
        H = 16 * CUN; top = 24 * CUN; low = 10 * CUN; mat = rng.choice(['brick_grey', 'brick_grey_old'])
        M.box_minmax(P, (-top / 2, -top / 2, 0), (top / 2, top / 2, H), mat)
        M.box_minmax(P, (-top / 2, -top / 2 - low, 0), (top / 2, -top / 2, H / 2), mat)
        M.box_minmax(P, (-top / 2 - .02, -top / 2 - .02, H - .05), (top / 2 + .02, top / 2 + .02, H), 'stone_carved')
    else:
        H = 22 * CUN; L = 38 * CUN; B = 22 * CUN; face = 18 * CUN; mat = rng.choice(['stone_carved', 'stone_carved_dark'])
        y0 = -L / 2 + face
        M.box_minmax(P, (-B / 2, y0, 0), (B / 2, L / 2, H), mat)                  # 面方二尺二寸
        for k in range(2):                                                         # 两踏
            M.box_minmax(P, (-B / 2, y0 - face * (2 - k) / 2, 0), (B / 2, y0 - face * (1 - k) / 2, H * (k + 1) / 3), mat)
        if sp['decor'] == 'diezhe':                                                # 叠涩: waist recess + top band
            M.box_minmax(P, (-B / 2 - .025, y0 - .025, H - .06), (B / 2 + .025, L / 2 + .025, H), mat)
            M.box_minmax(P, (-B / 2 - .02, y0 - .02, 0), (B / 2 + .02, L / 2 + .02, .06), mat)
    if sp['post']:                                              # 拴马桩 beside it 【推定】
        M.box_minmax(P, (.8, .1, 0), (1.04, .34, 1.7), 'stone_carved_dark')
        M.box(P, (.92, .22, 1.82), (.28, .3, .26), 'stone_carved_dark')


def macao(p, sp, st, rng):
    """马槽 (砖, 高二尺六寸广三尺) or 水槽子 (石, 长七尺方二尺); optional hay and 拴马桩."""
    P = p['Platform']; L = sp['length']
    if sp['material'] == 'brick':
        H = 26 * CUN; B = 30 * CUN; rim_h = H * 3 / 9; mat = rng.choice(['brick_grey', 'brick_grey_old'])
        M.box_minmax(P, (-L / 2, -B / 2, 0), (L / 2, B / 2, H - rim_h), mat)      # 五砖相并垒高六砖
        t = .12
        for a, b in (((-L / 2, -B / 2), (L / 2, -B / 2 + t)), ((-L / 2, B / 2 - t), (L / 2, B / 2)), ((-L / 2, -B / 2), (-L / 2 + t, B / 2)), ((L / 2 - t, -B / 2), (L / 2, B / 2))):
            M.box_minmax(P, (a[0], a[1], H - rim_h), (b[0], b[1], H), mat)       # 四边垒砖一周高三砖
        M.box_minmax(P, (-L / 2 + t, -B / 2 + t, H - rim_h), (L / 2 - t, B / 2 - t, H - rim_h + .02), 'stone_carved')   # 方砖槽底
        zf = H - rim_h + .02; ix, iy = L / 2 - t, B / 2 - t
    else:
        L = 70 * CUN; B = 20 * CUN; H = 20 * CUN; lip = .2 * B; bot = .25 * H; mat = rng.choice(['stone_carved', 'stone_carved_dark', 'stone'])
        M.box_minmax(P, (-L / 2, -B / 2, 0), (L / 2, B / 2, bot), mat)
        for a, b in (((-L / 2, -B / 2), (L / 2, -B / 2 + lip)), ((-L / 2, B / 2 - lip), (L / 2, B / 2)), ((-L / 2, -B / 2), (-L / 2 + lip, B / 2)), ((L / 2 - lip, -B / 2), (L / 2, B / 2))):
            M.box_minmax(P, (a[0], a[1], bot), (b[0], b[1], H), mat)
        zf = bot; ix, iy = L / 2 - lip, B / 2 - lip
    if sp['fill'] == 'hay':
        M.box_minmax(p['Props'], (-ix + .02, -iy + .02, zf), (ix - .02, iy - .02, zf + .12), 'thatch_old')
    elif sp['fill'] == 'water':
        M.box_minmax(p['Props'], (-ix + .01, -iy + .01, zf), (ix - .01, iy - .01, zf + .1), 'glaze_black')
    if sp['posts']:
        for x in (-L / 2 + .3, L / 2 - .3):
            M.column(p['Columns'], x, B / 2 + .35, 0, 1.5, .08, 'wood_dark', 8, .05, 0)
        M.beam(p['Columns'], (-L / 2 + .3, B / 2 + .35, 1.3), (L / 2 - .3, B / 2 + .35, 1.3), .08, .08, 'wood_dark')


# ------------------------------------------------------------------ 井口石 / 甃井 / 井屋子
def jingkou(p, sp, st, rng):
    """井口石 on a 井阶, brick 甃井 shaft (水面径四尺) below; top 素平 / 覆盆 / 莲华; 盖子; cover none | 井屋子 | 辘轳."""
    P = p['Platform']; half = 12.5 * CUN; T = 10 * CUN; r = 5 * CUN
    mat = rng.choice(['stone_carved', 'stone_carved_dark'])
    zs = .12
    M.box_minmax(P, (-1.1, -1.1, 0), (1.1, 1.1, zs), 'paving')                             # 井阶 【推定】
    M.tube(p['Props'], [(0, 0, -2.0), (0, 0, zs)], 20 * CUN + .1, 'brick_grey_moss', 20, False, False)   # 甃井 shaft (水面径四尺), seen through the mouth
    disc(p['Props'], 0, 0, -1.6, -1.55, 20 * CUN, 'glaze_black')                                         # water
    style = sp['top']
    if style == 'fupen':
        prof = [(0, .06), (.25, .055), (.55, .03), (.8, .008), (1, 0)]
    elif style == 'lian':
        prof = [(0, .07), (.3, .06), (.6, .03), (1, 0)]
    else:
        prof = [(0, 0), (1, 0)]
    square_hole(P, 0, 0, zs, zs + T, half, r, mat, 32, prof)
    if style == 'lian' and sp['lod'] < 2:                                                # 起突莲华瓣
        for k in range(16):                                      # tear-drop petals lying on the 覆盆 slope
            a = math.tau * (k + .5) / 16; c, s_ = math.cos(a), math.sin(a)
            M.tube(P, [((r + .015) * c, (r + .015) * s_, zs + T + .06), ((r + .09) * c, (r + .09) * s_, zs + T + .05), ((r + .2) * c, (r + .2) * s_, zs + T + .02)],
                   .03, mat, 8, True, True, radii=[.012, .04, .008])
    if sp['lid']:                                                                         # 盖子 with two holes
        disc(P, .55, .5, zs, zs + .06, 6 * CUN, mat)
        for dx in (-.05, .05):
            disc(P, .55 + dx, .5, zs + .06, zs + .065, .5 * CUN, 'tile_black', 8)
    cov = sp['cover']
    if cov == 'jingwuzi':
        jingwuzi(p, zs, sp['lod'], rng)
    elif cov == 'lulu':                                                                   # 辘轳 【推定】
        for sx in (-1, 1):
            M.box_minmax(p['Columns'], (sx * .55 - .06, .35, zs), (sx * .55 + .06, .47, 1.2), 'wood_dark')
        M.tube(p['Columns'], [(-.6, .41, 1.05), (.6, .41, 1.05)], .1, 'wood', 10)
        M.beam(p['Columns'], (.6, .41, 1.05), (.6, .41, 1.4), .04, .04, 'wood_dark')
        M.tube(p['Props'], [(0, .41, .95), (0, .1, zs + T + .02)], .008, 'iron', 4, False)


def jingwuzi(p, z0, lod, rng):
    """井屋子 【原文 卷六】: 8 尺 to the ridge, four posts 5 尺 square outside, 柱头 5.8 尺, 井匮 1.2 尺, two-slope board roof with 垂鱼惹草."""
    Ht = 80 * CUN; ch = 58 * CUN; S = 50 * CUN; a = .05 * Ht          # 柱 方五分 (per 尺 of height)
    wood = rng.choice(['wood_dark', 'planks_old']); C = p['Columns']; Rf = p['Roof']
    h = S / 2 - a / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            M.box_minmax(C, (sx * h - a / 2, sy * h - a / 2, z0), (sx * h + a / 2, sy * h + a / 2, z0 + ch), wood)
    for sy in (-1, 1):                                          # 额
        M.beam(C, (-h, sy * h, z0 + ch - .06), (h, sy * h, z0 + ch - .06), .06, .125, wood)
    for sx in (-1, 1):                                          # 栿 + 蜀柱 + 叉手
        M.beam(C, (sx * h, -h - .1, z0 + ch + .05), (sx * h, h + .1, z0 + ch + .05), .1, .125, wood)
    zr = z0 + Ht
    for sx in (-1, 1):
        M.box_minmax(C, (sx * h - .04, -.04, z0 + ch + .1), (sx * h + .04, .04, zr - .1), wood)
    ov = .35; run = h + ov; drop = (zr - z0 - ch) * (run / h)
    for sy in (-1, 1):                                          # 厦瓦版 (board roof) + 护缝
        vs = [(-h - .3, 0, zr), (h + .3, 0, zr), (h + .3, sy * run, zr - drop), (-h - .3, sy * run, zr - drop)]
        vs += [(x, y, z - .04) for x, y, z in vs]
        Rf.add(vs, M.BOX_FACES, wood)
        for k in range(7):
            x = -h - .3 + (2 * h + .6) * (k + .5) / 7
            M.beam(Rf, (x, 0, zr + .02), (x, sy * run, zr - drop + .02), .04, .02, wood)
    M.beam(Rf, (-h - .32, 0, zr + .04), (h + .32, 0, zr + .04), .1, .1, wood)                  # 压脊
    for sx in (-1, 1):                                          # 搏风版 + 垂鱼惹草
        x = sx * (h + .32)
        for sy in (-1, 1):
            M.beam(Rf, (x, 0, zr + .03), (x, sy * run, zr - drop - .02), .03, .125, wood)
            if lod < 2:
                M.box(Rf, (x, sy * run * .55, zr - drop * .55 - .14), (.02, .3, .22), wood)    # 惹草
        if lod < 2:
            M.box(Rf, (x, 0, zr - .3), (.02, .28, .48), wood)                                    # 垂鱼
    for sy in (-1, 1):                                          # 井匮 (board box between the posts)
        M.box_minmax(p['Walls'], (-h + a / 2, sy * h - .02, z0), (h - a / 2, sy * h + .02, z0 + 12 * CUN), wood)
    for sx in (-1, 1):
        M.box_minmax(p['Walls'], (sx * h - .02, -h + a / 2, z0), (sx * h + .02, h - a / 2, z0 + 12 * CUN), wood)


# ------------------------------------------------------------------ 灶
def _stove_body(P, x, y, w, d, h, mat):
    M.box_minmax(P, (x - w / 2, y - d / 2, 0), (x + w / 2, y + d / 2, h), mat)


def _pot(P, x, y, z, r, lod):
    n = 16 if lod < 2 else 8
    M.tube(P, [(x, y, z - r * .55), (x, y, z - r * .2), (x, y, z + .01)], r, 'iron', n, True, True, radii=[r * .45, r * .85, r])
    M.tube(P, [(x, y, z + .01), (x, y, z + .03)], r * 1.08, 'iron', n, True, False)


def _door(P, x, y, w, h, z=0.0):
    M.box_minmax(P, (x - w / 2, y - .02, z + .04), (x + w / 2, y + .01, z + .04 + h), 'tile_black')


def zao(p, sp, st, rng):
    """灶: 立灶 (转烟连二 / 直拔, 锅口径一尺为祖), 釜灶, 镬灶 (后驼项突), 茶炉; 石灰泥饰; 灶突 optional."""
    P = p['Platform']; kind = sp['kind']; mat = rng.choice(['plaster_lime', 'mud_smooth', 'adobe']); lod = sp['lod']
    pot = sp['pot'] * CHI; s = sp['pot']                       # 锅口径 (尺) → scale for 门/突
    if kind in ('li_zhuanyan', 'li_zhiba'):
        Ht = 25 * CUN; body = pot + 2 * 3 * CUN; tai = 13.5 * CUN
        nb = 2 if kind == 'li_zhuanyan' else 1; W = body * nb + (.06 if nb == 2 else 0)
        M.box_minmax(P, (-W / 2 - .05, -body / 2 - .1, 0), (W / 2 + .05, body / 2 + .05, tai), mat)            # 台
        _stove_body(P, 0, 0, W, body, Ht, mat)                                                                 # 身
        xs = [0.0] if nb == 1 else [-body / 2 - .03, body / 2 + .03]
        for x in xs:
            _pot(P, x, 0, Ht, pot / 2, lod)
            _door(P, x, -body / 2 - .1, 5 * CUN * s, 7 * CUN * s, 0)                                           # 灶门 高七寸广五寸
        if nb == 2:                                             # 隔烟 between the pots
            M.box_minmax(P, (-.03, -body / 2, Ht), (.03, body / 2, Ht + .06), mat)
        # 烟匮子: 长随身, 高出灶身一尺五寸, 广六寸
        M.box_minmax(P, (-W / 2, body / 2, 0), (W / 2, body / 2 + 6 * CUN, Ht + 15 * CUN), mat)
        if lod < 2:                                             # 山华子 beside the flue
            for sx in (-1, 1):
                x0 = sx * (6 * CUN); x1 = sx * (W / 2)
                P.add([(x0, body / 2, Ht + 15 * CUN), (x1, body / 2, Ht + 15 * CUN), (x1, body / 2, Ht + 15 * CUN + .01), (x0, body / 2, Ht + 15 * CUN + .01),
                       (x0, body / 2 + .04, Ht + 15 * CUN + 17 * CUN), (x0 + .01 * sx, body / 2 + .04, Ht + 15 * CUN + 17 * CUN), (x0 + .01 * sx, body / 2 + .04, Ht + 15 * CUN + .01), (x0, body / 2 + .04, Ht + 15 * CUN + .01)],
                      M.BOX_FACES, mat)
        chim_x, chim_y, chim_z, chim = 0.0, body / 2 + 3 * CUN, Ht + 15 * CUN, 6 * CUN
    elif kind in ('fu', 'huo'):
        if kind == 'fu':
            mouth = 16 * CUN; Ht = sp.get('fu_h', rng.choice([6, 18, 24, 30])) * CUN; dw, dh = 5 * CUN, 6 * CUN
        else:
            mouth = 30 * CUN; Ht = 15 * CUN; dw, dh = 9 * CUN, 12 * CUN
        r = mouth / 2 + 6 * CUN                                  # 面取圜泥造, 口径四周各出六寸
        M.tube(P, [(0, 0, 0), (0, 0, Ht * .9), (0, 0, Ht)], r, mat, 24, True, True, radii=[r * 1.04, r, r * .97])
        _pot(P, 0, 0, Ht, mouth / 2, lod)
        _door(P, 0, -r + .02, dw, min(dh, Ht * .8), 0)
        if kind == 'fu' and Ht > .4:                            # 甑 on the 釜
            M.tube(P, [(0, 0, Ht + .02), (0, 0, Ht + .45)], mouth / 2 * .9, 'wood', 16, True, False, radii=[mouth / 2 * .85, mouth / 2 * .95])
        chim_x, chim_y, chim_z, chim = 0.0, r + .2, Ht, 6 * CUN
        if kind == 'huo':                                       # 后驼项突: 方一尺五寸, 斜高二尺五寸, 曲长一丈七尺
            a = 15 * CUN; Lc = 170 * CUN; rise = 25 * CUN; pts = []
            for k in range(9):
                t = k / 8; pts.append((0, r - .1 + Lc * t * .92, a / 2 + rise * math.sin(t * math.pi / 2)))
            for q0, q1 in zip(pts, pts[1:]):
                M.beam(P, q0, q1, a, a, mat)
            chim_x, chim_y, chim_z, chim = 0.0, pts[-1][1], pts[-1][2] + a / 2, 9 * CUN
    else:                                                       # 茶炉
        Ht = 15 * CUN; top = 7.5 * CUN; bot = 6 * CUN
        vs = [(-bot / 2, -bot / 2, 0), (bot / 2, -bot / 2, 0), (bot / 2, bot / 2, 0), (-bot / 2, bot / 2, 0),
              (-top / 2, -top / 2, Ht), (top / 2, -top / 2, Ht), (top / 2, top / 2, Ht), (-top / 2, top / 2, Ht)]
        P.add(vs, M.BOX_FACES, mat)
        disc(P, 0, 0, Ht, Ht + .004, 1.75 * CUN, 'tile_black', 12)                          # 口 径三寸五分
        _door(P, 0, -(bot + top) / 4, 3 * CUN, 6 * CUN, 0)                                   # 吵眼 高六寸广三寸
        M.tube(P, [(.0, 0, Ht + .02), (0, 0, Ht + .16)], .07, 'bronze', 12, True, True, radii=[.06, .075])   # kettle 【推定】
        return
    if sp['chimney']:                                           # 灶突: 方六寸, 高视屋身出屋外三尺
        top = sp['roof_h'] + 30 * CUN
        M.box_minmax(P, (chim_x - chim / 2, chim_y - chim / 2, chim_z - .02), (chim_x + chim / 2, chim_y + chim / 2, top), mat)
        M.box_minmax(P, (chim_x - chim / 2 - .03, chim_y - chim / 2 - .03, top - .06), (chim_x + chim / 2 + .03, chim_y + chim / 2 + .03, top), 'brick_grey')


# ------------------------------------------------------------------ 船
def hull(part, L, B, D, *, bow=.7, stern=.8, rocker=.25, sheer=.15, flare=.82, t=.05, n=14, zb=-.32, mat='wood_dark'):
    """Flat-bottomed open hull (剗船/平底船) along Y, bow at -Y: closed solid with a cavity (outer skin, inner skin, rim, transoms)."""
    def sec(u, inner):
        tt = 2 * u - 1                                           # -1 bow .. +1 stern
        w = B / 2 * (1 - (1 - bow) * max(0, -tt) ** 2 - (1 - stern) * max(0, tt) ** 2)
        z0 = zb + rocker * (max(0, -tt) ** 2.2 + .6 * max(0, tt) ** 2.2)
        z1 = zb + D + sheer * tt * tt
        y = -L / 2 + L * u
        if inner:
            w -= t; z0 += t * 1.2; y = -L / 2 + t + (L - 2 * t) * u
        return [(-w * flare, y, z0), (w * flare, y, z0), (w, y, z1), (-w, y, z1)]
    O = [sec(i / n, False) for i in range(n + 1)]; I = [sec(i / n, True) for i in range(n + 1)]
    vs = [v for s in O for v in s] + [v for s in I for v in s]; off = 4 * (n + 1); fs = []
    o = lambda i, k: 4 * i + k
    q = lambda i, k: off + 4 * i + k
    for i in range(n):
        for a, b in ((0, 1), (1, 2), (3, 0)):
            fs.append((o(i, a), o(i, b), o(i + 1, b), o(i + 1, a))); fs.append((q(i, b), q(i, a), q(i + 1, a), q(i + 1, b)))
        fs.append((o(i, 2), q(i, 2), q(i + 1, 2), o(i + 1, 2))); fs.append((o(i, 3), o(i + 1, 3), q(i + 1, 3), q(i, 3)))
    for i in (0, n):
        fs.append((o(i, 0), o(i, 1), o(i, 2), o(i, 3))); fs.append((q(i, 3), q(i, 2), q(i, 1), q(i, 0)))
        fs.append((o(i, 3), o(i, 2), q(i, 2), q(i, 3)))
    part.add(vs, fs, mat)
    return lambda u: sec(u, True)


def boat(p, sp, st, rng):
    """船: ferry 渡船 (平底方头, 篷, 橹, 篙, 跳板) 【推定】 | zhou 舟 (长物志: 剗船形, 四仓, 板幔, 布帐) | xiao 小船 (长物志: 蓝布长幔)."""
    kind = sp['kind']; C = p['Columns']; Rf = p['Roof']; Pr = p['Props']; P = p['Platform']
    wood = rng.choice(['wood_dark', 'boards_weathered', 'planks_old'])
    if kind == 'zhou':
        L = rng.uniform(3.0, 3.4) * 10 * MING_CHI; B = 5 * MING_CHI; D = .7          # 长三丈有余, 头阔五尺
        inner = hull(P, L, B, D, bow=.92, stern=.85, rocker=.2, sheer=.1, mat=wood)
    elif kind == 'xiao':
        L = rng.uniform(1.0, 1.2) * 10 * MING_CHI; B = 3 * MING_CHI; D = .42
        inner = hull(P, L, B, D, bow=.55, stern=.7, rocker=.14, sheer=.08, n=10, zb=-.18, mat=wood)
    else:
        L = sp['length']; B = sp['beam']; D = .78
        inner = hull(P, L, B, D, bow=.78, stern=.82, rocker=.22, sheer=.12, mat=wood)
    zb = -.32 if kind != 'xiao' else -.18
    def at(u):                                                  # inner section at u: floor z, gunwale z, half width
        s = inner(u); return s[0][2], s[2][2], s[1][0], s[2][0], s[0][1]
    for u in [k / 10 for k in range(1, 10)] if kind != 'xiao' else [.3, .55, .8]:            # thwarts / 舱板
        zf, zg, wf, wg, y = at(u)
        M.beam(P, (-wg + .02, y, zg - .08), (wg - .02, y, zg - .08), .08, .06, wood)
    zf0, _, wf0, _, _ = at(.5)
    M.box_minmax(P, (-wf0 + .02, -L / 2 + .5, zf0), (wf0 - .02, L / 2 - .5, zf0 + .04), 'planks_old')   # floor boards
    for sx in (-1, 1):                                          # gunwale rails
        pts = [(sx * at(k / 10)[3], at(k / 10)[4], at(k / 10)[1] + .02) for k in range(11)]
        for a, b in zip(pts, pts[1:]):
            M.beam(P, a, b, .08, .06, wood)
    if kind == 'ferry':
        if sp['awning']:                                        # 篷: bamboo hoops + mat over the stern third 【推定】
            rows = []
            for k in range(7):
                u = .55 + .35 * k / 6; zf, zg, wf, wg, y = at(u)
                rows.append([(wg * math.cos(math.pi * j / 10), y, zg + .9 * math.sin(math.pi * j / 10) + .05) for j in range(11)])
            shell(Rf, rows, .03, 'wattle')
            for row in rows[::2]:
                for a, b in zip(row, row[1:]):
                    M.beam(Rf, (a[0], a[1], a[2] - .035), (b[0], b[1], b[2] - .035), .03, .03, 'bamboo')
        zf, zg, wf, wg, y = at(.97)                             # 橹 on a pin at the stern
        M.box(C, (wg * .5, y, zg + .06), (.08, .08, .14), 'wood_dark')
        M.beam(C, (wg * .5, y, zg + .14), (wg * .5 + .6, y + 4.2, -.1), .09, .05, 'wood')
        for k in range(2):                                      # 篙
            M.tube(Pr, [(-wg + .15 + k * .12, -L * .4, zg + .05), (-wg + .25 + k * .12, L * .45, zg + .08)], .022, 'bamboo', 6)
        if sp['plank']:                                         # 跳板 at the bow
            zf, zg, wf, wg, y = at(.02)
            M.beam(Pr, (0, y + .5, zg), (0, y - 1.8, zg - .25), .5, .05, 'planks_old')
        for x in (-wf0 * .5, wf0 * .5):                         # mooring post 【推定】
            zf, zg, wf, wg, y = at(.06)
            M.column(C, x, y + .3, zf, zg + .25, .05, 'wood_dark', 8, 0, 0)
    elif kind == 'zhou':                                        # 四仓 bulkheads; 中仓+后仓 under a 板幔, 布帐 rolled
        us = [.18, .42, .7, .86]
        for u in us:
            zf, zg, wf, wg, y = at(u)
            M.box_minmax(P, (-wf, y - .02, zf), (wf, y + .02, zg - .02), wood)
        u0, u1 = .42, .86; zf, zg, wf, wg, y0 = at(u0); y1 = at(u1)[4]; hh = zg + 1.35
        for y in (y0, (y0 + y1) / 2, y1):
            for sx in (-1, 1):
                M.box_minmax(C, (sx * (wg - .05) - .04, y - .04, zg - .05), (sx * (wg - .05) + .04, y + .04, hh), wood)
        rows = [[(wg * 1.05 * math.cos(math.pi * j / 6), y, hh + .18 * math.sin(math.pi * j / 6)) for j in range(7)] for y in (y0 - .25, y1 + .25)]
        shell(Rf, rows, .04, 'planks_old')                      # 幔以板
        for sx in (-1, 1):                                      # 布绢帐, rolled up under the eave
            M.tube(Rf, [(sx * wg * 1.02, y0 - .2, hh - .05), (sx * wg * 1.02, y1 + .2, hh - .05)], .06, 'cloth_blue', 8)
        zc = at(.56)[0]                                         # 卓 + 凳 in 中仓, 榻 in 后仓
        M.box_minmax(Pr, (-.35, at(.56)[4] - .3, zc), (.35, at(.56)[4] + .3, zc + .55), 'lacquer_black')
        M.box_minmax(Pr, (-.45, at(.78)[4] - .35, at(.78)[0]), (.45, at(.78)[4] + .35, at(.78)[0] + .32), 'wood')
    else:                                                       # 小船: 前以二竹为柱, 后缚船尾, 蓝布长幔两边走檐
        zf, zg, wf, wg, yf = at(.22); zt, zgt, wft, wgt, yt = at(.98)
        top = zg + 1.15
        for sx in (-1, 1):
            M.tube(C, [(sx * wg * .8, yf, zf), (sx * wg * .8, yf, top)], .02, 'bamboo', 6)
        rows = [[(wg * (j - 4) / 4 * (.8 if y == yf else .55), y, z - (.4 if y == yf else .2) * abs(j - 4) / 4) for j in range(9)] for y, z in ((yf, top), (yt, zgt + .25))]
        shell(Rf, rows, .01, 'cloth_blue')
        M.tube(Pr, [(wg * .6, yf - .2, zg), (wg * .6 + .6, yf - 2.6, zg + 1.2)], .012, 'bamboo', 5)   # 钓竿
        M.tube(Pr, [(-wg + .1, yf, zg + .03), (-wg + .2, yt, zg + .05)], .018, 'bamboo', 6)            # 篙
