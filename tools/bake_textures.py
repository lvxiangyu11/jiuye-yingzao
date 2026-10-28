# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Bake per-material albedo and roughness maps from the CC0 base sets.

Tint and roughness range are baked into textures (not shader nodes) so glTF/FBX exports
to Unity look the same as in Blender. Run: py -3.12 tools/bake_textures.py

Material keys (data/materials.json):
  mode     "tint" (default): keep the texture's luminance detail, replace hue with `color`
           "keep": keep the texture's own colour variation, shift its mean to `color` (stone, pebbles, clay tiles)
  overlay  {"base": set, "amount": 0..1, "color": [r,g,b], "scale": px}: weathering (moss, stains) mixed in
           through a large-scale noise mask
"""
import json, hashlib, zlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

ADDON = Path(__file__).resolve().parents[1] / 'jiuye_yingzao'
PBR = ADDON / 'textures/pbr'; OUT = ADDON / 'textures/derived'
LUM = np.array([.2126, .7152, .0722], np.float32)

def srgb_to_lin(c): return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
def lin_to_srgb(c): return np.where(c <= .0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - .055)

def albedo(name):
    return srgb_to_lin(np.asarray(Image.open(PBR / f'{name}_Color.jpg').convert('RGB'), np.float32) / 255)

def recolour(lin, color, mode):
    target = srgb_to_lin(np.array(color, np.float32))
    if mode == 'keep':
        mean = lin.reshape(-1, 3).mean(0)
        return lin * (target / np.maximum(mean, 1e-4))
    lum = lin @ LUM; detail = 1 + (lum / max(lum.mean(), 1e-4) - 1) * .85
    return detail[..., None] * target

def tileable_mask(shape, scale, seed):
    """Large-scale wrap-around noise in [0,1] (blurred random field, tiled 3x3 so the blur wraps)."""
    rng = np.random.default_rng(seed); h, w = shape
    base = Image.fromarray((rng.random((h // 8, w // 8)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    big = Image.new('L', (w * 3, h * 3))
    for i in range(3):
        for j in range(3):
            big.paste(base, (i * w, j * h))
    big = big.filter(ImageFilter.GaussianBlur(scale)).crop((w, h, 2 * w, 2 * h))
    m = np.asarray(big, np.float32) / 255
    return (m - m.min()) / max(m.max() - m.min(), 1e-4)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    spec = json.loads((ADDON / 'data/materials.json').read_text(encoding='utf-8'))
    report = {}
    for key, m in spec.items():
        if key.startswith('_') or not m.get('base'): continue
        out = recolour(albedo(m['base']), m['color'], m.get('mode', 'tint'))
        ov = m.get('overlay')
        if ov:
            o = albedo(ov['base'])
            if o.shape != out.shape:
                o = srgb_to_lin(np.asarray(Image.open(PBR / f"{ov['base']}_Color.jpg").convert('RGB').resize(out.shape[1::-1]), np.float32) / 255)
            o = recolour(o, ov.get('color', [.25, .3, .18]), 'tint')
            mask = tileable_mask(out.shape[:2], ov.get('scale', 40), zlib.crc32(key.encode()) % 1000)
            t = 1 - ov['amount']; mask = np.clip((mask - t) / max(1 - t, 1e-3) * 1.6, 0, 1)[..., None]
            out = out * (1 - mask) + o * mask
        out = lin_to_srgb(np.clip(out, 0, 1))
        Image.fromarray((out * 255 + .5).astype(np.uint8)).save(OUT / f'{key}_Color.jpg', quality=92)
        r = np.asarray(Image.open(PBR / f"{m['base']}_Roughness.jpg").convert('L'), np.float32) / 255
        lo, hi = m['roughness']; r = lo + (r - r.min()) / max(r.max() - r.min(), 1e-4) * (hi - lo)
        Image.fromarray((r * 255 + .5).astype(np.uint8)).save(OUT / f'{key}_Roughness.jpg', quality=92)
        report[key] = hashlib.sha256(json.dumps(m, sort_keys=True).encode()).hexdigest()[:12]
    (OUT / 'bake_report.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    print(len(report), 'materials baked')

if __name__ == '__main__':
    main()
