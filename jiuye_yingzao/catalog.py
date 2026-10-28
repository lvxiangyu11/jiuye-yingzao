# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Unified registry: every generatable kind (单体 / 特殊 / 组群 / 现代) behind one generate() call."""
from .gen import building as B, compound as C, specials as S


def entries():
    """[(key, label, category, group, preferred_styles)]"""
    out = []
    for k, t in B.TYPES.items():
        out.append((k, t['label'], 'building', t.get('group', ''), t['styles']))
    for k, (fn, label, group, ranges, styles) in S.SPECIALS.items():
        out.append((k, label, 'special', group, styles))
    for k, (fn, label, styles) in C.COMPOUNDS.items():
        out.append((k, label, 'compound', '组群', styles))
    out.append(('modern_residential', '现代居民楼', 'modern', '现代', ['modern']))
    return out


def category(key):
    if key in B.TYPES:
        return 'building'
    if key in S.SPECIALS:
        return 'special'
    if key in C.COMPOUNDS:
        return 'compound'
    if key == 'modern_residential':
        return 'modern'
    raise KeyError(key)


def generate(key, style=None, seed=0, lod=1, collection=None, **over):
    cat = category(key)
    if cat == 'building':
        return B.generate(key, style, seed, collection, lod=lod, **over)
    if cat == 'special':
        return S.generate(key, style, seed, collection, lod=lod, **over)
    if cat == 'compound':
        return C.generate(key, style, seed, collection, lod=lod)
    from .gen import modern
    return modern.generate(seed=seed, collection=collection, **over)


def styles():
    return {k: v['label'] for k, v in B.STYLES.items()}
