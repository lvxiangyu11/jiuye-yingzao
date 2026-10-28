# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
bl_info = {
    "name": "九野营造 Jiuye Yingzao",
    "author": "Xiangyu Lyu and contributors",
    "version": (0, 4, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > 九野营造",
    "description": "Parametric Chinese buildings after the Yingzao Fashi: halls, houses, pagodas, gates, bridges, foundations, street works",
    "doc_url": "https://github.com/lvxiangyu11/jiuye-yingzao",
    "category": "Add Mesh",
}


def register():
    from . import ui
    ui.register()


def unregister():
    from . import ui
    ui.unregister()
