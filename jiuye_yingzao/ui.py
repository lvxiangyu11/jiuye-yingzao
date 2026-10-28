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


class LYZ_Props(bpy.types.PropertyGroup):
    category: bpy.props.EnumProperty(name='类别', items=CATS)
    kind: bpy.props.EnumProperty(name='类型', items=_types)
    style: bpy.props.EnumProperty(name='风格', items=_styles)
    seed: bpy.props.IntProperty(name='种子', default=1, min=0)
    lod: bpy.props.IntProperty(name='细节等级', default=1, min=0, max=2, description='0 近景（瓦当/椽头/门钉/蹲兽）, 1 常规, 2 远景')
    bays: bpy.props.IntProperty(name='开间（0=自动）', default=0, min=0, max=11)
    floors: bpy.props.IntProperty(name='层数（0=自动）', default=0, min=0, max=9)
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
    export_dir: bpy.props.StringProperty(name='导出目录', subtype='DIR_PATH', default='//lanxi_export/')


def _over(p):
    o = {}
    if p.category == 'building':
        if p.bays:
            o['bays'] = p.bays
        if p.floors:
            o['floors'] = p.floors
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
    if p.category == 'modern' and p.floors:
        o['floors'] = p.floors
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
        if p.category in ('building', 'modern'):
            b = self.layout.box(); b.label(text='覆盖参数')
            if p.category == 'building':
                b.prop(p, 'bays'); b.prop(p, 'roof'); b.prop(p, 'tile'); b.prop(p, 'wall_mat'); b.prop(p, 'roof_mat')
                f = self.layout.box(); f.label(text='台基 / 地基')
                for k in ('found', 'found_tiers', 'yuetai', 'steps', 'balustrade', 'column_base', 'slope'):
                    f.prop(p, k)
            b.prop(p, 'floors')
        r = self.layout.row(align=True)
        r.operator('lyz.generate', text='生成').reseed = False
        r.operator('lyz.generate', text='随机种子生成').reseed = True
        self.layout.prop(p, 'export_dir'); self.layout.operator('lyz.export')


CLASSES = (LYZ_Props, LYZ_OT_generate, LYZ_OT_export, LYZ_PT_panel)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.Scene.lyz = bpy.props.PointerProperty(type=LYZ_Props)


def unregister():
    del bpy.types.Scene.lyz
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
