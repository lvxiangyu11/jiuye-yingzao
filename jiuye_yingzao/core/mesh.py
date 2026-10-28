# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Xiangyu Lyu and the Jiuye Yingzao contributors
"""Mesh building blocks.

Refactored from lanxi_map_editor.generators.houses.Part: one mesh per building component,
shared materials by key, metre-based UVs (timber along its long axis). Added: sub-assembly
transforms (mark/transform), oriented beams, tapered/entasis columns, profile extrusion,
sweeps and two-sided shells.
"""
import math
import bmesh
import bpy
from mathutils import Matrix, Vector


class Part:
    def __init__(self, name):
        self.name = name; self.v = []; self.f = []; self.mi = []; self.sm = []

    def add(self, vs, fs, mat, smooth=False):
        o = len(self.v)
        self.v.extend(tuple(map(float, v)) for v in vs)
        self.f.extend(tuple(i + o for i in f) for f in fs)
        self.mi.extend([mat] * len(fs)); self.sm.extend([smooth] * len(fs))

    def mark(self):
        return len(self.v)

    def transform(self, start, matrix):
        """Apply a 4x4 matrix to vertices added since mark()."""
        for i in range(start, len(self.v)):
            self.v[i] = tuple(matrix @ Vector(self.v[i]))

    def extend(self, other, matrix=None):
        start = self.mark()
        self.add(other.v, [], None)
        self.v[start:] = [tuple(matrix @ Vector(v)) if matrix else v for v in other.v]
        self.f.extend(tuple(i + start for i in f) for f in other.f)
        self.mi.extend(other.mi); self.sm.extend(other.sm)

    def tri_count(self):
        return sum(len(f) - 2 for f in self.f)

    def finish(self, root, collection, mats, weld=0.0005):
        if not self.f:
            return None
        mesh = bpy.data.meshes.new(root.name + '_' + self.name)
        mesh.from_pydata(self.v, [], self.f); mesh.update()
        used = list(dict.fromkeys(self.mi))
        for key in used:
            mesh.materials.append(mats[key])
        for p, key, smooth in zip(mesh.polygons, self.mi, self.sm):
            p.material_index = used.index(key); p.use_smooth = smooth
        bm = bmesh.new(); bm.from_mesh(mesh)          # face material/smooth survive welding
        if weld:
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld)
        bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh); bm.free(); mesh.update()
        uv = mesh.uv_layers.new(name='UV0')
        co = [v.co for v in mesh.vertices]
        for p in mesh.polygons:
            key = used[p.material_index]
            n = p.normal; axis = max(range(3), key=lambda i: abs(n[i])); axes = [i for i in range(3) if i != axis]
            if key.startswith(('wood', 'ochre', 'lacquer', 'bamboo')):
                span = {i: max(co[v][i] for v in p.vertices) - min(co[v][i] for v in p.vertices) for i in axes}
                axes.sort(key=lambda i: -span[i])
            horiz = Vector((-n.y, n.x, 0)) if abs(n.z) < .7 and (abs(n.x) + abs(n.y)) > 1e-6 else None
            for li in p.loop_indices:
                c = co[mesh.loops[li].vertex_index]
                if horiz is not None and not key.startswith(('wood', 'ochre', 'lacquer', 'bamboo')):
                    uv.data[li].uv = (c.dot(horiz.normalized()), c.z)   # walls: continuous along the facade
                else:
                    uv.data[li].uv = (c[axes[0]], c[axes[1]])
        ob = bpy.data.objects.new(mesh.name, mesh)
        collection.objects.link(ob); ob.parent = root; ob['lyz_component'] = self.name
        return ob


# ------------------------------------------------------------------ primitives
BOX_FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def box(part, c, s, mat, angle=0.0):
    """Axis box centred at c, size s, rotated about Z."""
    hx, hy, hz = s[0] / 2, s[1] / 2, s[2] / 2; ca, sa = math.cos(angle), math.sin(angle); vs = []
    for x, y, z in [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz), (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]:
        vs.append((c[0] + x * ca - y * sa, c[1] + x * sa + y * ca, c[2] + z))
    part.add(vs, BOX_FACES, mat)


def box_minmax(part, lo, hi, mat):
    box(part, [(a + b) / 2 for a, b in zip(lo, hi)], [b - a for a, b in zip(lo, hi)], mat)


def beam(part, a, b, w, h, mat, up=(0, 0, 1)):
    """Rectangular member from a to b; w across (horizontal), h vertical-ish."""
    a = Vector(a); b = Vector(b); d = b - a
    if d.length < 1e-6:
        return
    d.normalize(); u = Vector(up)
    if abs(d.dot(u)) > .95:
        u = Vector((1, 0, 0))
    side = d.cross(u).normalized(); upv = side.cross(d).normalized()
    vs = []
    for p in (a, b):
        for sx, sz in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
            vs.append(p + side * sx * w / 2 + upv * sz * h / 2)
    part.add(vs, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], mat)


def tube(part, points, r, mat, sides=8, caps=True, smooth=True, radii=None):
    ps = [Vector(p) for p in points]
    if len(ps) < 2:
        return
    vs = []; fs = []
    for i, p in enumerate(ps):
        d = (ps[min(i + 1, len(ps) - 1)] - ps[max(i - 1, 0)]).normalized()
        ref = Vector((0, 0, 1)) if abs(d.z) < .94 else Vector((1, 0, 0))
        u = d.cross(ref).normalized(); v = d.cross(u).normalized(); rr = radii[i] if radii else r
        vs.extend(p + rr * (u * math.cos(math.tau * j / sides) + v * math.sin(math.tau * j / sides)) for j in range(sides))
    for i in range(len(ps) - 1):
        for j in range(sides):
            a = i * sides + j; b = i * sides + (j + 1) % sides; fs.append((a, b, b + sides, a + sides))
    if caps:
        fs.extend([tuple(range(sides - 1, -1, -1)), tuple((len(ps) - 1) * sides + j for j in range(sides))])
    part.add(vs, fs, mat, smooth)


def column(part, x, y, z0, z1, r_base, mat, sides=12, taper=.1, entasis=0.0, lean=(0, 0), square=False):
    """Column with top taper (收分), Song 卷杀/梭柱 entasis and 侧脚 lean (dx, dy at the top)."""
    rings = 6 if entasis else 2; pts = []; radii = []
    for k in range(rings):
        t = k / (rings - 1)
        r = r_base * (1 - taper * t)
        if entasis:                       # 梭柱: swell in the lower third, roll-off (卷杀) in the upper third
            r *= 1 + entasis * math.sin(math.pi * min(1, t * 1.5)) * .5 - entasis * max(0, t - .66) * 1.5
        pts.append((x + lean[0] * t, y + lean[1] * t, z0 + (z1 - z0) * t)); radii.append(r)
    if square:
        for i in range(len(pts) - 1):
            beam(part, pts[i], pts[i + 1], radii[i] * 1.8, radii[i] * 1.8, mat, up=(1, 0, 0))
    else:
        tube(part, pts, r_base, mat, sides, True, True, radii)


def prism(part, outline, z0, z1, mat, top_mat=None):
    """Extrude a closed XY polygon (counter-clockwise) between z0 and z1."""
    n = len(outline)
    vs = [(x, y, z0) for x, y in outline] + [(x, y, z1) for x, y in outline]
    fs = [tuple(range(n - 1, -1, -1))]
    part.add(vs, fs, mat)
    part.add(vs, [tuple(range(n, 2 * n))], top_mat or mat)
    part.add(vs, [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)], mat)


def extrude_profile(part, outline, thickness, mat, matrix):
    """Extrude a 2D (u, v) outline by thickness along local Y, then place with matrix (local X=u, Z=v)."""
    n = len(outline); vs = []
    for y in (-thickness / 2, thickness / 2):
        for u, v in outline:
            vs.append(tuple(matrix @ Vector((u, y, v))))
    fs = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    part.add(vs, fs, mat)


def sweep(part, profile, path, mat, closed_profile=True, caps=True, smooth=False):
    """Sweep a 2D profile [(s, t)] along a 3D path; s across (horizontal normal), t up."""
    ps = [Vector(p) for p in path]; n = len(profile); vs = []; fs = []
    for i, p in enumerate(ps):
        d = (ps[min(i + 1, len(ps) - 1)] - ps[max(i - 1, 0)]).normalized()
        up = Vector((0, 0, 1)) if abs(d.z) < .95 else Vector((1, 0, 0))
        side = d.cross(up).normalized(); upv = side.cross(d).normalized()
        vs.extend(p + side * s + upv * t for s, t in profile)
    m = n if closed_profile else n - 1
    for i in range(len(ps) - 1):
        for j in range(m):
            a = i * n + j; b = i * n + (j + 1) % n; fs.append((a, b, b + n, a + n))
    if caps and closed_profile:
        fs.extend([tuple(range(n - 1, -1, -1)), tuple((len(ps) - 1) * n + j for j in range(n))])
    part.add(vs, fs, mat, smooth)


def grid(nu, nv, point):
    vs = []; rows = []
    for j in range(nv + 1):
        row = []
        for i in range(nu + 1):
            row.append(len(vs)); vs.append(tuple(point(i / nu, j / nv)))
        rows.append(row)
    fs = [(rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]) for j in range(nv) for i in range(nu)]
    edge = list(zip(rows[0][:-1], rows[0][1:])) + list(zip(rows[-1][1:], rows[-1][:-1])) + \
        [(rows[j][0], rows[j + 1][0]) for j in range(nv)] + [(rows[j + 1][-1], rows[j][-1]) for j in range(nv)]
    return vs, fs, edge


def shell(part, nu, nv, point, thickness, top, bottom, smooth=False, normal_offset=None):
    """Two-sided slab: top surface from point(u, v), bottom offset straight down by thickness."""
    vs, fs, edge = grid(nu, nv, point); n = len(vs)
    low = [(x, y, z - thickness) for x, y, z in vs]
    part.add(vs, fs, top, smooth)
    part.add(low, [tuple(reversed(f)) for f in fs], bottom, smooth)
    allv = vs + low
    part.add(allv, [(a, b, b + n, a + n) for a, b in edge], bottom, smooth)


def rotz(angle, origin=(0, 0, 0)):
    o = Vector(origin)
    return Matrix.Translation(o) @ Matrix.Rotation(angle, 4, 'Z') @ Matrix.Translation(-o)


def place(x, y, z, angle=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(angle, 4, 'Z')
