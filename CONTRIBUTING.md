# 参与贡献 / Contributing

欢迎提交 PR：新建筑类型、地方风格、规则修正（附原文出处）、材质、性能优化、Unity 导出、文档与翻译都可以。

Pull requests are welcome: new building types, regional styles, rule corrections (with the source passage), materials, performance work, Unity export, documentation and translations.

## 流程 / Workflow
1. 先读 `LICENSING.md` 和 `CLA.md`。第一个 PR 的描述里写明同意 CLA v1.0（写法见 `CLA.md` 第 7 条）。
2. Fork 后在新分支上修改，一个 PR 只做一件事。
3. 运行检查（Blender 4.2 以上，命令行无界面）：
   ```
   blender -b --factory-startup --python tools/test_addon.py
   blender -b --factory-startup --python tools/build_catalog.py -- --variants 2 [--only key1,key2]
   py -3.12 tools/gen_manual_tables.py
   ```
   `tools/build_catalog.py` 应输出 `CATALOG_DONE n of n`。新类型请附一张缩略图或 `tools/test_variants.py` 生成的对照图。
4. PR 描述写清：做了什么、依据是什么（古籍卷次、原文、【原文】/【推定】标注）、面数变化。

## 规则与标注 / Rules and labels
- 尺寸规则优先回到原典，例如《营造法式》《考工记》《长物志》，并在代码注释和手册中标注出处：
  - 【原文】：原文直接给出的数值。
  - 【推定】：为游戏地图选定的值。
- 不提交没有许可证、或许可证与 GPL-3.0 不兼容的代码和资产。第三方材料要在 `jiuye_yingzao/THIRD_PARTY_NOTICES.md` 中登记来源、版本和许可证。
- 贴图只用 CC0 或与 GPL 兼容的来源。改了 `data/materials.json` 后，运行 `tools/bake_textures.py` 重新烘焙。

## 代码风格 / Code style
- 风格跟随周围代码：紧凑，几何函数按"部件 → Part"组织，尺寸用米，宋尺用 `rules.CHI_SONG`。
- 新增的 `.py` 文件开头加：
  ```
  # SPDX-License-Identifier: GPL-3.0-or-later
  # Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
  ```
- 随机数一律用传入的 `rng` 或 `zlib.crc32` 派生，不依赖 Python 的 `hash()`，以保证同一种子结果可复现。

## 署名与分成 / Credit and revenue share
合并后，你会被记入 `CONTRIBUTORS.md`，并按 `CLA.md` 第 6 条记点。如果项目有商业授权收入，按点数比例分配。
