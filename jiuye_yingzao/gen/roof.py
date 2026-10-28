# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Roofs.

One height model for every form: z = base + Section.z(t) + corner lift (起翘) + 生起, where t runs from the ridge
(0) to the outer eave edge (1). Faces are patches of two kinds:
  * ring faces  - four trapezoids between an inner rectangle (half extents A-B(1-t_in), B t_in) and the eave
                  rectangle (A, B); hips at 45 deg, so adjoining faces share their hip edges exactly.
                  四阿/庑殿 t_in=0; 盝顶 t_in>0 plus a flat top; 九脊/歇山 lower part; 副阶/缠腰 (skirt).
  * gable faces - front/back slopes between the ridge and the eave over a constant x half-extent.
                  不厦两头/悬山, 硬山, 卷棚, 九脊 upper part.
  * polygon faces for 斗尖/攒尖 (n sides, or round).
Tiles are a displacement of the top surface (no per-tile objects): 筒瓦 bumps, 合瓦 waves, 石板 steps, 茅草 slab.
Rule sources: core/rules.py (《营造法式》卷五 举折/檐/出际/角梁, 卷十三 用瓦/鸱尾/兽头).
"""
import math

from ..core import mesh as M
from ..core import rules as R


def smooth01(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


class RoofModel:
    def __init__(self, form, a0, b0, z0, section, eave_total, *, corner_lift=0.0, corner_out=0.0, shengqi=0.0,
                 chuji=0.0, gable_at=None, flat_t=0.0, sides=4, tile='tube', tile_pitch=0.26, lod=1,
                 ridge='chiwei', ridge_h=0.5, hip_beasts=0, materials=None, gable='open', wall_t=0.36):
        self.form = form; self.a0 = a0; self.b0 = b0; self.z0 = z0; self.sec = section
        self.B = section.b; self.A = a0 + eave_total
        self.lift = corner_lift; self.out = corner_out; self.shengqi = shengqi; self.chuji = chuji
        self.gable_at = gable_at; self.flat_t = flat_t; self.sides = sides
        self.tile = tile; self.pitch = tile_pitch; self.lod = lod; self.ridge = ridge; self.ridge_h = ridge_h
        self.beasts = hip_beasts; self.gable = gable; self.wall_t = wall_t
        self.m = {'tile': 'tile_grey', 'ridge': 'tile_dark', 'timber': 'wood_dark', 'soffit': 'wood', 'board': 'ochre', 'gable_wall': 'plaster_white'}
        self.m.update(materials or {})
        if tile == 'bamboo':
            self.pitch = .2
        self.R = self.A - self.B                      # hip ridge half-length (ring forms)

    # ---------------------------------------------------------------- height model
    def lift_at(self, x, y):
        if not self.lift or self.form in ('cuanjian', 'yuan'):     # polygon roofs lift at facet corners (poly_z)
            return 0.0
        gx = smooth01((abs(x) / self.A - .45) / .55); gy = smooth01((abs(y) / self.B - self.sec.te * .55) / (1 - self.sec.te * .55))
        return self.lift * (gx * gy) ** 1.6

    def z(self, x, y, t, off=0.0):
        sq = self.shengqi * (min(1.0, abs(x) / max(self.a0, 1e-6))) ** 2
        return self.z0 + self.sec.z(t) + self.lift_at(x, y) + sq + off

    def displace(self, x, y):
        """生出: eave line pushed out toward the corners (plan)."""
        if not self.out:
            return x, y
        gx = smooth01((abs(x) / self.A - .5) / .5); gy = (abs(y) / self.B) ** 3
        y2 = y + math.copysign(self.out * gx * gy, y)
        if self.form in ('wudian', 'xieshan', 'luding', 'skirt'):
            hx = smooth01((abs(y) / self.B - .5) / .5); hy = (abs(x) / self.A) ** 3
            x = x + math.copysign(self.out * hx * hy, x)
        return x, y2

    # ---------------------------------------------------------------- tile relief
    def relief(self, along, t, face_len):
        """Tile displacement (metres, along the surface normal ~ up) at a world coordinate across the slope."""
        if self.lod >= 2 or self.tile in ('flat', 'thatch'):
            return 0.0
        p = self.pitch; ph = (along / p) % 1.0
        if self.tile == 'tube':                          # 筒瓦: round cover tile every pitch over a concave 板瓦 channel
            c = abs(ph - .5) * 2                          # 0 at cover-tile centre
            cover = .34 * p * math.sqrt(max(0.0, 1 - (c / .42) ** 2)) if c < .42 else 0.0
            return max(cover, -.05 * p * math.cos(math.pi * c))
        if self.tile == 'combo':                          # 合瓦: alternating convex/concave 板瓦
            return .10 * p * math.cos(math.tau * ph)
        if self.tile == 'slate':                          # 石板: overlapping courses down the slope
            return .03 * ((t * face_len / .35) % 1.0)
        if self.tile == 'bark':                           # 树皮: wide overlapping sheets
            return .025 * ((t * face_len / .6) % 1.0)
        if self.tile == 'bamboo':                         # 剖竹瓦: half-bamboo tubes laid alternately up and down
            return .07 * p * abs(math.sin(math.pi * ph)) * (1 if int(along / p) % 2 else -.6)
        return 0.0

    # ---------------------------------------------------------------- faces
    def faces(self):
        """Yield (name, point(u, v) -> (x, y, t, along, face_len), nu, nv)."""
        A, B = self.A, self.B
        f = self.form
        if f in ('wudian', 'luding', 'skirt', 'xieshan'):
            t_in = self.flat_t if f in ('luding', 'skirt') else (self._xs_t() if f == 'xieshan' else 0.0)
            for name, sx, sy in [('front', 0, -1), ('back', 0, 1), ('left', -1, 0), ('right', 1, 0)]:
                yield from self._ring_face(name, sx, sy, t_in)
            if f == 'xieshan':
                for sign, nm in [(-1, 'front_top'), (1, 'back_top')]:
                    yield from self._gable_face(nm, sign, self._xs_g() + self._xs_og(), 0.0, self._xs_t())
        elif f in ('xuanshan', 'yingshan', 'juanpeng', 'juanpeng_ying'):
            half = self.a0 + (self.chuji if f in ('xuanshan', 'juanpeng') else self.wall_t * .6)
            for sign, nm in [(-1, 'front'), (1, 'back')]:
                yield from self._gable_face(nm, sign, half, 0.0, 1.0)
        elif f == 'danpo':
            half = self.a0 + self.chuji
            yield from self._gable_face('slope', -1, half, 0.0, 1.0, single=True)
        elif f in ('cuanjian', 'yuan'):
            n = 24 if f == 'yuan' else self.sides
            for k in range(n):
                yield from self._poly_face(k, n, self.flat_t)

    def _xs_g(self):
        return self.gable_at if self.gable_at is not None else max(.3, self.a0 - 2 * self.b0 / 3)

    def _xs_t(self):
        return max(.08, min(.9, (self._xs_g() - self.R) / self.B))

    def _xs_og(self):
        return min(.6, self.chuji) if self.chuji else .35

    def _ring_face(self, name, sx, sy, t_in):
        A, B = self.A, self.B

        def pt(u, v):
            t = t_in + (1 - t_in) * v
            if sy:   # front/back: along x
                half = self.R + B * t; x = (2 * u - 1) * half; y = sy * B * t
                return x, y, t, x, 2 * half
            half = B * t; y = (2 * u - 1) * half; x = sx * (self.R + B * t)
            return x, y, t, y, 2 * half
        nu = self._nu(2 * A if sy else 2 * B); nv = self._nv(1 - t_in)
        yield name, pt, nu, nv

    def _gable_face(self, name, sign, half, t0, t1, single=False):
        B = self.B

        def pt(u, v):
            t = t0 + (t1 - t0) * v; x = (2 * u - 1) * half
            y = sign * B * t if not single else self.b0 / 2 - B * t     # 单坡: back wall at +b0/2, eave toward -y
            return x, y, t, x, 2 * half
        yield name, pt, self._nu(2 * half), self._nv(t1 - t0)

    def _poly_face(self, k, n, t_in=0.0):
        B = self.B; ang = math.tau * k / n; ca, sa = math.cos(ang), math.sin(ang); tan = math.tan(math.pi / n)   # facet faces the axis; corners at (k+.5)/n

        def pt(u, v):
            t = t_in + (1 - t_in) * v; r = B * t; along = (2 * u - 1) * r * tan
            x = r * ca - along * sa; y = r * sa + along * ca
            return x, y, t, along, 2 * B * tan
        yield f'facet{k}', pt, self._nu(2 * B * tan), self._nv(1.0)

    def _nu(self, length):
        if self.lod >= 2 or self.tile in ('flat', 'thatch', 'slate', 'bark'):
            return max(4, int(length / 1.2))
        per = 6 if self.lod == 0 else 4
        return max(4, int(length / self.pitch * per))

    def _nv(self, frac):
        return max(4, int(frac * (16 if self.lod < 2 else 8)))

    def poly_z(self, x, y, t):
        """Corner lift for polygon roofs follows the facet corners."""
        if self.form not in ('cuanjian', 'yuan') or not self.lift or self.form == 'yuan':
            return 0.0
        n = self.sides; seg = math.tau / n; ang = math.atan2(y, x) % seg; c = 1 - abs(ang / seg * 2 - 1)  # 1 at corner lines
        return self.lift * smooth01((c - .55) / .45) ** 2 * smooth01((t - .55) / .45)

    # ---------------------------------------------------------------- build
    def build(self, roof_part, timber_part, wall_part):
        thick = {'thatch': .32, 'bark': .1, 'bamboo': .14}.get(self.tile, .16 if self.lod < 2 else .12)
        for name, pt, nu, nv in self.faces():
            def top(u, v, pt=pt):
                x, y, t, along, length = pt(u, v)
                z = self.z(x, y, t) + self.poly_z(x, y, t) + self.relief(along, t, self.B)
                if self.form in ('luding',) and t <= self.flat_t + 1e-9:
                    pass
                dx, dy = self.displace(x, y)
                return dx, dy, z + thick
            M.shell(roof_part, nu, nv, top, thick, self.m['tile'], self.m['soffit'], smooth=self.tile != 'slate')
            if self.m.get('trim') and self.tile in ('tube', 'combo') and not name.endswith('_top'):
                self._trim(roof_part, pt, nu, top)
            if self.lod < 2 and not name.endswith('_top'):
                self._eave_details(pt, roof_part, timber_part, name)
        if self.form == 'luding':
            self._flat_top(roof_part)
        self._ridges(roof_part)
        self._gables(roof_part, timber_part, wall_part)

    def _trim(self, part, pt, nu, top):
        """剪边: a band of glazed tiles along the eave (about three tile courses), laid just over the main tiles."""
        t_in = pt(.5, 0.0)[2]; band = min(.25, 1.0 / self.B)
        v0 = max(0.0, (1 - band - t_in) / max(1e-6, 1 - t_in))

        def strip(u, w):
            x, y, z = top(u, v0 + (1 - v0) * w); return x, y, z + .015
        M.shell(part, nu, 3, strip, .02, self.m['trim'], self.m['trim'], smooth=True)

    def _flat_top(self, part):
        t = self.flat_t; hx = self.R + self.B * t; hy = self.B * t; z = self.z(0, 0, t) + .16
        M.box_minmax(part, (-hx, -hy, z - .16), (hx, hy, z), self.m['ridge'])

    def _eave_details(self, pt, roof_part, timber, name):
        """Fascia (连檐) along the eave; LOD0 adds exposed rafter/飞子 ends and 瓦当 at the cover tiles."""
        n = 24; edge = []
        for i in range(n + 1):
            x, y, t, along, L = pt(i / n, 1.0)
            dx, dy = self.displace(x, y); edge.append((dx, dy, self.z(x, y, t) + self.poly_z(x, y, t) - .02))
        M.tube(timber, edge, .06, self.m['timber'], 6)
        if self.lod > 0:
            return
        t_in = pt(.5, 0.0)[2]; te = self.sec.te
        v_in = max(0.0, (te * .97 - t_in) / max(1e-6, 1 - t_in))
        a0 = pt(0.0, 1.0)[3]; a1 = pt(1.0, 1.0)[3]; span = abs(a1 - a0)
        cnt = max(2, int(span / .30))
        for i in range(cnt):                                   # rafter ends under the eave, lying on the soffit
            u = (i + .5) / cnt; ps = []
            for v in (v_in, 1.0):
                x, y, t, al, _ = pt(u, v); dx, dy = self.displace(x, y)
                ps.append((dx, dy, self.z(x, y, t) + self.poly_z(x, y, t) - .06))
            M.tube(timber, ps, .05, self.m['timber'], 5, smooth=False)
        if self.tile not in ('tube', 'combo') or name.startswith('facet'):
            return
        ax, ay = (0.0, -1.0) if name == 'front' else (0.0, 1.0) if name == 'back' else (-1.0, 0.0) if name == 'left' else (1.0, 0.0) if name == 'right' else (0.0, -1.0)
        cnt = max(2, int(span / self.pitch))
        for i in range(cnt):                                   # 瓦当 discs on the cover-tile columns
            along = min(a0, a1) + (i + .5) * span / cnt
            u = (along - a0) / (a1 - a0) if a1 != a0 else .5
            if not 0 <= u <= 1:
                continue
            x, y, t, al, _ = pt(u, 1.0); dx, dy = self.displace(x, y)
            z = self.z(x, y, t) + .16 + self.relief(al, t, self.B) * .6
            M.tube(roof_part, [(dx - ax * .03, dy - ay * .03, z), (dx + ax * .03, dy + ay * .03, z)], self.pitch * .28, self.m['tile'], 8)

    # ---------------------------------------------------------------- ridges
    def _ridges(self, part):
        m = self.m['ridge']; h = self.ridge_h; f = self.form; B = self.B
        if f == 'skirt':          # 副阶/缠腰: hips plus a flashing ridge where the skirt meets the wall
            t_in = self.flat_t; hx = self.R + B * t_in; hy = B * t_in
            for a, b in [((-hx, -hy), (hx, -hy)), ((hx, -hy), (hx, hy)), ((hx, hy), (-hx, hy)), ((-hx, hy), (-hx, -hy))]:
                z = self.z(a[0], a[1], t_in) + .14
                M.beam(part, (a[0], a[1], z), (b[0], b[1], z), .22, .22, m)
        if f in ('wudian', 'xieshan', 'luding', 'skirt'):
            t_in = self.flat_t if f in ('luding', 'skirt') else 0.0
            if f == 'luding':     # 围脊 around the flat top
                hx = self.R + B * t_in; hy = B * t_in; z = self.z(0, 0, t_in) + .2
                for a, b in [((-hx, -hy), (hx, -hy)), ((hx, -hy), (hx, hy)), ((hx, hy), (-hx, hy)), ((-hx, hy), (-hx, -hy))]:
                    M.beam(part, (a[0], a[1], z + .1), (b[0], b[1], z + .1), .3, .3, m)
            # hips (垂脊 / 戗脊)
            t_from = self._xs_t() if f == 'xieshan' else t_in
            for sx in (-1, 1):
                for sy in (-1, 1):
                    pts = []
                    for k in range(17):
                        t = t_from + (1 - t_from) * k / 16
                        x = sx * (self.R + B * t); y = sy * B * t; dx, dy = self.displace(x, y)
                        pts.append((dx, dy, self.z(x, y, t) + .2 + .08 * (1 - t)))
                    self._ridge_strip(part, pts, h * .45, m)
                    if self.lod == 0 and self.beasts:
                        self._beasts(part, pts, self.beasts)
        if f in ('wudian', 'xieshan', 'xuanshan', 'yingshan'):
            half = self.R if f == 'wudian' else (self._xs_g() + self._xs_og() * .6 if f == 'xieshan' else self.a0 + (self.chuji if f == 'xuanshan' else self.wall_t * .6))
            if half > .05:
                zr = lambda x: self.z(x, 0, 0) + .12
                pts = [(-half + 2 * half * k / 24, 0, zr(-half + 2 * half * k / 24)) for k in range(25)]
                self._main_ridge(part, pts, h, m)
        if f in ('xuanshan', 'yingshan', 'juanpeng', 'juanpeng_ying', 'xieshan'):   # 垂脊 along the gable edges (排山)
            half = (self._xs_g() + self._xs_og()) if f == 'xieshan' else self.a0 + (self.chuji if f in ('xuanshan', 'juanpeng') else self.wall_t * .6)
            t_end = self._xs_t() if f == 'xieshan' else 1.0
            for sx in (-1, 1):
                for sy in (-1, 1):
                    pts = [(sx * half, sy * B * t_end * k / 12, self.z(sx * half, sy * B * t_end * k / 12, t_end * k / 12) + .17) for k in range(13)]
                    self._ridge_strip(part, pts, h * .35, m)
        if f == 'xieshan':      # 博脊 at the base of the gable
            G = self._xs_g(); tg = self._xs_t()
            for sx in (-1, 1):
                pts = [(sx * G, -B * tg + 2 * B * tg * k / 10, self.z(sx * G, 0, tg) + .12) for k in range(11)]
                M.tube(part, pts, .12, m, 6)
        if f in ('cuanjian', 'yuan'):
            n = 0 if f == 'yuan' else self.sides
            for k in range(n):
                ang = math.tau * (k + .5) / n; pts = []
                for j in range(13):
                    t = self.flat_t + (1 - self.flat_t) * j / 12; r = B * t / math.cos(math.pi / n); x = r * math.cos(ang); y = r * math.sin(ang)
                    pts.append((x, y, self.z(x, y, t) + self.poly_z(x * .999, y * .999, t) + .18))
                self._ridge_strip(part, pts, h * .4, m)
            if self.flat_t <= 0:
                self._finial(part, self.z(0, 0, 0))
        if f == 'juanpeng' or f == 'juanpeng_ying':
            return

    def _ridge_strip(self, part, pts, h, m):
        prof = [(-.13, -.05), (.13, -.05), (.13, h * .7), (0, h), (-.13, h * .7)]
        M.sweep(part, prof, pts, m, caps=True)

    def _main_ridge(self, part, pts, h, m):
        prof = [(-.17, -.08), (.17, -.08), (.17, h * .85), (.1, h), (-.1, h), (-.17, h * .85)]
        M.sweep(part, prof, pts, m, caps=True)
        if self.lod < 2:
            ends = [pts[0], pts[-1]]
            for sign, p in zip((-1, 1), ends):
                self._ridge_end(part, p, sign, h)

    def _ridge_end(self, part, p, sign, h):
        kind = self.ridge
        mat = self.m.get('ornament', self.m['ridge'])
        if kind == 'chiwei':        # 鸱尾: tall hooked tail curving inward (Tang/Song)
            H = max(.6, h * 2.6)
            out = [(0, 0), (.42, 0), (.46, .25), (.34, .55), (.22, .78), (.30, 1.0), (.18, 1.02), (.02, .84), (-.14, .92),
                   (-.20, .80), (-.08, .62), (-.04, .30), (-.10, .12)]
            out = [(u * H * sign * -1, v * H) for u, v in out]
            if sign > 0:
                out = list(reversed(out))
            M.extrude_profile(part, out, .22, mat, M.place(p[0] + sign * .05, p[1], p[2] + h * .35))
        elif kind == 'shoutou':     # 兽头: compact beast-head block on the ridge end
            M.box(part, (p[0] + sign * .05, p[1], p[2] + h * .9), (.36, .30, h * 1.1), mat)
            M.box(part, (p[0] + sign * .14, p[1], p[2] + h * 1.35), (.22, .24, .26), mat)
        elif kind == 'swallow':     # 燕尾: raised, forked ridge tail (闽南)
            base = (p[0], p[1], p[2] + h * .5)
            tip = (p[0] + sign * .7, p[1], p[2] + h * 1.9)
            M.tube(part, [base, (p[0] + sign * .35, p[1], p[2] + h * .9), tip], .09, mat, 6)
            for fy in (-1, 1):
                M.tube(part, [tip, (tip[0] + sign * .25, tip[1] + fy * .22, tip[2] + .35)], .06, mat, 6)
        elif kind == 'curl':        # 江南 纹头/哺鸡 style curl
            M.tube(part, [(p[0], p[1], p[2] + h * .6), (p[0] + sign * .3, p[1], p[2] + h * 1.2), (p[0] + sign * .2, p[1], p[2] + h * 1.6), (p[0] + sign * .05, p[1], p[2] + h * 1.45)], .08, mat, 6)
        elif kind == 'qing_wen':    # 清式正吻 (kept as an option; not used by default styles)
            M.box(part, (p[0] - sign * .05, p[1], p[2] + h * 1.4), (.5, .3, h * 2.2), mat)
        elif kind == 'raised':      # 民居: ends simply raised (起翘脊头)
            M.tube(part, [(p[0] - sign * .25, p[1], p[2] + h * .8), (p[0] + sign * .15, p[1], p[2] + h * 1.25)], .08, mat, 6)

    def _beasts(self, part, pts, count):
        """嫔伽/蹲兽: small figures near the lower end of hips (【原文 卷十三】 counts by building size)."""
        n = len(pts)
        for k in range(count):
            p = pts[n - 3 - k] if n - 3 - k >= 0 else pts[0]
            M.box(part, (p[0], p[1], p[2] + .3), (.14, .14, .2), self.m['ridge'])

    def _finial(self, part, z):
        rings = [(.32, 0), (.38, .12), (.2, .3), (.3, .42), (.14, .6), (.22, .7), (.06, 1.0), (.02, 1.4)]
        for (r0, z0), (r1, z1) in zip(rings, rings[1:]):
            n = 12; vs = [(r * math.cos(math.tau * i / n), r * math.sin(math.tau * i / n), z + zz) for r, zz in ((r0, z0), (r1, z1)) for i in range(n)]
            part.add(vs, [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)] + [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))], self.m.get('ornament', 'bronze'))

    # ---------------------------------------------------------------- gables
    def _gables(self, roof_part, timber, walls):
        f = self.form; B = self.B
        if f in ('xuanshan', 'juanpeng', 'xieshan'):
            if f == 'xieshan':
                xb = self._xs_g() + self._xs_og(); xs = self._xs_g(); t_end = self._xs_t()
            else:
                xb = self.a0 + self.chuji; xs = self.a0; t_end = 1.0
            for sx in (-1, 1):
                # 搏风版 along the gable edge 【原文 卷五 广两材至三材】
                pts = [(sx * (xb + .03), -B * t_end + 2 * B * t_end * k / 24, 0) for k in range(25)]
                pts = [(x, y, self.z(x, y, abs(y) / B) - .05) for x, y, _ in pts]
                M.sweep(timber, [(-.04, -.32), (.04, -.32), (.04, .06), (-.04, .06)], pts, self.m['board'])
                if self.lod < 2:            # 悬鱼 at the apex, 惹草 at the purlin ends
                    apex = (sx * (xb + .06), 0, self.z(sx * xb, 0, 0) - .3)
                    fish = [(-.18, 0), (.18, 0), (.22, -.35), (.12, -.75), (0, -.95), (-.12, -.75), (-.22, -.35)]
                    M.extrude_profile(timber, fish, .05, self.m['board'], M.place(apex[0], 0, apex[2], math.pi / 2))
                if f == 'xieshan' or self.gable == 'shanhua':     # 山花 (gable triangle) closed with boards
                    tri = []
                    for k in range(13):
                        y = -B * t_end + 2 * B * t_end * k / 12; tri.append((y, self.z(sx * xs, y, abs(y) / B) - .1))
                    zb = self.z(sx * xs, B * t_end, t_end) - .1
                    outline = [(y, z) for y, z in tri] + [(B * t_end, zb), (-B * t_end, zb)]
                    outline = [(y, z) for y, z in outline]
                    M.extrude_profile(walls, [(y, z - zb) for y, z in outline], .08, self.m['board'], M.place(sx * (xs + .05), 0, zb, math.pi / 2))

    # helper for walls/frames: roof underside height at (x, y)
    def underside(self, x, y):
        f = self.form; B = self.B
        if f in ('wudian', 'luding', 'skirt'):
            t = max(abs(y) / B, (abs(x) - self.R) / B)
        elif f == 'xieshan':
            t = abs(y) / B if abs(x) <= self._xs_g() else max(abs(y) / B, (abs(x) - self.R) / B)
        elif f in ('cuanjian', 'yuan'):
            t = math.hypot(x, y) / B
        elif f == 'danpo':
            t = (self.b0 / 2 - y) / B
        else:
            t = abs(y) / B
        return self.z(x, y, min(1.0, max(0.0, t)))
