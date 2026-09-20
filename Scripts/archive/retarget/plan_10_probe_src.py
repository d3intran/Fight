# -*- coding: utf-8 -*-
"""
plan_10_probe_src.py —— 源骨架结构全量实测（为白名单净化提供依据）

用法:
  blender -b -P Scripts/plan_10_probe_src.py -- <SRC_GLB> <OUT_TXT>

输出（写入 OUT_TXT，UTF-8）:
  - 场景 fps / 对象清单 / armature 数
  - 全骨清单（名 | 父 | 长度(m) | 子数）
  - 根骨与子树规模（识别独立道具子树）
  - 前缀分组统计
  - 完整层级树（不截断，含 head/tail 的世界 Z）
  - actions 清单（帧范围 + 被驱动的骨骼数）
  - 腿链 / 臂链深挖（从 L_Hip、L_Shoulder 递归全部深度）

严禁在其中做任何资产修改——本脚本只读。
"""
import bpy
import sys
import os

argv = sys.argv[sys.argv.index("--") + 1:]
SRC = argv[0]
OUT = argv[1]

lines = []


def P(s=""):
    lines.append(str(s))


d = os.path.dirname(OUT)
if d and not os.path.isdir(d):
    os.makedirs(d, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
sc.render.fps_base = 1.0

bpy.ops.import_scene.gltf(filepath=SRC)

P("SRC = %s" % SRC)
P("scene fps = %s / base = %s" % (sc.render.fps, sc.render.fps_base))
P("objects = %d" % len(bpy.data.objects))
for o in bpy.data.objects:
    P("   obj %-46s type=%-9s parent=%s" % (o.name, o.type, o.parent.name if o.parent else "-"))

arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
P("")
P("armatures = %d -> %s" % (len(arms), [a.name for a in arms]))
if not arms:
    raise SystemExit("NO ARMATURE")

arm = arms[0]
bones = arm.data.bones
mw = arm.matrix_world
P("bone count = %d" % len(bones))
P("armature matrix_world:")
for r in mw:
    P("    " + "  ".join("%9.5f" % x for x in r))


def blen(b):
    return (mw @ b.tail_local - mw @ b.head_local).length


def headw(b):
    return mw @ b.head_local


def tailw(b):
    return mw @ b.tail_local


# ---------- 1. 全骨清单 ----------
P("")
P("=== [1] ALL BONES : name | parent | len(m) | #children ===")
for b in sorted(bones, key=lambda x: x.name):
    P("%-42s | %-42s | %10.5f | %d" % (
        b.name, b.parent.name if b.parent else "-", blen(b), len(b.children)))


# ---------- 2. 根骨与子树规模 ----------
def count_sub(b):
    n = 1
    for c in b.children:
        n += count_sub(c)
    return n


P("")
P("=== [2] ROOTS (独立子树识别) ===")
roots = [b for b in bones if b.parent is None]
for r in sorted(roots, key=lambda x: -count_sub(x)):
    P("%-42s subtree=%4d  len=%10.5f" % (r.name, count_sub(r), blen(r)))


# ---------- 3. 前缀分组 ----------
P("")
P("=== [3] PREFIX GROUPS (name.split('_')[0]) ===")
grp = {}
for b in bones:
    grp.setdefault(b.name.split("_")[0], []).append(b.name)
for k in sorted(grp, key=lambda x: -len(grp[x])):
    v = grp[k]
    P("%-26s %4d   %s" % (k, len(v), (", ".join(v[:8]) + (" ..." if len(v) > 8 else ""))))


# ---------- 4. 完整层级树 ----------
P("")
P("=== [4] FULL HIERARCHY : (depth-indent) name  len  headZ  tailZ ===")
def walk(b, depth=0):
    P("%s%-38s %9.5f  hz=%8.5f  tz=%8.5f" % (
        "  " * depth, b.name, blen(b), headw(b).z, tailw(b).z))
    for c in b.children:
        walk(c, depth + 1)


for r in roots:
    walk(r, 0)


# ---------- 5. actions ----------
# Blender 4.4+ 用 slotted action（layers -> strips -> channelbags），A.fcurves 已移除
def action_fcurves(a):
    try:
        fcs = list(a.fcurves)
        if fcs:
            return fcs
    except AttributeError:
        pass
    out = []
    for layer in getattr(a, "layers", []):
        for strip in getattr(layer, "strips", []):
            # 4.4 命名：channelbags；兼容旧命名 channelbag
            cbs = getattr(strip, "channelbags", None) or []
            for cb in cbs:
                out.extend(cb.fcurves)
    return out


P("")
P("=== [5] ACTIONS ===")
acts = list(bpy.data.actions)
P("action count = %d" % len(acts))
P("has_action_layers_api = %s" % (hasattr(acts[0], "layers") if acts else "n/a"))
for a in sorted(acts, key=lambda x: x.name):
    fr = a.frame_range
    fcs = action_fcurves(a)
    driven = set()
    for fc in fcs:
        dp = fc.data_path
        if '"' in dp:
            driven.add(dp.split('"')[1])
    P("%-44s frames=%7.2f ~ %7.2f  span=%6.1f  fcurves=%5d  bones=%3d" % (
        a.name, fr[0], fr[1], fr[1] - fr[0], len(fcs), len(driven)))


# ---------- 6. 腿链 / 臂链深挖 ----------
P("")
P("=== [6] LEG / ARM CHAIN DEEP DIVE ===")
probes = ["L_Hip", "R_Hip", "L_Shoulder", "R_Shoulder", "Neck", "Head", "Root", "Pelvis"]
for pn in probes:
    b = bones.get(pn)
    if b is None:
        P("-- %s : NOT FOUND (尝试模糊匹配: %s)" % (
            pn, [x.name for x in bones if pn.split('_')[-1].lower() in x.name.lower()][:10]))
        continue
    P("")
    P("-- chain from %s --" % pn)

    def cw(x, depth=0):
        h, t = headw(x), tailw(x)
        P("   %s%-34s len=%9.5f  head=(%8.4f,%8.4f,%8.4f) tail=(%8.4f,%8.4f,%8.4f)" % (
            "  " * depth, x.name, blen(x), h.x, h.y, h.z, t.x, t.y, t.z))
        for c in x.children:
            cw(c, depth + 1)

    cw(b)

# ---------- 7. 蒙皮网格与顶点组 ----------
P("")
P("=== [7] MESHES ===")
for o in bpy.data.objects:
    if o.type == 'MESH':
        vg = [g.name for g in o.vertex_groups]
        P("%-46s verts=%-7d vgroups=%-4d modifier=%s" % (
            o.name, len(o.data.vertices), len(vg),
            [(m.type, getattr(m, 'object', None).name if getattr(m, 'object', None) else None) for m in o.modifiers]))

P("")
P("=== DONE ===")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print("WROTE %s  (%d lines)" % (OUT, len(lines)))
