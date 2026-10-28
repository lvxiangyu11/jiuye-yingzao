# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Construction rules.

Primary source: 《营造法式》(北宋 李诫, 1103), text from zh.wikisource (public domain,
https://zh.wikisource.org/wiki/營造法式). Quoted rules are marked 【原文】; values chosen for the game
where the text gives none are marked 【推定】. Qing 举架 is kept only as a weak option (styles.json).
"""
import math

CHI_SONG = 0.312      # 宋营造尺 (m) 【推定，学界常用 30.9–31.6 cm】
CHI_MING = 0.32       # 明清营造尺 (m) 【推定】

# 【原文 卷四·材】材有八等：广、厚 (寸)；以广的 1/15 为一分（"各以其材之广分为十五分，以十分为其厚"）
CAI_GRADES = {
    1: (9.0, 6.0, '殿身九间至十一间'), 2: (8.25, 5.5, '殿身五间至七间'), 3: (7.5, 5.0, '殿身三间至殿五间或堂七间'),
    4: (7.2, 4.8, '殿三间、厅堂五间'), 5: (6.6, 4.4, '殿小三间、厅堂大三间'), 6: (6.0, 4.0, '亭榭或小厅堂'),
    7: (5.25, 3.5, '小殿及亭榭'), 8: (4.5, 3.0, '殿内藻井或小亭榭施铺作多'),
}


def fen(grade, chi=CHI_SONG):
    """One 分 in metres for a 材 grade."""
    return CAI_GRADES[grade][0] / 10 * chi / 15


def grade_for(cls, bays):
    """【原文 卷四】choose the 材 grade from building class and bay count; 余屋/民居 use 6–8 【推定】."""
    if cls == 'dian':
        return 1 if bays >= 9 else 2 if bays >= 5 else 4 if bays >= 3 else 5
    if cls == 'ting':
        return 3 if bays >= 7 else 4 if bays >= 5 else 5 if bays >= 3 else 6
    if cls == 'ting_small':
        return 6
    return 7 if bays >= 3 else 8


# 【原文 卷五·柱】柱径：殿阁两材两栔至三材 (42–45 分)，厅堂两材一栔 (36 分)，余屋一材一栔至两材 (21–30 分)
COLUMN_FEN = {'dian': 43.5, 'ting': 36.0, 'ting_small': 32.0, 'yuwu': 26.0}

# 【原文 卷五·柱】至角生起：三间二寸、五间四寸、七间六寸、九间八寸、十一间一尺、十三间一尺二寸
def shengqi(bays, chi=CHI_SONG):
    table = {1: 0, 3: 2, 5: 4, 7: 6, 9: 8, 11: 10, 13: 12}
    b = max(k for k in table if k <= max(1, bays))
    return table[b] / 100 * chi * 10   # 寸 -> m


# 【原文 卷五·柱】侧脚：正面每柱长一尺侧脚一分 (1%)，侧面八厘 (0.8%)
CEJIAO_FRONT = 0.01
CEJIAO_SIDE = 0.008

# 【原文 卷五·阳马/出际】两际出际：两椽二尺至二尺五寸，四椽三尺至三尺五寸，六椽三尺五寸至四尺，八至十椽四尺五寸至五尺
def chuji(rafters, chi=CHI_SONG):
    t = {2: 2.25, 4: 3.25, 6: 3.75, 8: 4.75, 10: 4.75}
    k = min(t, key=lambda n: abs(n - rafters))
    return t[k] * chi


# 【原文 卷五·檐】造檐之制，皆从橑檐方心出：椽径三寸檐出三尺五寸，椽径五寸檐出四尺至四尺五寸；
# 檐外别加飞檐，每檐一尺出飞子六寸。
def eave_out(rafter_d_m, chi=CHI_SONG):
    cun = rafter_d_m / chi * 10
    out_chi = 3.5 + (min(max(cun, 3), 5) - 3) / 2 * (4.25 - 3.5)
    eave = out_chi * chi
    return eave, eave * 0.6


# 【原文 卷五·椽】椽径：殿阁九至十分，厅堂七至八分，余屋六至七分；每架平不过六尺
RAFTER_FEN = {'dian': 9.5, 'ting': 7.5, 'ting_small': 7.0, 'yuwu': 6.5}
MAX_JIA = 6 * CHI_SONG


# ------------------------------------------------------------------ 举折 / 举架 / 民间做法
def song_juzhe(depth, n_jia, cls='ting', tile='tube'):
    """【原文 卷五·举折】Song roof section.

    depth: 前后橑檐方心 (or 檐柱心 when no brackets) distance; n_jia: rafter spans per side.
    举屋之法: 殿阁楼台 三分举一；㼧瓦(筒瓦)厅堂 四分举一，每尺加八分；㼧瓦廊屋及瓪瓦(板瓦)厅堂 加五分；
    瓪瓦廊屋 加三分；两椽屋不加；副阶/缠腰 二分举一。
    折屋之法: 举高每尺折一寸 (H/10)，每架自上递减半；逐缝取平，皆下至橑檐方背。
    Returns [(s, z)] from ridge (s=0) to eave purlin (s=1), z above the eave purlin.
    """
    if cls == 'dian':
        H = depth / 3
    elif cls == 'fujie':
        H = depth / 2      # 副阶/缠腰 depth here is the skirt's own run *2 (二分中举一分)
    else:
        add = {('ting', 'tube'): .08, ('ting', 'flat'): .05, ('lang', 'tube'): .05, ('lang', 'flat'): .03}.get((cls if cls in ('ting', 'lang') else 'ting', tile), .05)
        H = depth / 4 * (1 + (0 if n_jia <= 1 else add))
    n = max(1, n_jia)
    s = [k / n for k in range(n + 1)]          # purlin positions from ridge
    z = [H] + [None] * n; z[n] = 0.0
    drop = H / 10
    for k in range(1, n):
        line = z[k - 1] * (1 - (s[k] - s[k - 1]) / (1 - s[k - 1]))   # from previous purlin straight down to the eave purlin
        z[k] = line - drop
        drop /= 2
    return list(zip(s, z))


def qing_jujia(depth, n_jia, steps=(0.5, 0.65, 0.75, 0.9, 1.0)):
    """Qing 举架 (de-emphasised): from the eave purlin up, each step rises step_span * coefficient."""
    span = depth / 2 / max(1, n_jia); pts = [(1.0, 0.0)]; z = 0.0
    for k in range(n_jia):
        z += span * steps[min(k, len(steps) - 1)]; pts.append((1 - (k + 1) / n_jia, z))
    return sorted(pts)


# 《考工记·匠人》: 葺屋参分, 瓦屋四分 (考工记解: 屋深九尺则檐低于脊三尺, 瓦屋则多一分以为峻)
# as rise / half-depth: thatch 2/3, tile 1/2
THATCH_RATIO = 2 / 3
TILE_RATIO = 1 / 2


def folk_pitch(depth, n_jia, ratio=0.5, sag=0.06):
    """Vernacular: rise = ratio x half-depth (0.5 ~ 26.6 deg) with a slight 囊 (sag) 【推定】."""
    H = depth / 2 * ratio
    n = max(2, n_jia * 2)
    return [(k / n, H * (1 - k / n) - sag * H * math.sin(math.pi * k / n)) for k in range(n + 1)]


def flat_section(depth, n_jia, ratio=0.02):
    return [(0.0, depth * ratio), (1.0, 0.0)]


def smooth_profile(points):
    """Monotone cubic (Fritsch–Carlson) through purlin points -> f(s) for s in [0,1], z decreasing with s."""
    xs = [p[0] for p in points]; ys = [p[1] for p in points]; n = len(xs)
    if n == 2:
        return lambda s: ys[0] + (ys[1] - ys[0]) * s, lambda s: ys[1] - ys[0]
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else (d[i - 1] + d[i]) / 2 for i in range(1, n - 1)] + [d[-1]]
    for i in range(n - 1):
        if d[i] == 0:
            m[i] = m[i + 1] = 0
            continue
        a = m[i] / d[i]; b = m[i + 1] / d[i]; h = a * a + b * b
        if h > 9:
            t = 3 / math.sqrt(h); m[i] = t * a * d[i]; m[i + 1] = t * b * d[i]

    def seg(s):
        s = min(max(s, 0.0), 1.0)
        i = min(n - 2, max(0, next((k for k in range(n - 1) if s <= xs[k + 1]), n - 2)))
        h = xs[i + 1] - xs[i]; t = (s - xs[i]) / h
        h00 = 2 * t ** 3 - 3 * t ** 2 + 1; h10 = t ** 3 - 2 * t ** 2 + t; h01 = -2 * t ** 3 + 3 * t ** 2; h11 = t ** 3 - t ** 2
        return i, h, t, h00 * ys[i] + h10 * h * m[i] + h01 * ys[i + 1] + h11 * h * m[i + 1]

    def f(s):
        return seg(s)[3]

    def df(s):
        e = 1e-4; return (f(min(1, s + e)) - f(max(0, s - e))) / (min(1, s + e) - max(0, s - e))
    return f, df


class Section:
    """Roof cross-section over t in [0, 1]: t=0 ridge, t=t_eave eave purlin, t=1 outer eave edge.

    z(t) is height above the eave purlin. Beyond the eave purlin the rafter continues at the last
    slope and the 飞子 portion (fly) flattens it and turns the tip up by `kick`.
    """

    def __init__(self, points, half_depth, eave, fly, kick=0.06, juanpeng=0.0):
        self.f, self.df = smooth_profile(points)
        self.b0 = half_depth; self.eave = eave; self.fly = fly; self.b = half_depth + eave + fly
        self.te = half_depth / self.b; self.kick = kick; self.H = self.f(0); self.juanpeng = juanpeng

    def z(self, t):
        t = max(0.0, t)
        if self.juanpeng and t * self.b < self.juanpeng:          # 卷棚: parabolic cap over the 顶步, slope-continuous
            r = self.juanpeng; x = t * self.b
            slope = -self.df(r / self.b0) / self.b0
            return self.f(r / self.b0) + slope * (r * r - x * x) / (2 * r)
        if t <= self.te:
            return self.f(t / self.te)
        x = (t - self.te) * self.b                                  # metres beyond the eave purlin
        slope = -self.df(1.0) / self.b0                              # dz/dx at the eave purlin (positive down)
        if x <= self.eave:
            return -slope * x
        y = x - self.eave; z_e = -slope * self.eave
        return z_e - slope * 0.55 * y + self.kick * (y / max(self.fly, 1e-6)) ** 2
