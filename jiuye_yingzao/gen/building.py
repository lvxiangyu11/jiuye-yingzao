# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Single buildings: type (data/types.json) x style (data/styles.json) x seed -> spec -> meshes.

Frame: X along the front, front facade at -Y, Z up, origin at ground under the plan centre.
Assembly order: platform -> per floor (columns 生起/侧脚/梭柱, 阑额/普拍方, walls + openings, 平坐, 腰檐)
-> 铺作 -> roof (gen/roof.py) -> gables -> 副阶 -> extras. Parts are merged per component (core/mesh.Part).
"""
import json
import math
import random
import zlib
from pathlib import Path

import bpy

from ..core import materials, mesh as M, rules as R
from . import parts as P
from .roof import RoofModel
from . import foundation as FD

DATA = Path(__file__).resolve().parents[1] / 'data'


def load(name):
    return {k: v for k, v in json.loads((DATA / name).read_text(encoding='utf-8')).items() if not k.startswith('_')}


TYPES = load('types.json')
STYLES = load('styles.json')


def U(rng, r):
    return r[0] if r[0] == r[1] else rng.uniform(*r)


def I(rng, r):
    return rng.randint(int(r[0]), int(r[1]))


# ------------------------------------------------------------------ spec
def resolve(type_key, style_key=None, seed=0, **over):
    t = TYPES[type_key]; rng = random.Random(seed * 7919 + zlib.crc32(type_key.encode()) % 10007)
    if style_key in (None, 'auto'):
        cands = [s for s in t['styles'] if not STYLES[s].get('deemphasized')]
        style_key = rng.choice(cands)
    st = STYLES[style_key]; off = t['official']
    bays = over.get('bays', I(rng, t['bays']))
    bw = over.get('bay_w', U(rng, t['bay_w']))
    widths = [bw * (1.0 if abs(i - (bays - 1) / 2) < .6 else .9 if abs(i - (bays - 1) / 2) < 1.6 else .82) for i in range(bays)]
    jia = over.get('jia', 2 * I(rng, [t['jia'][0] // 2, t['jia'][1] // 2]))
    jl = over.get('jia_len', U(rng, t['jia_len']))
    roof = over.get('roof') or (rng.choice(t['roof']) if over.get('random_roof') else t['roof'][0])
    if t.get('polygon') and roof not in ('cuanjian', 'yuan'):
        roof = 'cuanjian'
    if style_key == 'loess':
        roof = 'pingding'
    floors = over.get('floors', I(rng, t['floors']))
    # materials use their own random stream, so adding options never changes a seed's geometry
    mrng = random.Random(seed * 104723 + zlib.crc32((type_key + str(style_key)).encode()) % 99991)
    def pick(key_over, type_opts, style_opts, fallback):
        if over.get(key_over):
            return over[key_over]
        opts = t.get(type_opts) or st.get(style_opts)
        return mrng.choice(opts) if opts else fallback
    tile = over.get('tile') or (mrng.choice(t['tile_options']) if t.get('tile_options') else None) or t.get('tile') or         (mrng.choice(st['tile_kind_options']) if st.get('tile_kind_options') and not off else None) or st['tile']['official' if off else 'house']
    ridge = over.get('ridge') or st['ridge']['official' if off else 'house']
    if tile == 'thatch':
        ridge = 'plain'
    gable = over.get('gable') or st['gable']
    if roof == 'xuanshan' and gable in ('horse', 'wok', 'yingshan'):
        roof = 'yingshan'
    if roof in ('yingshan', 'juanpeng_ying') and gable == 'open':
        gable = 'brick'
    b = st['bracket']; lv = min(I(rng, t['brackets']), b['max_levels']) if b['kind'] in ('song', 'simple') else 0
    bkind = b['kind'] if lv > 0 or b['kind'] == 'simple' and I(rng, t['brackets']) > 0 else 'none'
    if bkind == 'simple':
        lv = 1
    cls = t['cls']; grade = R.grade_for(cls, bays); fen = R.fen(grade)
    spec = dict(type=type_key, label=t['label'], style=style_key, style_label=st['label'], seed=seed, cls=cls, official=off,
                bays=bays, widths=widths, jia=jia, jia_len=jl, depth=jia * jl, col_h=over.get('col_h', U(rng, t['col_h'])),
                floors=floors, roof=roof, tile=tile, ridge=ridge, gable=gable, brackets=lv, bracket_kind=bkind,
                bujian=b.get('bujian', 0), grade=grade, fen=fen,
                porch=rng.random() < t.get('porch', 0), fujie=rng.random() < t.get('fujie', 0),
                pingzuo=rng.random() < t.get('pingzuo', 0), yaoyan=rng.random() < t.get('yaoyan', 0),
                balcony=rng.random() < t.get('balcony', 0), awning=rng.random() < t.get('awning', 0),
                sign=rng.random() < t.get('sign', 0), lanterns=rng.random() < t.get('lanterns', 0),
                railing=rng.random() < t.get('railing', 0), chimney=rng.random() < t.get('chimney', 0),
                vents=t.get('vents', 0) > 0, well=t.get('well', 0) > 0, stele=t.get('stele', 0) > 0,
                base_tower=t.get('base_tower', 0) > 0, hanging_posts=t.get('hanging_posts', 0) > 0,
                furniture=t.get('furniture'), sides_n=t.get('sides_n', 4), polygon=t.get('polygon', False),
                front=t['front'], back=t['back'], sides=t['sides'],
                platform_h=U(rng, t['platform_h']), stilts=U(rng, t['stilts']) if 'stilts' in t else st.get('stilts', 0.0),
                wall=pick('wall', 'wall_options', 'wall_options', t.get('wall') or st['wall']),
                wall_low=pick('wall_low', None, 'wall_low_options', st['wall_low']),
                tile_mat=pick('tile_mat', 'tile_mat_options', 'tile_mat_options', st['tile_mat']),
                trim=over.get('trim', mrng.choice(st['trim_options']) if st.get('trim_options') and off else ''),
                lod=over.get('lod', 1))
    TILE_MAT = {'thatch': ['thatch', 'thatch_old'], 'slate': ['slate', 'slate_scale', 'slate_shingle'], 'bark': ['bark_roof'], 'bamboo': ['bamboo_roof']}
    if spec['tile'] in TILE_MAT and not over.get('tile_mat') and spec['tile_mat'] not in TILE_MAT[spec['tile']]:
        spec['tile_mat'] = mrng.choice(TILE_MAT[spec['tile']])
    if spec['tile'] in ('thatch', 'bark', 'bamboo'):
        spec['ridge'] = 'plain'
    spec.update(foundation_choice(t, st, style_key, spec, mrng, over))
    spec['pitch_ratio'] = float(over.get('pitch_ratio', 0.0))      # explicit rise / half-depth override
    spec.update({k: v for k, v in over.items() if k in spec and k not in ('bays', 'bay_w')})
    spec['W'] = sum(spec['widths']); spec['D'] = spec['depth']
    return spec, st


# ------------------------------------------------------------------ foundations
FOUND_BY_PLATFORM = {'stone': ['stone', 'stone', 'rubble'], 'brick': ['brick', 'tamped'], 'earth': ['earth', 'tamped'], 'xumi': ['xumi', 'diezhe'], 'none': ['none']}
FOUND_MATS = {   # body / cap options per platform kind
    'stone': (['ashlar_grey', 'stone_block', 'ashlar_moss', 'stone'], ['stone_carved', 'stone_carved_dark']),
    'brick': (['brick_grey', 'brick_grey_old'], ['stone_carved', 'stone_carved_dark']),
    'tamped': (['brick_grey_old', 'brick_grey'], ['stone_carved', 'stone_carved_dark']),
    'earth': (['earth_rammed', 'earth_loess'], ['earth_rammed']),
    'rubble': (['wall_rubble', 'wall_pebble', 'wall_slate_dry'], ['stone_carved_dark', 'stone']),
    'diezhe': (['stone_carved'], ['stone_carved']),
    'xumi': (['stone_carved', 'brick_grey'], ['stone_carved']),
}
COLUMN_BASE = {'song': 'fupen', 'tang': 'fupen', 'liaojin': 'fupen', 'daoguan': 'fupen', 'lanxi': 'fupen', 'ming': 'gu', 'qing': 'gu',
               'north_folk': 'su', 'loess': 'su', 'jiangnan': 'gu', 'hui': 'gu', 'lingnan': 'tall', 'minnan': 'tall', 'chuan': 'su', 'ganlan': 'su', 'hakka': 'su'}


def foundation_choice(t, st, style_key, spec, rng, over):
    """台基 kind, tiers, 月台, 踏道, 钩阑, 螭首, 柱础 for a building; all drawn from the material random stream."""
    cls = t['cls']; off = t['official']; H = spec['platform_h']; plat = st.get('platform', 'stone')
    kinds = t.get('found_options') or FOUND_BY_PLATFORM.get(plat, ['stone'])
    if off and cls == 'dian' and plat in ('stone', 'xumi'):
        kinds = ['diezhe', 'xumi', 'stone']                     # 殿阶基 叠涩坐 / 须弥座 for halls
    kind = over.get('found') or rng.choice(kinds)
    if spec.get('stilts') or spec.get('base_tower') or H <= .01:
        kind = 'none'
    elif kind == 'none':
        kind = 'stone'                                           # never leave a raised floor without a platform
    bodies, caps = FOUND_MATS.get(kind, (['stone'], ['stone_light']))
    tiers = over.get('found_tiers') or (rng.choice([1, 1, 2]) if cls == 'dian' and H >= 1.0 else 1)
    yuetai = None
    if 'yuetai' in over:
        yuetai = over['yuetai']
    elif off and cls in ('dian', 'ting') and t.get('front') in ('all_doors', 'open') and rng.random() < .5:
        yuetai = 'auto'
    steps = over.get('steps') or ('two' if cls == 'dian' and style_key in ('tang', 'song', 'liaojin') and rng.random() < .4 else
                                  'ruyi' if cls == 'yuwu' and rng.random() < .4 else 'brick' if plat == 'brick' else 'tadao')
    bal = over.get('balustrade') or ('chong' if cls == 'dian' and H >= 1.2 and rng.random() < .5 else
                                     'dan' if cls in ('dian',) and H >= .9 or (off and cls == 'ting' and H >= .8 and rng.random() < .3) else 'none')
    return dict(found=kind, found_body=over.get('found_body') or rng.choice(bodies), found_cap=over.get('found_cap') or rng.choice(caps),
                found_tiers=tiers, yuetai=yuetai, steps=steps, side_steps=over.get('side_steps', cls == 'dian' and rng.random() < .3),
                balustrade=bal, chishou=cls == 'dian' and kind in ('diezhe', 'xumi'), slope=over.get('slope', 0.0),
                column_base=over.get('column_base') or ('lian' if cls == 'dian' and COLUMN_BASE.get(style_key) == 'fupen' else COLUMN_BASE.get(style_key, 'su')))


# wall thickness by material (m) 【推定】: earth 0.45–0.6, masonry 0.36–0.5, timber-framed infill 0.12–0.16
WALL_T = {'earth_rammed': .55, 'earth_red': .55, 'earth_loess': .6, 'adobe': .45, 'straw_clay': .45, 'mud_smooth': .42,
          'brick_grey': .36, 'brick_red': .36, 'brick_grey_old': .36, 'brick_grey_moss': .36, 'brick_red_old': .36,
          'stone': .5, 'wall_slate_dry': .55, 'wall_pebble': .5, 'wall_rubble': .55, 'stone_block': .5, 'ashlar_grey': .45, 'ashlar_moss': .45,
          'planks': .1, 'planks_old': .1, 'boards_weathered': .1, 'wattle': .12}


# ------------------------------------------------------------------ build
class Builder:
    def __init__(self, spec, st, collection):
        self.s = spec; self.st = st; self.col = collection; self.rng = random.Random(spec['seed'])
        self.p = {k: M.Part(k) for k in ('Platform', 'Columns', 'Beams', 'Walls', 'Openings', 'Brackets', 'Roof', 'Roof_timber', 'Railings', 'Props')}
        tm = st['column']['mat']
        organic = spec['tile'] in ('thatch', 'bark', 'bamboo')
        # a hard (硬山) gable continues the same masonry/earth wall; timber-framed walls keep the style's gable material
        gable_wall = spec['wall'] if WALL_T.get(spec['wall'], .16) >= .36 else (st['gable_wall'] if st['gable_wall'] != st['wall'] else spec['wall'])
        self.mat = {'col': tm, 'beam': st['beam_mat'], 'board': st['board_mat'], 'wall': spec['wall'], 'wall_low': spec['wall_low'],
                    'gable_wall': gable_wall, 'base': st['platform_mat'], 'tile': spec['tile_mat'],
                    'ridge': spec['tile_mat'] if organic else st['ridge_mat'], 'window': st['window_mat'], 'trim': spec['trim']}
        if spec['tile'] == 'slate':
            self.mat['ridge'] = 'stone'
        self.om = {'frame': st['window_mat'], 'door': 'wood_dark' if st['window_mat'] in ('wood_dark',) else 'wood', 'paper': st['paper'],
                   'metal': 'iron', 'stone': 'stone', 'sign': 'lacquer_black', 'lantern': 'cloth_red'}
        f = spec['fen']; cls = spec['cls']
        self.col_r = max(.1 if cls == 'yuwu' else .14, R.COLUMN_FEN.get(cls, 26) * f / 2)
        self.wall_t = WALL_T.get(spec['wall'], .16)

    # -------------------------------------------------------------- helpers
    def xs(self):
        out = [-self.s['W'] / 2]
        for w in self.s['widths']:
            out.append(out[-1] + w)
        return out

    def ys(self):
        D = self.s['D']; n = max(1, self.s['jia'] // 2)
        return [-D / 2 + D * i / n for i in range(n + 1)]

    def perimeter(self):
        xs = self.xs(); ys = self.ys(); pts = []
        for x in xs:
            pts.append((x, ys[0], 'front')); pts.append((x, ys[-1], 'back'))
        for y in ys[1:-1]:
            pts.append((xs[0], y, 'side')); pts.append((xs[-1], y, 'side'))
        return pts

    # -------------------------------------------------------------- platform
    def platform(self, z):
        """台基 via gen/foundation.py; returns the floor height (platform top)."""
        s = self.s; W, D = s['W'], s['D']
        if s['polygon'] or s['found'] == 'none' or z <= .01:
            return z if not s['polygon'] else z
        mx = max(.5, min(1.6, .45 * self.eave_total()))         # 阶头 【推定 by eave reach】
        front = s['jia_len'] if s['porch'] else 0.0
        if s['fujie']:
            mx += s['jia_len'] * 1.2
        yt = s['yuetai']
        if yt == 'auto':
            yt = (min(W * .7, W + 2 * mx), min(max(3.0, D * .45), 9.0), min(.35, z * .3))
        mats = {'body': s['found_body'], 'cap': s['found_cap'], 'soil': 'stone', 'waist': 'stone_carved_dark' if s['found'] in ('diezhe', 'xumi') else s['found_body'],
                'step': s['found_cap'], 'rail': 'stone_carved', 'apron': 'paving', 'retain': 'wall_rubble' if s['found'] != 'earth' else 'earth_rammed', 'joint': 'stone'}
        F = FD.Foundation(self.p, mats, s['lod'], self.rng); self.F = F
        return F.platform(W, D, z, s['found'], mx, tiers=s['found_tiers'], front_extra=front, yuetai=yt, steps=s['steps'],
                          side_steps=s['side_steps'], balustrade=s['balustrade'], slope=s['slope'], sanshui=not s['stilts'],
                          chishou=s['chishou'])

    def eave_total(self):
        return sum(self.eave_parts())

    def eave_parts(self):
        rd = max(.08, R.RAFTER_FEN.get(self.s['cls'], 6.5) * self.s['fen'])
        e, f = R.eave_out(rd)
        small = min(1.0, max(.6, min(self.s['W'], self.s['D']) / 6))     # small pavilions/shrines: shorter eaves 【推定】
        e *= self.st['eave_factor'] * small; f = f * self.st['eave_factor'] * small if self.st['fly'] else 0.0
        if self.s['cls'] == 'yuwu':
            e *= .75; f *= .75
        return e, f

    # -------------------------------------------------------------- frame
    def columns(self, z0, h, top_floor, shengqi):
        s = self.s; W = s['W']; Pc = self.p['Columns']; ent = self.st['entasis'] if s['cls'] != 'yuwu' else 0
        lean = self.st['cejiao']; square = self.st['column']['shape'] == 'square'
        for x, y, side in self.perimeter():
            hh = h + (shengqi * (abs(x) / (W / 2)) ** 2 if top_floor else 0)
            dx = -math.copysign(R.CEJIAO_FRONT * hh, x) if lean and side != 'side' and abs(x) > .01 else 0
            dy = -math.copysign(R.CEJIAO_SIDE * hh, y) if lean and (side == 'side' or abs(abs(x) - W / 2) < .01) else 0
            M.column(Pc, x, y, z0, z0 + hh, self.col_r, self.mat['col'], 12 if s['lod'] < 2 else 8, .08, ent, (dx, dy), square)
            if s['lod'] < 2 and (self.st['platform'] != 'none' or not s['stilts']):
                FD.column_base(self.p['Platform'], x, y, z0, self.col_r, s['column_base'], 'stone_carved' if s['found_cap'] != 'earth_rammed' else 'stone', s['lod'])   # 柱础

    def lintels(self, z, top_floor):
        s = self.s; xs = self.xs(); ys = self.ys(); Pb = self.p['Beams']; f = s['fen']
        bh = max(.18, 30 * f); bw = max(.12, 20 * f); m = self.mat['beam']
        rows = [(xs[0], ys[0], xs[-1], ys[0]), (xs[0], ys[-1], xs[-1], ys[-1]), (xs[0], ys[0], xs[0], ys[-1]), (xs[-1], ys[0], xs[-1], ys[-1])]
        for x0, y0, x1, y1 in rows:
            M.beam(Pb, (x0, y0, z - bh / 2), (x1, y1, z - bh / 2), bw, bh, m)
            if s['brackets'] and s['bracket_kind'] == 'song' and top_floor:    # 普拍方
                M.beam(Pb, (x0, y0, z + .04), (x1, y1, z + .04), bw * 1.5, .08, m)
        return bh

    # -------------------------------------------------------------- walls
    def wall_run(self, a, b, z0, z1, cfg, outward, floor_idx):
        """Wall between two columns a->b (in plan) with openings according to cfg."""
        s = self.s; Pw = self.p['Walls']; Po = self.p['Openings']
        L = math.dist(a, b); ang = math.atan2(b[1] - a[1], b[0] - a[0]); c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        t = self.wall_t; h = z1 - z0; low = min(self.st['wall_low_h'], h * .4) if floor_idx == 0 else 0
        inner = L - 2 * self.col_r * .6
        def seg(u0, u1, w0, w1, mat=None):           # wall block in local (u along, w height)
            if u1 - u0 < .02 or w1 - w0 < .02:
                return
            st = Pw.mark(); M.box(Pw, ((u0 + u1) / 2, 0, (w0 + w1) / 2), (u1 - u0, t, w1 - w0), mat or self.mat['wall'])
            Pw.transform(st, M.place(c[0], c[1], z0, ang))
        def low_band(u0, u1):
            if low > 0 and self.mat['wall_low'] != self.mat['wall']:
                st = Pw.mark(); M.box(Pw, ((u0 + u1) / 2, 0, low / 2), (u1 - u0, t + .04, low), self.mat['wall_low'])
                Pw.transform(st, M.place(c[0], c[1], z0, ang))
        half = inner / 2
        if cfg in ('none', 'open'):
            return
        opening = None
        if cfg == 'door':
            ow = min(inner * .72, 2.0 if s['cls'] == 'yuwu' else 2.6); oh = min(h * .78, 2.4 if s['cls'] == 'yuwu' else 3.2)
            opening = ('door', ow, 0.0, oh)
        elif cfg == 'geyan':
            opening = ('geyan', inner * .96, 0.0, min(h * .82, 3.4))
        elif cfg == 'window':
            kind = self.st['window']; ow = min(inner * .62, 1.8); oh = min(h * .38, 1.3)
            if kind == 'small':
                ow, oh = min(.7, inner * .3), .6
            zb = max(low, h * .38) if kind != 'small' else h * .62
            opening = (kind, ow, zb, oh)
        elif cfg == 'shop':
            opening = ('shop', inner * .96, 0.0, min(h * .86, 3.0))
        elif cfg == 'gate':
            opening = ('gate', min(inner * .7, 2.8), 0.0, min(h * .8, 3.2))
        if opening is None:
            seg(-half, half, 0, h); low_band(-half, half)
            return
        kind, ow, zb, oh = opening
        seg(-half, -ow / 2, 0, h); seg(ow / 2, half, 0, h); seg(-ow / 2, ow / 2, zb + oh, h)
        if zb > 0:
            seg(-ow / 2, ow / 2, 0, zb, self.mat['wall_low'] if low else None)
        low_band(-half, -ow / 2); low_band(ow / 2, half)
        st = Po.mark(); om = dict(self.om)
        if kind in ('door', 'gate'):
            P.door_banmen(Po, ow, oh, om, s['lod'], studs=kind == 'gate' or s['official'])
        elif kind == 'geyan':
            P.door_geyan(Po, ow, oh, om, s['lod'], leaves=4 if ow > 2.4 else 2)
        elif kind == 'shop':
            P.shop_front(Po, ow, oh, om, self.rng, s['lod'])
        else:
            P.window(Po, ow, oh, om, kind, s['lod'])
            Po.transform(st, M.Matrix.Translation((0, 0, zb)))
        Po.transform(st, M.place(c[0], c[1], z0, ang))   # run direction already puts local -Y outside

    def walls(self, z0, h, floor_idx):
        s = self.s; xs = self.xs(); ys = self.ys(); nb = len(xs) - 1; mid = (nb - 1) / 2
        def front_cfg(i):
            f = s['front']
            if floor_idx > 0:
                return 'window' if f not in ('none',) else 'none'
            if f == 'doors_center':
                return 'door' if abs(i - mid) < .6 else 'window'
            if f == 'door_each':                        # 营屋 rows: one door per 间
                return 'door'
            if f == 'all_doors':
                hd = self.st['hall_door']; return 'geyan' if hd == 'geyan' else ('door' if abs(i - mid) < .6 else 'window')
            if f == 'shop':
                return 'shop'
            if f == 'gate':
                return 'gate' if abs(i - mid) < .6 else 'wall'
            return f
        for i in range(nb):
            self.wall_run((xs[i], ys[0]), (xs[i + 1], ys[0]), z0, z0 + h, front_cfg(i), -1, floor_idx)
            bcfg = {'wall': 'wall', 'windows': 'window', 'all_doors': 'geyan', 'open': 'none', 'none': 'none'}[s['back']]
            if floor_idx > 0 and bcfg == 'none' and s['front'] != 'none':
                bcfg = 'window'
            self.wall_run((xs[i + 1], ys[-1]), (xs[i], ys[-1]), z0, z0 + h, bcfg, 1, floor_idx)
        scfg = {'wall': 'wall', 'windows': 'window', 'none': 'none', 'open': 'none'}[s['sides']]
        for j in range(len(ys) - 1):
            cfg = scfg if not (scfg == 'window' and j % 2) else 'wall'
            self.wall_run((xs[0], ys[j + 1]), (xs[0], ys[j]), z0, z0 + h, cfg, 1, floor_idx)
            self.wall_run((xs[-1], ys[j]), (xs[-1], ys[j + 1]), z0, z0 + h, cfg, 1, floor_idx)

    # -------------------------------------------------------------- roof
    def section(self, b0, n_jia):
        s = self.s; pm = self.st['pitch']; m = pm['method']; D = 2 * b0
        clsmap = {'dian': 'dian', 'ting': 'ting', 'ting_small': 'ting', 'lang': 'lang', 'yuwu': 'lang'}
        cls = clsmap[s['cls']]
        if pm.get('cls_shift') == -1 and cls == 'dian':
            cls = 'ting'
        tile = 'tube' if s['tile'] == 'tube' else 'flat'
        if m == 'song':
            pts = R.song_juzhe(D, n_jia, cls, tile)
        elif m == 'qing':
            pts = R.qing_jujia(D, n_jia)
        elif m == 'flat':
            pts = R.flat_section(D, n_jia)
        else:
            pts = R.folk_pitch(D, n_jia, pm.get('folk_ratio', .5))     # 瓦屋四分: rise = depth / 4 at ratio .5 【原文 考工记】
        k = pm.get('flatten', 1.0) * pm.get('steepen', 1.0)
        if s['tile'] == 'thatch' and m != 'flat':       # 葺屋参分: rise = depth / 3 (屋深九尺则檐低于脊三尺) 【原文 考工记】
            pts = R.folk_pitch(D, n_jia, R.THATCH_RATIO); k = 1.0
        if s.get('pitch_ratio'):
            pts = R.folk_pitch(D, n_jia, s['pitch_ratio']); k = 1.0
        pts = [(a, z * k) for a, z in pts]
        if s['roof'] in ('cuanjian', 'yuan'):
            pts = R.song_juzhe(D, max(2, n_jia), 'dian')
            pts[0] = (0, pts[0][1] * 1.25)                # 簇角梁 steepens the top 【原文 卷五 斗尖 两分举一，推定比例】
        return pts

    def roof(self, z_top, bracket_proj, part_override=None, form=None, a_half=None, b_half=None, flat_t=0.0):
        s = self.s; form = form or s['roof']
        e, f = self.eave_parts()
        a0 = (a_half if a_half is not None else s['W'] / 2) + bracket_proj
        b0 = (b_half if b_half is not None else s['D'] / 2) + bracket_proj
        n_jia = max(1, s['jia'] // 2)
        swap = form in ('wudian', 'xieshan', 'luding') and b0 > a0
        if swap:
            a0, b0 = b0, a0
        pts = self.section(b0, n_jia)
        if form == 'pingding':
            pts = R.flat_section(2 * b0, 1); form = 'yingshan'
        jp = .5 * s['jia_len'] if form.startswith('juanpeng') else 0
        sec = R.Section(pts, b0, e, f, kick=.06 if self.st['fly'] else .0, juanpeng=jp)
        B = sec.b
        lift = self.st['corner_lift'] * B if form not in ('yingshan', 'juanpeng_ying') else 0.0
        if form in ('xuanshan', 'juanpeng') and self.st['corner_lift'] < .1:
            lift = 0.0
        if s['tile'] == 'thatch':
            lift = 0.0
        shq = R.shengqi(s['bays']) if self.st['shengqi'] else 0.0
        k_xs = 2 if s['cls'] in ('dian', 'ting') and s['jia'] >= 6 else 1
        gable_at = a0 - k_xs * s['jia_len'] if form == 'xieshan' else None
        ridge_h = {'dian': .9, 'ting': .55, 'ting_small': .45, 'lang': .35, 'yuwu': .32}[s['cls']]
        beasts = {'dian': 4, 'ting': 2}.get(s['cls'], 0)
        mats = {'tile': self.mat['tile'], 'ridge': self.mat['ridge'], 'timber': self.mat['beam'], 'soffit': self.mat['board'] if self.mat['board'] != 'lacquer_black' else 'wood_dark',
                'board': self.mat['board'], 'ornament': self.mat['ridge'], 'trim': self.mat['trim']}
        model = RoofModel(form, a0, b0, z_top, sec, e + f, corner_lift=lift, corner_out=self.st['corner_out'] * B * (lift > 0),
                          shengqi=shq, chuji=R.chuji(s['jia']) if form in ('xuanshan', 'juanpeng', 'xieshan', 'danpo') else 0.0,
                          gable_at=gable_at, flat_t=flat_t, sides=s['sides_n'], tile='flat' if s['roof'] == 'pingding' else s['tile'],
                          lod=s['lod'], ridge=s['ridge'], ridge_h=ridge_h, hip_beasts=beasts, materials=mats,
                          gable='shanhua' if s['gable'] == 'shanhua' else 'open', wall_t=self.wall_t)
        rp, tp, wp = M.Part('r'), M.Part('t'), M.Part('w')
        model.build(rp, tp, wp)
        mtx = M.Matrix.Rotation(math.pi / 2, 4, 'Z') if swap else M.Matrix.Identity(4)
        self.p['Roof'].extend(rp, mtx); self.p['Roof_timber'].extend(tp, mtx); self.p['Walls'].extend(wp, mtx)
        model.swap = swap
        return model

    def under(self, model, x, y):
        if getattr(model, 'swap', False):
            return model.underside(y, -x)
        return model.underside(x, y)

    # -------------------------------------------------------------- gables
    def gables(self, model, z_wall_top):
        s = self.s; g = s['gable']; W, D = s['W'], s['D']; form = s['roof']; Pw = self.p['Walls']; Pt = self.p['Roof_timber']
        if form in ('wudian', 'cuanjian', 'yuan', 'luding', 'danpo', 'xieshan'):
            if form == 'danpo':
                for sx in (-1, 1):            # side walls up to the slope
                    self._gable_fill(model, sx * W / 2, z_wall_top, .16, self.mat['wall'], open_frame=False)
            return
        if form in ('xuanshan', 'juanpeng'):
            for sx in (-1, 1):
                x = sx * W / 2
                if g == 'chuandou':
                    self._chuandou(model, x, z_wall_top)
                else:
                    self._gable_fill(model, x, z_wall_top, .14, self.mat['gable_wall'] if self.st['gable_wall'] else self.mat['wall'], open_frame=True)
            return
        # 硬山: masonry gable walls to the roof underside, regional parapets
        t = self.wall_t if self.wall_t > .3 else .36
        for sx in (-1, 1):
            x = sx * (W / 2 + t * .2)
            self._gable_fill(model, x, 0.0, t, self.mat['gable_wall'], open_frame=False, solid_to_ground=True)
            self._parapet(model, x, sx, t)
            if self.st['label'].startswith(('中原', '岚溪')) or g == 'brick':          # 墀头 at the front/back corners
                for sy in (-1, 1):
                    y = sy * (D / 2 + .1); zt = self.under(model, x, y)
                    M.box_minmax(Pw, (x - t / 2, y - .25 * (sy < 0) - .05, zt - .9), (x + t / 2, y + .25 * (sy > 0) + .05, zt - .1), 'brick_grey')

    def _gable_fill(self, model, x, z0, t, mat, open_frame, solid_to_ground=False):
        s = self.s; D = s['D']; Pw = self.p['Walls']; n = 16; ext = .1
        ys = [-D / 2 - ext + (D + 2 * ext) * i / n for i in range(n + 1)]
        for a, b in zip(ys, ys[1:]):
            za = self.under(model, x, a) - .05; zb = self.under(model, x, b) - .05; lo = 0.0 if solid_to_ground else z0
            if min(za, zb) <= lo:
                continue
            vs = [(x + dx, y, z) for dx in (-t / 2, t / 2) for y, z in ((a, lo), (b, lo), (b, zb), (a, za))]
            Pw.add(vs, M.BOX_FACES, mat)
        if open_frame and s['lod'] < 2:        # Song 山面梁架: 平梁 + 蜀柱 + 叉手 shown on the gable 【原文 卷五 侏儒柱/叉手】
            Pt = self.p['Roof_timber']; m = self.mat['beam']; zt = self.under(model, x, 0) - .1
            zl = z0 + (zt - z0) * .45
            M.beam(Pt, (x + .1 * (1 if x > 0 else -1), -D / 3, zl), (x + .1 * (1 if x > 0 else -1), D / 3, zl), .2, .28, m)
            xo = x + .12 * (1 if x > 0 else -1)
            M.beam(Pt, (xo, 0, zl), (xo, 0, zt), .16, .16, m)
            for sy in (-1, 1):            # 叉手: a straight strut under a concave (举折) roof; keep its midpoint and top under the roof
                y0 = sy * D / 3; top = zt - .1
                for _ in range(12):
                    mid_ok = (zl + .1 + top) / 2 < self.under(model, x, y0 / 2) - .15
                    if mid_ok:
                        break
                    top -= .12
                if top > zl + .45 and top < self.under(model, x, 0) - .1:   # too shallow a gable: no 叉手
                    M.beam(Pt, (xo, y0, zl + .1), (xo, 0, top), .14, .18, m)

    def _chuandou(self, model, x, z0):
        """穿斗: a column at every purlin up to the roof, 穿枋 ties, white infill (川西)."""
        s = self.s; D = s['D']; n = s['jia']; Pt = self.p['Roof_timber']; m = self.mat['beam']
        self._gable_fill(model, x, z0, .1, 'plaster_white', open_frame=False)
        xo = x + .08 * (1 if x > 0 else -1)
        for i in range(n + 1):
            y = -D / 2 + D * i / n; zt = self.under(model, x, y) - .08
            M.beam(Pt, (xo, y, z0 - .1), (xo, y, zt), .14, .14, m)
        for k in range(1, 4):
            zz = z0 + k * .6
            pts = [(-D / 2 + D * i / n) for i in range(n + 1) if self.under(model, x, -D / 2 + D * i / n) > zz + .2]
            if len(pts) >= 2:
                M.beam(Pt, (xo, pts[0], zz), (xo, pts[-1], zz), .1, .16, m)

    def _parapet(self, model, x, sx, t):
        s = self.s; g = s['gable']; D = s['D']; Pw = self.p['Walls']; Pr = self.p['Roof']; half = D / 2 + .25
        top = self.under(model, x, 0) + .25
        if g == 'horse':          # 马头墙: stepped fire walls with tile copings
            for side in (-1, 1):
                for j, frac in enumerate((1.0, .66, .33)):
                    y0 = side * half * j / 3; y1 = side * half * (j + 1) / 3; lo, hi = min(y0, y1), max(y0, y1)
                    zt = model.z0 + (top - model.z0) * frac + .5
                    M.box_minmax(Pw, (x - t / 2, lo, model.z0 - .2), (x + t / 2, hi, zt), self.mat['gable_wall'])
                    M.box_minmax(Pr, (x - t / 2 - .12, lo - .05, zt), (x + t / 2 + .12, hi + .05, zt + .12), 'tile_dark')
                    M.tube(Pr, [(x, lo if side > 0 else hi, zt + .16), (x, hi if side > 0 else lo, zt + .16)], .08, 'tile_dark', 6)
        elif g == 'wok':          # 镬耳: rounded ears above the roof
            pts = []
            for i in range(33):
                y = -half + 2 * half * i / 32; u = abs(y) / half
                z = max(self.under(model, x, y) + .25, model.z0 + (top - model.z0) * (1.05 - .7 * u * u) + .6 * math.exp(-((u - .55) / .2) ** 2))
                pts.append((y, z))
            for (a, za), (b, zb) in zip(pts, pts[1:]):
                vs = [(x + dx, y, z) for dx in (-t / 2, t / 2) for y, z in ((a, model.z0 - .2), (b, model.z0 - .2), (b, zb), (a, za))]
                Pw.add(vs, M.BOX_FACES, self.mat['gable_wall'])
            M.tube(Pr, [(x, y, z + .03) for y, z in pts], .08, 'stone_light', 6)
        elif g in ('brick', 'yingshan', 'swallow', 'shanhua'):   # coping along the gable (排山)
            pts = [(x, -half + 2 * half * i / 24, self.under(model, x, -half + 2 * half * i / 24) + .2) for i in range(25)]
            M.tube(Pr, pts, .1, self.mat['ridge'], 6)

    # -------------------------------------------------------------- extras
    def balcony_ring(self, z, depth, front_only=True):
        s = self.s; W, D = s['W'], s['D']; Pp = self.p['Railings']; m = self.mat['beam']
        y0 = -D / 2 - depth
        M.box_minmax(self.p['Beams'], (-W / 2 - (0 if front_only else depth), y0, z - .14), (W / 2 + (0 if front_only else depth), -D / 2 if front_only else D / 2 + depth, z), 'wood_dark')
        pts = [(-W / 2, -D / 2, z), (-W / 2, y0, z), (W / 2, y0, z), (W / 2, -D / 2, z)] if front_only else \
              [(-W / 2 - depth, y0, z), (W / 2 + depth, y0, z), (W / 2 + depth, D / 2 + depth, z), (-W / 2 - depth, D / 2 + depth, z), (-W / 2 - depth, y0, z)]
        P.railing(Pp, pts, .95, m, lod=s['lod'])
        if front_only:
            for x in (-W / 2, W / 2):           # 挑枋 struts under the gallery
                M.beam(self.p['Beams'], (x, -D / 2, z - .9), (x, y0 + .1, z - .1), .1, .12, m)

    def skirt(self, z_wall, run, rise, a_half, b_half):
        """副阶/缠腰/腰檐 ring roof meeting the wall at z_wall: 二分举一 slope 【原文 卷五】."""
        s = self.s; e, f = self.eave_parts(); e *= .7; f *= .7
        b0 = b_half + run; a0 = a_half + run
        s_w = b_half / b0; H = rise / max(1e-3, 1 - s_w)
        sec = R.Section([(0, H), (1, 0)], b0, e, f, kick=.05 if self.st['fly'] else 0)
        t_in = (b0 * s_w) / sec.b
        mats = {'tile': self.mat['tile'], 'ridge': self.mat['ridge'], 'timber': self.mat['beam'], 'soffit': 'wood', 'board': self.mat['board'], 'trim': self.mat['trim']}
        model = RoofModel('skirt', a0, b0, z_wall - rise, sec, e + f, corner_lift=self.st['corner_lift'] * sec.b * .7,
                          corner_out=0.0, flat_t=t_in, tile=s['tile'] if s['tile'] != 'thatch' else 'combo', lod=s['lod'], materials=mats, ridge='plain')
        model.build(self.p['Roof'], self.p['Roof_timber'], M.Part('w'))   # ring works for deep plans too: inner x = a_half

    # -------------------------------------------------------------- main
    def build(self):
        s = self.s; st = self.st
        root = bpy.data.objects.new(f"{s['label']}_{s['style']}_{s['seed']}", None); self.col.objects.link(root)
        if s['polygon'] or (s['roof'] in ('cuanjian',) and s['sides_n'] != 4) or s['roof'] == 'yuan':
            self.build_polygon(root)
        else:
            self.build_rect()
        return self.finish(root)

    def build_rect(self):
        s = self.s; st = self.st; W, D = s['W'], s['D']
        zb = s['platform_h'] + s['stilts']
        if s['base_tower']:
            self.tower_base()
            zb = s['platform_h']
        else:
            self.platform(s['platform_h'])
        if s['stilts']:
            self.stilts(s['stilts'])
        e_total = self.eave_total()
        fh = s['col_h']; z = zb
        fuj_run = s['jia_len'] * 1.2 if s['fujie'] else 0
        if s['fujie']:
            fh = s['col_h'] * 1.0 + 1.6
        if s['porch']:
            self.porch(zb, s['col_h'])
        shq = R.shengqi(s['bays']) if st['shengqi'] else 0.0
        for fl in range(s['floors']):
            h = fh if fl == 0 else s['col_h'] * .88
            top = fl == s['floors'] - 1
            self.columns(z, h, top, shq)
            if fl > 0:
                M.box_minmax(self.p['Beams'], (-W / 2 - .1, -D / 2 - .1, z - .2), (W / 2 + .1, D / 2 + .1, z), 'wood_dark')
            self.walls(z, h - .02, fl)
            bh = self.lintels(z + h, top)
            if not top:
                if s['pingzuo'] or s['balcony']:
                    self.balcony_ring(z + h + .25, 1.0 if s['pingzuo'] else .9, front_only=not s['pingzuo'])
                if s['yaoyan']:
                    self.skirt(z + h - .1, .9, .45, W / 2, D / 2)
            z += h + (.25 if not top else 0)
        top_z = z
        bproj = 0.0; bh = 0.0
        if s['brackets'] and s['bracket_kind'] in ('song', 'simple'):
            bh, bproj = self.bracket_row(top_z)
        if s['fujie']:
            self.fujie(zb, s['col_h'], fuj_run)
        model = self.roof(top_z + bh + .05, bproj)
        self.gables(model, top_z)
        self.extras(zb, model)

    def bracket_row(self, z):
        s = self.s; xs = self.xs(); ys = self.ys(); Pb = self.p['Brackets']; f = s['fen']; kind = s['bracket_kind']; lv = s['brackets']; m = self.mat['beam']
        h = P.bracket_height(lv, f, kind); proj = 0.0
        for x in xs:
            for y, ang in ((ys[0], 0.0), (ys[-1], math.pi)):
                corner = x in (xs[0], xs[-1])
                h, proj = P.bracket(Pb, x, y, z, ang, lv, f, m, kind, corner, s['lod'])
        for y in ys[1:-1]:
            for x, ang in ((xs[0], -math.pi / 2), (xs[-1], math.pi / 2)):
                P.bracket(Pb, x, y, z, ang, lv, f, m, kind, False, s['lod'])
        nb = s['bujian'] if s['lod'] < 2 else 0
        if nb and kind == 'song':                 # 补间铺作
            for i in range(len(xs) - 1):
                k = min(nb, max(1, int((xs[i + 1] - xs[i]) / 1.6)))
                for j in range(k):
                    x = xs[i] + (xs[i + 1] - xs[i]) * (j + 1) / (k + 1)
                    for y, ang in ((ys[0], 0.0), (ys[-1], math.pi)):
                        P.bracket(Pb, x, y, z, ang, lv, f, m, kind, False, s['lod'])
        # 橑檐方 on the outer 跳 tips
        if proj:
            for y, sg in ((ys[0], -1), (ys[-1], 1)):
                M.beam(self.p['Beams'], (xs[0] - proj, y + sg * proj, z + h - .05), (xs[-1] + proj, y + sg * proj, z + h - .05), .14, .2, m)
        return h, proj

    def porch(self, zb, h):
        s = self.s; W, D = s['W'], s['D']; y = -D / 2 - s['jia_len']
        for x in self.xs():
            M.column(self.p['Columns'], x, y, zb, zb + h, self.col_r * .9, self.mat['col'], 10, .08, 0, (0, 0), self.st['column']['shape'] == 'square')
        M.beam(self.p['Beams'], (-W / 2, y, zb + h - .12), (W / 2, y, zb + h - .12), .16, .24, self.mat['beam'])
        for x in self.xs():
            M.beam(self.p['Beams'], (x, y, zb + h - .3), (x, -D / 2, zb + h - .3), .12, .2, self.mat['beam'])
        if s['railing']:
            P.railing(self.p['Railings'], [(-W / 2, y, zb), (W / 2, y, zb)], .7, self.mat['beam'], lod=s['lod'])

    def fujie(self, zb, h, run):
        """副阶周匝: an outer ring of columns one 架 outside, carrying a skirt roof against the main walls."""
        s = self.s; W, D = s['W'], s['D']; xs = [-W / 2 - run] + self.xs() + [W / 2 + run]; ys = [-D / 2 - run] + self.ys() + [D / 2 + run]
        ring = [(x, ys[0]) for x in xs] + [(x, ys[-1]) for x in xs] + [(xs[0], y) for y in ys[1:-1]] + [(xs[-1], y) for y in ys[1:-1]]
        for x, y in ring:
            M.column(self.p['Columns'], x, y, zb, zb + h, self.col_r * .85, self.mat['col'], 10, .08, self.st['entasis'], (0, 0), False)
        for (x0, y0), (x1, y1) in (((xs[0], ys[0]), (xs[-1], ys[0])), ((xs[0], ys[-1]), (xs[-1], ys[-1])), ((xs[0], ys[0]), (xs[0], ys[-1])), ((xs[-1], ys[0]), (xs[-1], ys[-1]))):
            M.beam(self.p['Beams'], (x0, y0, zb + h - .15), (x1, y1, zb + h - .15), .18, .3, self.mat['beam'])
        rise = run * .5 + .3
        self.skirt(zb + h + rise + .05, run, rise, W / 2, D / 2)

    def stilts(self, hs):
        s = self.s; W, D = s['W'], s['D']; Pc = self.p['Columns']
        for x in self.xs():
            for y in self.ys():
                M.column(Pc, x, y, 0, hs, self.col_r, self.mat['col'], 8, 0, 0, (0, 0), False)
                M.box(self.p['Platform'], (x, y, .12), (.4, .4, .24), 'stone')
        M.box_minmax(self.p['Beams'], (-W / 2 - .2, -D / 2 - .2, hs - .18), (W / 2 + .2, D / 2 + .2, hs), 'wood_dark')
        steps = int(hs / .2)
        for i in range(steps):
            M.box_minmax(self.p['Platform'], (W / 2 + .3, -D / 2 + i * .25, i * .2), (W / 2 + 1.2, -D / 2 + (i + 1) * .25, (i + 1) * .2), 'wood_dark')

    def tower_base(self):
        """城台 for 钟楼/鼓楼: brick block with an arched passage."""
        s = self.s; W, D = s['W'] + 3, s['D'] + 3; h = s['platform_h']; Pp = self.p['Platform']
        aw = 3.0; ah = min(h * .7, 3.6)
        for sx in (-1, 1):
            M.box_minmax(Pp, (sx * aw / 2 if sx > 0 else -W / 2, -D / 2, 0), (W / 2 if sx > 0 else -aw / 2, D / 2, h), 'brick_grey')
        M.box_minmax(Pp, (-aw / 2, -D / 2, ah), (aw / 2, D / 2, h), 'brick_grey')
        n = 10
        for i in range(n):
            a0 = math.pi * i / n; a1 = math.pi * (i + 1) / n
            x0, z0 = -math.cos(a0) * aw / 2, ah - aw / 2 + math.sin(a0) * aw / 2
            x1, z1 = -math.cos(a1) * aw / 2, ah - aw / 2 + math.sin(a1) * aw / 2
            M.box_minmax(Pp, (min(x0, x1), -D / 2, min(z0, z1)), (max(x0, x1), D / 2, ah), 'brick_grey')
        M.box_minmax(Pp, (-W / 2 - .05, -D / 2 - .05, h - .3), (W / 2 + .05, D / 2 + .05, h), 'stone_light')
        P.railing(self.p['Railings'], [(-W / 2, -D / 2, h), (W / 2, -D / 2, h), (W / 2, D / 2, h), (-W / 2, D / 2, h), (-W / 2, -D / 2, h)], .9, 'brick_grey', post_every=1.0, lod=s['lod'])

    def extras(self, zb, model):
        s = self.s; W, D = s['W'], s['D']; om = self.om; Pr = self.p['Props']
        if s['sign']:
            P.sign_board(Pr, 0, -D / 2 - .25, zb + s['col_h'] * .92, min(W * .45, 2.6), om)
        if s['awning']:
            ang = .25; d = 1.6; z = zb + s['col_h'] * .75
            M.box_minmax(Pr, (-W / 2, -D / 2 - d, z - .02), (W / 2, -D / 2, z + .02), 'cloth_blue')
            for x in (-W / 2 + .2, W / 2 - .2):
                M.beam(Pr, (x, -D / 2 - d, zb), (x, -D / 2 - d, z), .08, .08, 'wood_dark')
        if s['lanterns']:
            for x in (-W / 2 + .5, W / 2 - .5):
                P.lantern(Pr, x, -D / 2 - .5, zb + s['col_h'] * .65, om)
        if s['chimney']:
            M.box(Pr, (W / 2 - .8, D / 2 - .6, zb + s['col_h'] + s['D'] * .3), (.6, .6, s['col_h'] * .6 + s['D'] * .6), 'brick_grey')
        if s['vents']:
            for x in self.xs()[1:-1]:
                M.box(Pr, (x, -D / 2 - .05, zb + s['col_h'] * .8), (.4, .1, .3), 'wood_dark')
        if s['furniture'] == 'tables':
            P.tables(Pr, -W / 2, W / 2, -D / 2, D / 2, zb, self.rng, om)
        elif s['furniture'] == 'crates':
            P.crates(Pr, -W / 2, W / 2, -D / 2 + .5, D / 2 - .5, zb, self.rng, om)
        if s['well']:
            P.well(Pr, 0, 0, zb, om)
        if s['stele']:
            P.stele(Pr, 0, 0, zb, om)
        if s['railing'] and s['front'] == 'none' and not s['porch'] and not s['polygon']:
            xs = self.xs(); ys = self.ys()
            for i in range(len(xs) - 1):
                if abs(i - (len(xs) - 2) / 2) < .6 and s['type'] != 'lang':
                    continue
                for y in (ys[0], ys[-1]):
                    P.railing(self.p['Railings'], [(xs[i], y, zb), (xs[i + 1], y, zb)], .55, self.mat['beam'], lod=s['lod'], seat=True)
        if s['hanging_posts']:                    # 垂花门: short hanging posts at the front eave
            for x in (-W / 2 + .3, W / 2 - .3):
                top = min(zb + s['col_h'], self.under(model, x, -D / 2 - .5) - .15)      # stays under the eave
                M.column(self.p['Columns'], x, -D / 2 - .5, zb + s['col_h'] * .62, top, .1, self.mat['col'], 8, 0, 0, (0, 0), False)
                M.tube(self.p['Columns'], [(x, -D / 2 - .5, zb + s['col_h'] * .62), (x, -D / 2 - .5, zb + s['col_h'] * .55)], .14, 'lacquer_red', 8)

    # -------------------------------------------------------------- polygon pavilions
    def build_polygon(self, root):
        s = self.s; n = s['sides_n'] if s['roof'] != 'yuan' else 8; ap = s['widths'][0] / 2 + .2
        r = ap / math.cos(math.pi / n); zb = s['platform_h']; h = s['col_h']; Pc = self.p['Columns']; Pb = self.p['Beams']
        base = [((r + .7) * math.cos(math.tau * (k + .5) / n), (r + .7) * math.sin(math.tau * (k + .5) / n)) for k in range(n)]
        M.prism(self.p['Platform'], base, 0, zb, self.mat['base'], 'stone_light')
        vs = [(r * math.cos(math.tau * (k + .5) / n), r * math.sin(math.tau * (k + .5) / n)) for k in range(n)]
        for x, y in vs:
            M.column(Pc, x, y, zb, zb + h, self.col_r, self.mat['col'], 10, .08, self.st['entasis'], (0, 0), False)
        for k in range(n):
            a = vs[k]; b = vs[(k + 1) % n]
            M.beam(Pb, (a[0], a[1], zb + h - .12), (b[0], b[1], zb + h - .12), .16, .24, self.mat['beam'])
            if s['railing'] and k != n * 3 // 4 % n:
                P.railing(self.p['Railings'], [(a[0], a[1], zb), (b[0], b[1], zb)], .55, self.mat['beam'], lod=s['lod'], seat=True)
        steps = max(1, int(zb / .16))
        for i in range(steps):
            M.box_minmax(self.p['Platform'], (-1, -ap - .7 - (steps - i) * .3, 0), (1, -ap - .7 - (steps - i - 1) * .3, zb * (i + 1) / steps), 'stone_light')
        if s['well']:
            P.well(self.p['Props'], 0, 0, zb, self.om)
        e, f = self.eave_parts(); pts = self.section(ap, 2)
        sec = R.Section(pts, ap, e, f, kick=.06 if self.st['fly'] else 0)
        mats = {'tile': self.mat['tile'], 'ridge': self.mat['ridge'], 'timber': self.mat['beam'], 'soffit': 'wood', 'board': self.mat['board'], 'ornament': 'bronze'}
        form = 'yuan' if s['roof'] == 'yuan' else 'cuanjian'
        if s['fujie']:
            pass
        model = RoofModel(form, ap, ap, zb + h + .05, sec, e + f, corner_lift=self.st['corner_lift'] * sec.b * .7, sides=n, tile=s['tile'], lod=s['lod'],
                          ridge='plain', ridge_h=.35, materials=mats)
        model.build(self.p['Roof'], self.p['Roof_timber'], self.p['Walls'])

    # -------------------------------------------------------------- finish
    def finish(self, root):
        mats = materials.library(); objs = []
        for p in self.p.values():
            ob = p.finish(root, self.col, mats)
            if ob:
                objs.append(ob)
        s = self.s
        meta = {k: v for k, v in s.items() if isinstance(v, (int, float, str, bool))}
        root['lyz_spec'] = json.dumps(meta, ensure_ascii=False); root['lyz_type'] = s['type']; root['lyz_style'] = s['style']
        root['lyz_tris'] = sum(p.tri_count() for p in self.p.values())
        if getattr(getattr(self, 'F', None), 'site', None):
            root['lyz_site'] = json.dumps(self.F.site)              # slope footprint, for placing on terrain
        return root


def generate(type_key, style_key=None, seed=0, collection=None, **over):
    spec, st = resolve(type_key, style_key, seed, **over)
    col = collection or bpy.context.scene.collection
    return Builder(spec, st, col).build()
