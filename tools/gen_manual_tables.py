# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Write 技术手册_附表.md from the data tables and catalog/report.json. Run: py -3.12 tools/gen_manual_tables.py"""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; A = ROOT / 'jiuye_yingzao'
T = {k: v for k, v in json.loads((A / 'data/types.json').read_text(encoding='utf-8')).items() if not k.startswith('_')}
S = {k: v for k, v in json.loads((A / 'data/styles.json').read_text(encoding='utf-8')).items() if not k.startswith('_')}
spec_src = (A / 'gen/specials.py').read_text(encoding='utf-8')
SP = re.findall(r"^    '(\w+)':\s+\(([\w.]+),\s+'([^']+)',\s+'([^']+)',\s+(\{.*?\}),\s+(\[.*?\])\),", spec_src, re.M)
CP = re.findall(r"^    '(\w+)':\s+\(.*?'([^']+)',\s*(\[.*?\])\),", (A / 'gen/compound.py').read_text(encoding='utf-8'), re.M)
ROOF = {'wudian': '四阿/庑殿', 'xieshan': '九脊/歇山', 'xuanshan': '不厦两头/悬山', 'yingshan': '硬山', 'juanpeng': '卷棚', 'juanpeng_ying': '卷棚硬山',
        'luding': '盝顶', 'cuanjian': '攒尖', 'yuan': '圆攒尖', 'danpo': '单坡', 'pingding': '平顶'}
FRONT = {'doors_center': '明间门、余间窗', 'door_each': '每间一门', 'all_doors': '通间格子门', 'windows': '通间窗', 'wall': '实墙', 'shop': '铺面排门', 'open': '敞开', 'gate': '门屋大门', 'none': '无墙'}
FLAGS = ['porch', 'fujie', 'pingzuo', 'yaoyan', 'balcony', 'awning', 'sign', 'lanterns', 'railing', 'chimney']
FLAG_ZH = {'porch': '前廊', 'fujie': '副阶', 'pingzuo': '平坐', 'yaoyan': '腰檐', 'balcony': '挑台', 'awning': '布棚', 'sign': '招牌', 'lanterns': '灯笼', 'railing': '栏杆', 'chimney': '烟囱',
           'vents': '气窗', 'well': '井', 'stele': '碑', 'base_tower': '城台', 'hanging_posts': '垂莲柱', 'stilts': '吊脚', 'furniture': '家具', 'note': ''}
TILES = 5; USABLE = [k for k, v in S.items() if not v.get('deemphasized')]


def rng_count(r, even=False):
    a, b = int(r[0]), int(r[1])
    return len([x for x in range(a, b + 1) if not even or x % 2 == 0]) or 1


def building_rows():
    rows = []; total_pref = total_open = 0
    for k, t in T.items():
        nb = rng_count(t['bays']); nj = rng_count(t['jia'], True); nf = rng_count(t['floors']); nr = len(t['roof'])
        flags = [f for f in FLAGS if 0 < t.get(f, 0) < 1]; extras = [FLAG_ZH[f] for f in FLAGS + ['vents', 'well', 'stele', 'base_tower', 'hanging_posts', 'stilts', 'furniture'] if t.get(f)]
        disc = nb * nj * nf * nr * 2 ** len(flags)
        pref = disc * len(t['styles']); opn = nb * nj * nf * 11 * TILES * 2 ** len(flags) * len(USABLE)
        total_pref += pref; total_open += opn
        rows.append(f"| `{k}` | {t['label']} | {t.get('group', '')} | {t['cls']} | {t['bays'][0]}–{t['bays'][1]} | {t['jia'][0]}–{t['jia'][1]} | {t['floors'][0]}–{t['floors'][1]} | "
                    f"{'、'.join(ROOF[r] for r in t['roof'])} | {FRONT.get(t['front'], t['front'])} | {'、'.join(e for e in extras if e) or '—'} | {'、'.join(t['styles'])} | {pref:,} |")
    return rows, total_pref, total_open


def main():
    rows, tp, to = building_rows()
    out = ['# 九野营造 · 技术手册附表（自动生成）', '', '由 `tools/gen_manual_tables.py` 从 `data/types.json`、`data/styles.json`、`gen/specials.py`、`gen/compound.py`、`catalog/report.json` 生成，勿手改。', '']
    out += ['## 附表 A · 单体建筑类型（%d 种）' % len(T), '',
            '"离散组合" = 间数 × 进深椽数（偶数） × 层数 × 屋顶选项 × 2^(随机附件数) × 推荐风格数；开间宽、步架长、柱高、台基高为连续量，另由种子取值，不计入。', '',
            '| 键 | 名称 | 组 | 等级 | 间数 | 椽数 | 层数 | 屋顶 | 前檐 | 附件 | 推荐风格 | 离散组合 |', '|---|---|---|---|---|---|---|---|---|---|---|---:|'] + rows
    out += ['', f'单体合计：推荐风格范围内离散组合 {tp:,} 种；放开全部 {len(USABLE)} 个可用风格、11 种屋顶、5 种瓦作覆盖后为 {to:,} 种（含不合形制的组合，例如茅草庑殿）。', '']
    out += ['## 附表 B · 特殊结构（%d 种）' % len(SP), '', '| 键 | 名称 | 组 | 参数范围 | 推荐风格 |', '|---|---|---|---|---|']
    for k, fn, label, group, ranges, styles in SP:
        out.append(f'| `{k}` | {label} | {group} | `{ranges}` | {", ".join(re.findall(chr(39) + r"(\w+)" + chr(39), styles))} |')
    out += ['', '## 附表 C · 组群（%d 种）' % len(CP), '', '| 键 | 名称 | 推荐风格 |', '|---|---|---|']
    for k, label, styles in CP:
        out.append(f'| `{k}` | {label} | {", ".join(re.findall(chr(39) + r"(\w+)" + chr(39), styles))} |')
    out += ['', '另有 `modern_residential` 现代居民楼 1 种（层数 3–9、种子；来源 kang340/xingfuli-residential，MIT）。', '']
    out += ['## 附表 D · 风格（%d 种，其中弱化 %d 种）' % (len(S), len(S) - len(USABLE)), '',
            '| 键 | 名称 | 举屋方法 | 出檐系数 | 起翘/B | 生出/B | 生起 | 侧脚 | 梭柱 | 铺作高/柱高 | 补间 | 柱色 | 墙 | 瓦（官/民） | 脊饰（官/民） | 山面 | 窗 | 门 |',
            '|---|---|---|---:|---:|---:|---|---|---:|---:|---:|---|---|---|---|---|---|---|']
    for k, s in S.items():
        out.append(f"| `{k}` | {s['label']} | {s['pitch']['method']} | {s['eave_factor']} | {s['corner_lift']} | {s['corner_out']} | {'是' if s['shengqi'] else '否'} | {'是' if s['cejiao'] else '否'} | {s['entasis']} | "
                   f"{s['bracket']['scale']} | {s['bracket'].get('bujian', 0)} | {s['column']['mat']} | {s['wall']} | {s['tile']['official']}/{s['tile']['house']} | {s['ridge']['official']}/{s['ridge']['house']} | {s['gable']} | {s['window']} | {s['door']} |")
    MT = {k: v for k, v in json.loads((A / 'data/materials.json').read_text(encoding='utf-8')).items() if not k.startswith('_')}
    GZ = {'wall': '墙体/石作', 'roof': '屋面', 'other': '木作/装修/杂项'}
    out += ['', f'## 附表 F · 材质（{len(MT)} 种）', '', '贴图均为 ambientCG CC0；`keep` = 保留原图色彩变化，`tint` = 只保留明暗细节、重新着色；"做旧" = 苔藓/污渍叠加。', '']
    for g in ('wall', 'roof', 'other'):
        ks = [k for k, v in MT.items() if v.get('group', 'other') == g]
        out += [f'### {GZ[g]}（{len(ks)} 种）', '', '| 键 | 名称 | 底图 | 方式 | 做旧 |', '|---|---|---|---|---|']
        out += [f"| `{k}` | {MT[k].get('label', k)} | {MT[k].get('base') or '—'} | {MT[k].get('mode', 'tint') if MT[k].get('base') else '纯色'} | {'是' if MT[k].get('overlay') else ''} |" for k in ks]
        out.append('')
    rep = ROOT / 'catalog/report.json'
    if rep.exists():
        R = json.loads(rep.read_text(encoding='utf-8')); ok = [r for r in R if r['ok']]
        out += ['', f'## 附表 E · 目录生成结果（{len(ok)}/{len(R)} 成功，LOD1）', '', '缩略图由 `tools/build_catalog.py` 生成到 `catalog/thumbs/`（不入库）。', '', '| 键 | 名称 | 风格 | 种子 | 三角面 | 包围盒 (m) | 生成 (s) |', '|---|---|---|---:|---:|---|---:|']
        for r in R:
            if r['ok']:
                out.append(f"| `{r['key']}` | {r['label']} | {r['style']} | {r['seed']} | {r['tris']:,} | {' × '.join(str(v) for v in r['size_m'])} | {r['gen_s']} |")
            else:
                out.append(f"| `{r['key']}` | {r['label']} | {r['style']} | {r['seed']} | 失败 | {r.get('error', '')[:60]} | |")
        tris = sorted(r['tris'] for r in ok)
        out += ['', f"三角面：最小 {tris[0]:,}，中位 {tris[len(tris) // 2]:,}，最大 {tris[-1]:,}。"]
    (ROOT / '技术手册_附表.md').write_text('\n'.join(out) + '\n', encoding='utf-8')
    print('written', len(T), len(SP), len(CP), tp, to)


if __name__ == '__main__':
    main()
