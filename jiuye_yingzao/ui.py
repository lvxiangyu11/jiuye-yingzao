# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Sidebar panel: View3D > Sidebar > 九野营造."""
import random

import bpy

from . import catalog, export

CATS = [('building', '单体', '单体建筑（民居/商业/官式/宗教/园林/公用）'), ('special', '特殊', '塔/门/桥/码头/城防/墙/窑洞/土楼/台基/坛/遗址'),
        ('compound', '组群', '院落与中轴组群'), ('modern', '现代', '现代居民楼（MIT 来源）')]
ROOFS = [('AUTO', '自动', ''), ('wudian', '四阿/庑殿', ''), ('xieshan', '九脊/歇山', ''), ('xuanshan', '不厦两头/悬山', ''),
         ('yingshan', '硬山', ''), ('juanpeng', '卷棚', ''), ('luding', '盝顶', ''), ('cuanjian', '攒尖', ''), ('danpo', '单坡', ''), ('pingding', '平顶', '')]
TILES = [('AUTO', '自动', ''), ('tube', '筒瓦', ''), ('combo', '合瓦', ''), ('flat', '平板', ''), ('thatch', '茅草', ''), ('slate', '石板', ''),
         ('bark', '树皮', ''), ('bamboo', '剖竹瓦', '')]
FOUNDS = [('AUTO', '自动', ''), ('stone', '条石台基', ''), ('diezhe', '叠涩坐（宋殿阶基）', ''), ('xumi', '须弥座', ''), ('brick', '砖砌', ''),
          ('tamped', '夯土包砖', ''), ('earth', '土台', ''), ('rubble', '乱石', ''), ('none', '无', '')]
STEPS = [('AUTO', '自动', ''), ('tadao', '踏道（副子）', ''), ('two', '东西两阶', ''), ('ruyi', '如意踏跺', ''), ('brick', '砖踏道', ''), ('mandao', '慢道', ''), ('none', '无', '')]
RAILS = [('AUTO', '自动', ''), ('none', '无', ''), ('dan', '单钩阑', ''), ('chong', '重台钩阑', '')]
BASES = [('AUTO', '自动', ''), ('su', '素平', ''), ('fupen', '覆盆', ''), ('lian', '仰覆莲华', ''), ('zhi', '櫍', ''), ('gu', '鼓镜', ''), ('tall', '高柱础', '')]
TRI = [('AUTO', '自动', ''), ('YES', '有', ''), ('NO', '无', '')]
HMODES = [('AUTO', '自动', '层高按类型范围随种子取值'), ('UNIFORM', '统一层高', '每层同一高度'), ('PER', '逐层设定', '每一层单独设定高度')]


def _mats(group):
    def items(self, context):
        from .core import materials as Mt
        return [('AUTO', '自动（风格候选随机）', '')] + [(k, v.get('label', k), k) for k, v in Mt.specs().items() if v.get('group') == group]
    return items


def _types(self, context):
    return [(k, f'{label}', group) for k, label, cat, group, _ in catalog.entries() if cat == self.category] or [('NONE', '-', '')]


def _styles(self, context):
    items = [('auto', '自动（按类型推荐）', '')]
    for k, label in catalog.styles().items():
        items.append((k, label, ''))
    return items


def _special_ranges(kind):
    from .gen.specials import SPECIALS
    return SPECIALS[kind][3] if kind in SPECIALS else {}


def _levels_kind(p):
    """What the storey controls drive for the current selection: 'floors' | 'modern' | 'levels' | None."""
    if p.category == 'building':
        return 'floors'
    if p.category == 'modern':
        return 'modern'
    if p.category == 'special' and 'levels' in _special_ranges(p.kind):
        return 'levels'
    return None


def _default_h(p, i):
    if p.category == 'modern':
        return 4.35 if i == 0 else 2.95
    if p.category == 'special':
        if p.kind == 'pagoda_dense':
            return 1.0                                       # metres between eaves
        r = _special_ranges(p.kind).get('storey_h')
        return sum(r) / 2 if r else 2.9
    return 3.4 if i == 0 else 3.0


def _target_rows(p):
    n = p.floors or (len(p.floor_list) - (1 if p.category == 'modern' and len(p.floor_list) else 0)) or (6 if p.category == 'modern' else 2)
    return n + 1 if p.category == 'modern' else n


def _sync(self, context):
    """Resize the per-storey list to the storey count, keeping the values already typed in."""
    if self.height_mode != 'PER' or _levels_kind(self) is None:
        return
    n = _target_rows(self); L = self.floor_list
    while len(L) > n:
        L.remove(len(L) - 1)
    while len(L) < n:
        i = len(L); it = L.add()
        it.height = L[i - 1].height if i > 1 or (i == 1 and self.category != 'modern') else _default_h(self, i)


def _reset(self, context):
    """Category / type changed: storey defaults differ, start the per-storey list afresh."""
    self.floor_list.clear(); _sync(self, context)


class LYZ_FloorH(bpy.types.PropertyGroup):
    height: bpy.props.FloatProperty(name='层高 (m)', default=3.0, min=0.01, soft_min=.5, soft_max=12.0, unit='LENGTH',
                                    description='这一层的高度（本层地面到上层地面，不含层间梁）')


class LYZ_Props(bpy.types.PropertyGroup):
    category: bpy.props.EnumProperty(name='类别', items=CATS, update=_reset)
    kind: bpy.props.EnumProperty(name='类型', items=_types, update=_reset)
    style: bpy.props.EnumProperty(name='风格', items=_styles)
    seed: bpy.props.IntProperty(name='种子', default=1, min=0)
    lod: bpy.props.IntProperty(name='细节等级', default=1, min=0, max=2, description='0 近景（瓦当/椽头/门钉/蹲兽）, 1 常规, 2 远景')
    bays: bpy.props.IntProperty(name='开间（0=自动）', default=0, min=0, max=11)
    floors: bpy.props.IntProperty(name='层数（0=自动）', default=0, min=0, soft_max=30, update=_sync, description='不设上限；0 = 按类型范围随种子取值')
    height_mode: bpy.props.EnumProperty(name='层高', items=HMODES, update=_sync)
    floor_h: bpy.props.FloatProperty(name='统一层高 (m)', default=3.0, min=0.01, soft_min=.5, soft_max=12.0, unit='LENGTH')
    floor_list: bpy.props.CollectionProperty(type=LYZ_FloorH)
    platform_h: bpy.props.FloatProperty(name='台基高 (m，-1=自动)', default=-1.0, min=-1.0, soft_max=5.0, description='-1 = 按类型随种子取值；0 = 无台基')
    pitch_ratio: bpy.props.FloatProperty(name='屋面坡度（0=自动）', default=0.0, min=0.0, soft_max=2.0, description='举高 ÷ 半进深；0.5 ≈ 瓦屋四分，0.667 ≈ 葺屋参分')
    sp_height: bpy.props.FloatProperty(name='总高 (m，0=自动)', default=0.0, min=0.0, soft_max=40.0, unit='LENGTH', description='牌坊、牌楼、门、墙、城墙、华表、望火楼等的高度')
    roof: bpy.props.EnumProperty(name='屋顶', items=ROOFS)
    tile: bpy.props.EnumProperty(name='瓦作', items=TILES)
    wall_mat: bpy.props.EnumProperty(name='墙体材质', items=_mats('wall'))
    roof_mat: bpy.props.EnumProperty(name='屋面材质', items=_mats('roof'))
    found: bpy.props.EnumProperty(name='台基', items=FOUNDS)
    found_tiers: bpy.props.IntProperty(name='台基层数（0=自动）', default=0, min=0, max=3)
    yuetai: bpy.props.EnumProperty(name='月台', items=TRI)
    steps: bpy.props.EnumProperty(name='踏道', items=STEPS)
    balustrade: bpy.props.EnumProperty(name='钩阑', items=RAILS)
    column_base: bpy.props.EnumProperty(name='柱础', items=BASES)
    slope: bpy.props.FloatProperty(name='坡地落差 (m)', default=0.0, min=0.0, max=6.0, description='前低后高的地形落差；台基下加挡土台')
    export_dir: bpy.props.StringProperty(name='导出目录', subtype='DIR_PATH', default='//jiuye_export/')


def _heights(p):
    """Storey overrides for the current selection (nothing is clamped)."""
    o = {}; lk = _levels_kind(p)
    if lk is None:
        return o
    key_n, key_h, key_hs = ('levels', 'storey_h', 'storey_hs') if lk == 'levels' else ('floors', 'floor_h', 'floor_hs')
    if p.floors:
        o[key_n] = p.floors
    if p.height_mode == 'UNIFORM':
        o[key_h] = round(p.floor_h, 4)
    elif p.height_mode == 'PER' and len(p.floor_list):
        o[key_hs] = [round(it.height, 4) for it in p.floor_list]
        if not p.floors:
            o[key_n] = len(p.floor_list) - (1 if lk == 'modern' else 0)
    return o


def _over(p):
    o = _heights(p)
    if p.category == 'special' and p.sp_height > 0 and 'height' in _special_ranges(p.kind):
        o['height'] = p.sp_height
    if p.category == 'building':
        if p.bays:
            o['bays'] = p.bays
        if p.platform_h >= 0:
            o['platform_h'] = p.platform_h
        if p.pitch_ratio > 0:
            o['pitch_ratio'] = p.pitch_ratio
        if p.roof != 'AUTO':
            o['roof'] = p.roof
        if p.tile != 'AUTO':
            o['tile'] = p.tile
        if p.wall_mat != 'AUTO':
            o['wall'] = p.wall_mat
        if p.roof_mat != 'AUTO':
            o['tile_mat'] = p.roof_mat
        for k in ('found', 'steps', 'balustrade', 'column_base'):
            if getattr(p, k) != 'AUTO':
                o[k] = getattr(p, k)
        if p.found_tiers:
            o['found_tiers'] = p.found_tiers
        if p.yuetai != 'AUTO':
            o['yuetai'] = 'auto' if p.yuetai == 'YES' else None
        if p.slope > 0:
            o['slope'] = p.slope
    return o


class LYZ_OT_generate(bpy.types.Operator):
    bl_idname = 'lyz.generate'; bl_label = '生成'; bl_options = {'REGISTER', 'UNDO'}
    reseed: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        p = context.scene.lyz
        if self.reseed:
            p.seed = random.randint(1, 99999)
        kind = p.kind if p.category != 'modern' else 'modern_residential'
        root = catalog.generate(kind, None if p.style == 'auto' else p.style, p.seed, p.lod, context.collection, **_over(p))
        root.location = context.scene.cursor.location
        for o in context.view_layer.objects:
            o.select_set(False)
        root.select_set(True); context.view_layer.objects.active = root
        self.report({'INFO'}, f"{root.name}: {root.get('lyz_tris', 0)} 三角面")
        return {'FINISHED'}


class LYZ_OT_sync_floors(bpy.types.Operator):
    bl_idname = 'lyz.sync_floors'; bl_label = '按层数重排逐层列表'; bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        _sync(context.scene.lyz, context)
        return {'FINISHED'}


class LYZ_OT_fill_floors(bpy.types.Operator):
    bl_idname = 'lyz.fill_floors'; bl_label = '全部设为统一层高'; bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        p = context.scene.lyz
        for i, it in enumerate(p.floor_list):
            if not (p.category == 'modern' and i == 0):
                it.height = p.floor_h
        return {'FINISHED'}


class LYZ_OT_export(bpy.types.Operator):
    bl_idname = 'lyz.export'; bl_label = '导出选中（GLB）'

    def execute(self, context):
        root = context.view_layer.objects.active
        while root and root.parent:
            root = root.parent
        if not root:
            self.report({'ERROR'}, '请选中一个生成的建筑'); return {'CANCELLED'}
        path = bpy.path.abspath(context.scene.lyz.export_dir) + root.name + '.glb'
        export.export_root(root, path)
        self.report({'INFO'}, path)
        return {'FINISHED'}


class LYZ_PT_panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = '九野营造'; bl_label = '九野营造 · 建筑生成'

    def draw(self, context):
        p = context.scene.lyz; c = self.layout.column(align=True)
        c.prop(p, 'category'); c.prop(p, 'kind'); c.prop(p, 'style'); c.prop(p, 'seed'); c.prop(p, 'lod')
        self.draw_heights(p)
        if p.category == 'building':
            b = self.layout.box(); b.label(text='覆盖参数')
            b.prop(p, 'bays'); b.prop(p, 'roof'); b.prop(p, 'tile'); b.prop(p, 'wall_mat'); b.prop(p, 'roof_mat')
            f = self.layout.box(); f.label(text='台基 / 地基')
            for k in ('found', 'found_tiers', 'yuetai', 'steps', 'balustrade', 'column_base', 'slope'):
                f.prop(p, k)
        r = self.layout.row(align=True)
        r.operator('lyz.generate', text='生成').reseed = False
        r.operator('lyz.generate', text='随机种子生成').reseed = True
        self.layout.prop(p, 'export_dir'); self.layout.operator('lyz.export')

    def draw_heights(self, p):
        lk = _levels_kind(p); has_h = p.category == 'special' and 'height' in _special_ranges(p.kind)
        if lk is None and not has_h:
            return
        b = self.layout.box(); b.label(text='高度 / 层数')
        if has_h:
            b.prop(p, 'sp_height')
        if lk:
            dense = p.kind == 'pagoda_dense' and lk == 'levels'
            b.prop(p, 'floors', text={'levels': '层数/檐数（0=自动）', 'modern': '住宅层数（0=自动，不含底层商铺）'}.get(lk, '层数（0=自动）'))
            b.row().prop(p, 'height_mode', expand=True)
            if p.height_mode == 'UNIFORM':
                b.prop(p, 'floor_h', text='统一檐间距 (m)' if dense else ('住宅统一层高 (m)' if lk == 'modern' else '统一层高 (m)'))
            elif p.height_mode == 'PER':
                r = b.row(align=True)
                r.operator('lyz.sync_floors', text='按层数重排'); r.prop(p, 'floor_h', text=''); r.operator('lyz.fill_floors', text='全部填入')
                col = b.column(align=True); total = 0.0
                for i, it in enumerate(p.floor_list):
                    if lk == 'modern':
                        lab = '底层商铺' if i == 0 else f'住宅第 {i} 层'
                    else:
                        lab = f'第 {i + 1} 檐间距' if dense else f'第 {i + 1} 层'
                    col.prop(it, 'height', text=lab); total += it.height
                if len(p.floor_list):
                    b.label(text=f'{len(p.floor_list)} 行，合计 {total:.2f} m')
                else:
                    b.label(text='点"按层数重排"生成逐层列表', icon='INFO')
        if p.category == 'building':
            b.prop(p, 'platform_h'); b.prop(p, 'pitch_ratio')


CLASSES = (LYZ_FloorH, LYZ_Props, LYZ_OT_generate, LYZ_OT_sync_floors, LYZ_OT_fill_floors, LYZ_OT_export, LYZ_PT_panel)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.Scene.lyz = bpy.props.PointerProperty(type=LYZ_Props)


def unregister():
    del bpy.types.Scene.lyz
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
