# Third-party notices — 九野营造 Jiuye Yingzao (jiuye_yingzao)

The add-on itself is GPL-3.0-or-later (see `LICENSE` at the repository root). The components below keep their own licenses.

## xingfuli-residential (modern residential block)
- Source: https://github.com/kang340/xingfuli-residential, revision 52825a5 (2026-10-18)
- License: MIT, Copyright (c) 2026 kang340. Full text: `vendor/xingfuli/LICENSE`.
- Use: `vendor/xingfuli/*.py` kept unmodified. `gen/modern.py` loads them with patched constants (NFLOORS, random seeds)
  and a Blender 4.x/5.x socket-name shim ('Fac'/'Factor'), then joins the result per collection.

## threejs-architecture-effects (via lanxi_map_editor)
- Source: https://github.com/lhlGitHub/threejs-architecture-effects, revision 693ca2e
- License: MIT, Copyright (c) 2026 Hailey. Full text: `vendor/LICENSE_threejs-architecture-effects`.
- Use: the idea of one shared boundary height function so hip slopes meet exactly, as adapted earlier in
  lanxi_map_editor/generators/heritage_roofs.py. gen/roof.py is a new implementation (举折 sections, ring/gable/polygon
  patches, tile relief); no source lines are copied. The notice is kept because the design derives from that adaptation.

## ambientCG surface maps
- License: CC0 1.0 (https://docs.ambientcg.com/license/).
- Sets: Wood026, Plaster003, Bricks058, Bricks006, Rock030, Fabric036, Ground054, Ground037, PavingStones131, Gravel021
  (copied from lanxi_map_editor, hashes in `data/material_sources_upstream.json`); ThatchedRoof001A, Bamboo001A, Clay005,
  Planks023A, Concrete034, PaintedPlaster017 (downloaded 2026-10-27, 1K-JPG; hashes in `data/material_sources.json`).
- Derived maps in `textures/derived` are tinted/rescaled by tools/bake_textures.py.

## Texts
- 《营造法式》《长物志》《考工记》: public domain, text from zh.wikisource; used as rule sources, not bundled in the add-on.
