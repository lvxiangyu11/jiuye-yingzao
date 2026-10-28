# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Foundations (台基/地基): platforms, mouldings, steps, balustrades, slope retaining, column bases.

Rules 【原文】 from 《营造法式》:
  卷三 立基: 其高与材五倍 (max 六倍)          卷三 殿阶基: 叠涩坐, 每层露棱五寸, 束腰露身一尺, 隔身版柱, 下施土衬石
  卷三 压阑石: 长三尺 广二尺 厚六寸            卷三 角石: 方二尺, 每方一尺厚四寸; 角柱: 每长一尺方四寸
  卷三 柱础: 其方倍柱之径; 覆盆每方一尺高一寸; 仰覆莲华其高加覆盆一倍
  卷三 踏道: 每阶高一尺作二踏, 每踏厚五寸广一尺; 两边副子各广一尺八寸; 象眼逐层退入
  卷十五 砖踏道: 每踏高四寸广一尺, 两颊各广一尺二寸     卷十五 慢道: 城门 1:5, 厅堂 1:4 (三瓣蝉翅)
  卷十五 须弥坐: 十三砖, 逐层出入 (混肚/牙脚/罨牙/合莲/束腰/仰莲/壶门柱子/罨涩/方涩)
  卷三 钩阑: 重台钩阑高四尺, 单钩阑高三尺五寸    卷十五 砖墙: 每高一尺底广五寸, 每面斜收一寸 (收分 10%)
Other values 【推定】. Local frame as gen/building.py: X along the front, front at -Y, Z up, ground = 0.
"""
import math

from ..core import mesh as M
from ..core import rules as R

CUN = R.CHI_SONG / 10          # 1 寸 (m)


def ring(part, hx, hy, z0, z1, mat, inset0=0.0, inset1=None, y_front_extra=0.0):
    """Rectangular solid course: half extents (hx, hy) shrunk by inset at bottom/top (tapered mouldings)."""
    i1 = inset0 if inset1 is None else inset1
    vs = []
    for z, i in ((z0, inset0), (z1, i1)):
        a, b = hx - i, hy - i
        vs += [(-a, -b - y_front_extra, z), (a, -b - y_front_extra, z), (a, b, z), (-a, b, z)]
    part.add(vs, M.BOX_FACES, mat)


# ------------------------------------------------------------------ platform profiles
def profile(kind, H):
    """Courses for a platform of height H: [(z0, z1, inset_bottom, inset_top, material_role)] from the ground up.
    Insets are measured inward from the outer face (positive = recessed). Roles: base, body, cap, waist, panel."""
    if kind in ('stone', 'brick', 'earth', 'tamped', 'rubble', 'plain'):
        cap = min(.19, H * .3)                                  # 压阑石/阶条石 厚六寸
        soil = min(.12, H * .2)                                 # 土衬石
        bat = .1 * (H - cap - soil) if kind in ('brick', 'tamped', 'rubble') else 0.0   # 砖墙收分
        return [(0, soil, -.05, -.05, 'base'), (soil, H - cap, 0, bat, 'body'), (H - cap, H, bat - .03, bat - .03, 'cap')]
    if kind == 'diezhe':                                        # 宋 殿阶基 叠涩坐
        lu = 5 * CUN; waist = 10 * CUN
        n_low = max(1, int((H * .45) / lu)); n_up = max(1, int((H * .4) / lu))
        scale = H / ((n_low + n_up) * lu + waist + .12)
        lu *= scale; waist *= scale; out = []; z = 0.0
        out.append((0, .12 * scale, -.06, -.06, 'base'))      # 土衬石
        z = .12 * scale
        for k in range(n_low):                                   # 下叠涩: each course steps in
            out.append((z, z + lu, k * .05, k * .05, 'cap' if k == 0 else 'body')); z += lu
        wi = n_low * .05 + .06
        out.append((z, z + waist, wi, wi, 'waist')); z += waist  # 束腰 with 隔身版柱
        for k in range(n_up):                                    # 上叠涩: steps back out
            ii = max(-.02, (n_up - 1 - k) * .05)
            out.append((z, z + lu, ii, ii, 'cap' if k == n_up - 1 else 'body')); z += lu
        return out
    if kind == 'xumi':                                          # 砖作 须弥坐 十三砖 (heights in courses, step in 寸 vs previous)
        seq = [(1, 0.0, 'base'), (1, -1.0, 'round'), (1, 1.0, 'body'), (1, -.3, 'body'), (1, 1.5, 'lotus_down'), (1, 1.0, 'waist'),
               (1, -.7, 'lotus_up'), (3, 1.5, 'panel'), (1, -.5, 'body'), (2, -.5, 'cap')]
        course = H / 13; scale = max(.6, H / .9); out = []; z = 0.0; inset = 0.0
        for n, step, role in seq:
            inset += step * CUN * scale
            i0, i1 = inset, inset
            if role == 'lotus_down':                            # 合莲: narrows upward
                i0, i1 = inset - .7 * CUN * scale, inset
            elif role == 'lotus_up':                            # 仰莲: widens upward
                i0, i1 = inset + .7 * CUN * scale, inset - .3 * CUN * scale
            elif role == 'round':                               # 混肚: bulge
                i0, i1 = inset + .4 * CUN * scale, inset + .4 * CUN * scale
            out.append((z, z + n * course, i0, i1, role)); z += n * course
        m = min(i for _, _, a, b, _ in out for i in (a, b))
        return [(a, b, i0 - m, i1 - m, r) for a, b, i0, i1, r in out]   # outermost course flush with the outline
    return [(0, H, 0, 0, 'body')]


class Foundation:
    """Builds one platform (optionally several tiers, a 月台, steps, balustrades, slope retaining)."""

    def __init__(self, parts, mats, lod=1, rng=None):
        self.p = parts; self.m = mats; self.lod = lod; self.rng = rng

    def mat(self, role):
        return {'base': self.m.get('soil', self.m['cap']), 'cap': self.m['cap'], 'body': self.m['body'], 'waist': self.m.get('waist', self.m['body']),
                'panel': self.m.get('waist', self.m['body']), 'round': self.m['cap'], 'lotus_down': self.m['cap'], 'lotus_up': self.m['cap']}[role]

    def block(self, hx, hy, z0, H, kind, front_extra=0.0):
        """One platform tier with outer half extents (hx, hy) from z0 to z0+H."""
        P = self.p['Platform']
        for a, b, i0, i1, role in profile(kind, H):
            ring(P, hx, hy, z0 + a, z0 + b, self.mat(role), i0, i1)
            if role == 'waist' and self.lod < 2:                # 隔身版柱 / 壸门 rhythm on the waist
                n = max(2, int(2 * hx / .9)); hz = b - a
                for k in range(n + 1):
                    x = -hx + i0 + (2 * (hx - i0)) * k / n
                    for y in (-hy + i0 - .03, hy - i0 + .03):
                        M.box(P, (x, y, z0 + a + hz / 2), (.14, .06, hz * .96), self.m['cap'])
            if role == 'panel' and self.lod < 2:                # 壶门柱子
                n = max(2, int(2 * hx / .55)); hz = b - a
                for k in range(n + 1):
                    x = -hx + i0 + (2 * (hx - i0)) * k / n
                    for y in (-hy + i0 - .02, hy - i0 + .02):
                        M.box(P, (x, y, z0 + a + hz / 2), (.09, .04, hz), self.m['cap'])
        if self.lod < 2 and kind in ('stone', 'diezhe', 'xumi'):     # 角石 on the corners of the top
            s = min(.62, max(.4, H * .5)); t = s * .4
            for sx in (-1, 1):
                for sy in (-1, 1):
                    M.box(P, (sx * (hx - s / 2), sy * (hy - s / 2), z0 + H - t / 2 + .005), (s, s, t), self.m['cap'])
            if kind == 'stone':                                  # 角柱 under the 角石
                for sx in (-1, 1):
                    for sy in (-1, 1):
                        M.box(P, (sx * (hx - .1), sy * (hy - .1), z0 + H / 2), (.24, .24, H * .9), self.m['cap'])
        if self.lod < 2 and kind in ('stone', 'brick', 'diezhe') and H > .35:     # 压阑石 joints along the top edge
            for y in (-hy + .3, hy - .3):
                n = max(2, int(2 * hx / (3 * R.CHI_SONG)))
                for k in range(1, n):
                    x = -hx + 2 * hx * k / n
                    M.box(P, (x, y, z0 + H + .002), (.015, .6, .004), self.m.get('joint', self.m['body']))

    def chishou(self, hx, hy, z, count_x=2):
        """螭首 at the corners (and along the front for 殿) 【原文 卷三: 施之于殿阶对柱及四角, 随阶斜出, 长七尺】."""
        L = min(1.2, 7 * R.CHI_SONG * .45)
        for sx in (-1, 1):
            for sy in (-1, 1):
                a = math.atan2(sy, sx)
                M.beam(self.p['Platform'], (sx * hx - math.cos(a) * .2, sy * hy - math.sin(a) * .2, z - .12),
                       (sx * hx + math.cos(a) * L * .6, sy * hy + math.sin(a) * L * .6, z - .05), .22, .2, self.m['cap'])

    # -------------------------------------------------------------- steps
    def steps(self, x, y_edge, width, z_top, z_ground=0.0, kind='tadao', direction=-1, foot=None):
        """Stairs from z_top down to z_ground in front of an edge at y_edge (direction -1 = toward -Y). foot: bottom of the solid (below grade on slopes)."""
        P = self.p['Platform']; H = z_top - z_ground; zf = z_ground if foot is None else min(foot, z_ground)
        if H <= .05:
            return
        if kind == 'mandao':                                     # 慢道: 1:4 ramp with side cheeks
            L = H * 4; y1 = y_edge + direction * L
            vs = [(x - width / 2, y_edge, z_top), (x + width / 2, y_edge, z_top), (x + width / 2, y1, z_ground), (x - width / 2, y1, z_ground)]
            vs += [(vx, vy, z_ground - .05) for vx, vy, _ in vs]
            P.add(vs, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], self.m['step'])
            for sx in (-1, 1):
                M.beam(P, (x + sx * (width / 2 + .2), y_edge, z_top + .05), (x + sx * (width / 2 + .2), y1, z_ground + .05), .4, .2, self.m['cap'])
            return
        rise = 5 * CUN if kind != 'brick' else 4 * CUN; tread = 10 * CUN      # 每踏厚五寸广一尺 / 砖踏高四寸
        n = max(1, round(H / rise)); rise = H / n
        for i in range(n):
            z1 = z_ground + (i + 1) * rise; y0 = y_edge + direction * (n - i - 1) * tread; y1 = y_edge + direction * (n - i) * tread
            extra = (n - i) * tread * .7 if kind == 'ruyi' else 0.0              # 如意踏跺: steps wrap round the sides
            M.box_minmax(P, (x - width / 2 - extra, min(y0, y1), zf), (x + width / 2 + extra, max(y0, y1), z1), self.m['step'])
        if kind in ('tadao', 'brick'):                           # 副子/垂带 + 象眼 (solid cheeks)
            cw = 18 * CUN * .6 if kind == 'tadao' else 12 * CUN * .6
            L = n * tread; y1 = y_edge + direction * L
            for sx in (-1, 1):
                xo = x + sx * (width / 2 + cw / 2)
                vs = [(xo - cw / 2, y_edge, zf), (xo + cw / 2, y_edge, zf), (xo + cw / 2, y1, zf), (xo - cw / 2, y1, zf),
                      (xo - cw / 2, y_edge, z_top + .02), (xo + cw / 2, y_edge, z_top + .02), (xo + cw / 2, y1, z_ground + .08), (xo - cw / 2, y1, z_ground + .08)]
                P.add(vs, M.BOX_FACES, self.m['cap'])

    # -------------------------------------------------------------- balustrade
    def balustrade(self, pts, z, kind='dan', gaps=()):
        """钩阑 along a polyline at height z: 单钩阑 1.09 m (三尺五寸) or 重台钩阑 1.25 m (四尺); gaps = [(x0, x1)] left open at steps."""
        if kind == 'none':
            return
        part = self.p['Railings']; mat = self.m['rail']; H = (3.5 if kind == 'dan' else 4.0) * R.CHI_SONG
        seglen = (6 if kind == 'dan' else 7) * R.CHI_SONG
        for a, b in zip(pts, pts[1:]):
            L = math.dist(a[:2], b[:2])
            if L < .1:
                continue
            n = max(1, round(L / seglen))
            for k in range(n):
                t0, t1 = k / n, (k + 1) / n
                p0 = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0); p1 = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
                mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
                if any(g0 <= mid[0] <= g1 and abs(mid[1] - gy) < .6 for g0, g1, gy in gaps):
                    continue
                M.box(part, (p0[0], p0[1], z + H / 2 + .05), (.2, .2, H + .1), mat)                      # 望柱
                M.box(part, (p0[0], p0[1], z + H + .15), (.16, .16, .14), mat)                         # 柱头
                M.beam(part, (p0[0], p0[1], z + .06), (p1[0], p1[1], z + .06), .2, .12, mat)          # 地栿
                M.beam(part, (p0[0], p0[1], z + H * .55), (p1[0], p1[1], z + H * .55), .16, .08, mat)  # 盆唇
                M.beam(part, (p0[0], p0[1], z + H * .9), (p1[0], p1[1], z + H * .9), .1, .1, mat)     # 寻杖
                M.beam(part, (p0[0], p0[1], z + H * .32), (p1[0], p1[1], z + H * .32), .06, H * .4, mat)   # 华版 / 万字版
                if kind == 'chong':                                                                     # 重台: second panel + 束腰
                    M.beam(part, (p0[0], p0[1], z + H * .7), (p1[0], p1[1], z + H * .7), .1, .05, mat)
            M.box(part, (b[0], b[1], z + H / 2 + .05), (.2, .2, H + .1), mat)

    # -------------------------------------------------------------- composite
    def tier(self, hx, hy, cy, z0, H, kind):
        st = self.p['Platform'].mark(); self.block(hx, hy, z0, H, kind)
        self.p['Platform'].transform(st, M.Matrix.Translation((0, cy, 0)))

    def platform(self, W, D, H, kind, margin, *, tiers=1, front_extra=0.0, yuetai=None, steps='tadao', side_steps=False,
                 balustrade='none', slope=0.0, sanshui=True, chishou=False, step_width=None):
        """Platform around a W x D plan (front at -Y; front_extra = porch depth). Returns the top height.
        tiers: stacked platforms, each lower tier 1.2 m wider all round. yuetai = (width, depth, drop): front terrace.
        slope: ground drop toward the front (m); the platform is extended down and retained (挡土)."""
        G = 1.2; hx = W / 2 + margin; hy = D / 2 + margin; y_front = -hy - front_extra
        cy = (y_front + hy) / 2; half_y = (hy - y_front) / 2; ground = -slope if slope > .01 else 0.0
        g_all = (tiers - 1) * G
        self.site = None
        if ground < 0:                                           # 挡土台: wedge following the slope (uphill back at grade 0, front at -slope)
            ext_front = (yuetai[1] if yuetai else 0) + g_all + .3
            X = hx + g_all + .3; yf = y_front - ext_front; yb = hy + g_all + .3; bat = min(.25, .1 * slope)   # 收分 10%
            vs = [(-X, yf, ground - .3), (X, yf, ground - .3), (X, yb, -.3), (-X, yb, -.3), (-X + bat, yf + bat, 0.0), (X - bat, yf + bat, 0.0), (X - bat, yb, 0.0), (-X + bat, yb, 0.0)]
            self.p['Platform'].add(vs, M.BOX_FACES, self.m['retain'])
            M.box_minmax(self.p['Platform'], (-X + bat - .08, yf + bat - .08, -.12), (X - bat + .08, yb, .02), self.m['cap'])   # 压顶
            self.site = dict(x=X, y_front=yf, y_back=yb, slope=slope)
        Ht = H / tiers; z = 0.0
        for k in range(tiers):
            g = (tiers - 1 - k) * G
            self.tier(hx + g, half_y + g, cy, z, Ht, kind); z += Ht
        top = z; sw = step_width or min(W * .45, 3.6); foot = ground - .5 if ground < 0 else None
        start_y, start_z = y_front, top
        if yuetai:                                               # 月台: lower terrace in front, steps onto it and off it
            yw, yd, drop = yuetai; zt = top - drop
            self.tier(yw / 2, yd / 2, y_front - yd / 2, 0.0, zt, kind if kind != 'xumi' else 'stone')
            if drop > .05:
                self.steps(0, y_front, sw * .8, top, zt, 'ruyi' if steps == 'ruyi' else 'tadao')
            if balustrade != 'none':
                self.balustrade([(-yw / 2 + .12, y_front, zt), (-yw / 2 + .12, y_front - yd + .12, zt), (yw / 2 - .12, y_front - yd + .12, zt), (yw / 2 - .12, y_front, zt)],
                                zt, balustrade, gaps=[(-sw / 2 - .2, sw / 2 + .2, y_front - yd + .12)])
            start_y, start_z = y_front - yd, zt
        if steps != 'none':
            if steps == 'two':                                   # 东西两阶 (Tang/Song halls)
                for sx in (-1, 1):
                    self.steps(sx * W * .28, start_y, min(2.4, sw * .7), start_z, ground, 'tadao', foot=foot)
            else:
                self.steps(0, start_y, sw, start_z, ground, steps, foot=foot)
            if side_steps:                                       # steps on both gable ends
                for sx in (-1, 1):
                    st = self.p['Platform'].mark(); self.steps(0, -(hx + g_all), min(D * .4, 2.4), top, ground, steps if steps != 'two' else 'tadao')
                    self.p['Platform'].transform(st, M.Matrix.Translation((0, cy, 0)) @ M.Matrix.Rotation(sx * math.pi / 2, 4, 'Z'))
        if balustrade != 'none':
            X, Yb, Yf = hx - .12, hy - .12, y_front + .12
            gaps = [(sx * W * .28 - 1.4, sx * W * .28 + 1.4, Yf) for sx in (-1, 1)] if steps == 'two' else [(-sw / 2 - .2, sw / 2 + .2, Yf)]
            self.balustrade([(-X, Yf, top), (-X, Yb, top), (X, Yb, top), (X, Yf, top), (-X, Yf, top)], top, balustrade, gaps=gaps)
        if chishou and self.lod == 0:
            st = self.p['Platform'].mark(); self.chishou(hx, half_y, top)
            self.p['Platform'].transform(st, M.Matrix.Translation((0, cy, 0)))
        if sanshui:                                              # 散水 apron
            g = g_all + .7; yf = y_front - (yuetai[1] if yuetai else 0)
            M.box_minmax(self.p['Platform'], (-hx - g, yf - g, ground - .02), (hx + g, hy + g, ground + .03), self.m['apron'])
        return top


# ------------------------------------------------------------------ column bases
def column_base(part, x, y, z, col_r, kind, mat, lod=1):
    """柱础 【原文 卷三】: square plinth 2 x column diameter wide (方倍柱之径); 覆盆 rises 1/10 of the side; 仰覆莲 2/10.
    kinds: su 素平 | fupen 覆盆 | lian 仰覆莲华 | zhi 櫍 (drum under the column) | gu 鼓镜 (Ming-Qing) | tall 高柱础 (Lingnan/Minnan)."""
    s = 4 * col_r                                               # 方倍柱之径
    M.box(part, (x, y, z + .03), (s, s, .06), mat)               # exposed top of the plinth
    if kind == 'su' or lod >= 2:
        return z + .06
    if kind in ('fupen', 'lian'):
        hh = s * (.1 if kind == 'fupen' else .2)
        rr = [col_r * 1.75, col_r * 1.6, col_r * 1.3, col_r * 1.08]
        M.tube(part, [(x, y, z + .06), (x, y, z + .06 + hh * .4), (x, y, z + .06 + hh * .8), (x, y, z + .06 + hh)], col_r, mat, 16, radii=rr)
        if kind == 'lian' and lod == 0:                         # lotus petals
            n = 12
            for k in range(n):
                a = math.tau * k / n
                M.box(part, (x + math.cos(a) * col_r * 1.45, y + math.sin(a) * col_r * 1.45, z + .06 + hh * .35), (col_r * .55, col_r * .3, hh * .5), mat, a)
        return z + .06 + hh
    if kind == 'zhi':                                           # 櫍: wider drum (each side +3 分, 10 分 thick) 【原文 卷五】
        M.tube(part, [(x, y, z + .06), (x, y, z + .06 + col_r * .55)], col_r * 1.22, mat, 14)
        return z + .06 + col_r * .55
    if kind == 'gu':
        M.tube(part, [(x, y, z + .06), (x, y, z + .06 + col_r * .35), (x, y, z + .06 + col_r * .5)], col_r, mat, 14, radii=[col_r * 1.5, col_r * 1.45, col_r * 1.15])
        return z + .06 + col_r * .5
    if kind == 'tall':                                          # 高柱础: octagonal stone pedestal against damp (岭南/闽南)
        h = max(.35, col_r * 3)
        vs = []
        for zz, r in ((z + .06, col_r * 1.5), (z + .06 + h * .2, col_r * 1.3), (z + .06 + h * .8, col_r * 1.25), (z + .06 + h, col_r * 1.1)):
            vs.append([(x + r * math.cos(math.tau * (k + .5) / 8), y + r * math.sin(math.tau * (k + .5) / 8), zz) for k in range(8)])
        for a, b in zip(vs, vs[1:]):
            part.add(a + b, [(i, (i + 1) % 8, 8 + (i + 1) % 8, 8 + i) for i in range(8)], mat)
        part.add(vs[-1], [tuple(range(8))], mat)
        return z + .06 + h
    return z + .06
