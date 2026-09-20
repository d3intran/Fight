# -*- coding: utf-8 -*-
"""
plan_12_rest_stability.py —— rest matrix_local 重算稳定性的三组对照实验

动机：
  plan_10_src_clean 报出「最大 rest 偏差 = 2.680e-04 (R_Foot)」，并使 R_Foot 的下游
  世界位置偏差（0.0135 单位）比上游 R_KneeLower（0.000091）大 148 倍。
  必须判定这是本次手术的损伤，还是 Blender edit-mode 骨架重建的固有特性。

三组对照（同一进程、同一 armature，逐级加压）：
  A. 仅进出 EDIT mode，零修改
  B. 删掉一根与人体无关的骨（Piece_1）
  C. 删除全部非人体骨（模拟 plan_10 的删除量）+ 重挂 KneeLower/Elbow

用法:
  blender -b -P Scripts/retarget/plan_12_rest_stability.py -- <SRC_GLB> <OUT_TXT>
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


WATCH = ["R_Foot", "L_Foot", "R_Toe", "L_Toe", "R_KneeLower", "L_KneeLower",
         "R_KneeUpper", "L_KneeUpper", "R_Hip", "Pelvis", "Head"]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]

bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
bpy.context.view_layer.objects.active = arm


def snap():
    return {b.name: b.matrix_local.copy() for b in arm.data.bones}


def diff(before, label):
    rows = []
    for n, m in before.items():
        if n not in arm.data.bones:
            continue
        d = max(abs(arm.data.bones[n].matrix_local[i][j] - m[i][j])
                for i in range(4) for j in range(4))
        rows.append((d, n))
    rows.sort(reverse=True)
    P("")
    P("=== %s ===" % label)
    P("  偏差 > 1e-5 的骨数 = %d / %d" % (sum(1 for d, _ in rows if d > 1e-5), len(rows)))
    P("  top 8:")
    for d, n in rows[:8]:
        mark = "   <<< 关注" if n in WATCH else ""
        P("     %-42s %.3e%s" % (n, d, mark))
    return dict(rows)


P("骨数 = %d" % len(arm.data.bones))

# ---------------- A. 零修改 ----------------
b0 = snap()
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.armature.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode='OBJECT')
dA = diff(b0, "对照 A：仅进出 EDIT mode（零修改）")

# ---------------- B. 删一根无关骨 ----------------
b1 = snap()
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
bpy.ops.armature.select_all(action='DESELECT')
eb["Piece_1"].select = True
bpy.ops.armature.delete()
bpy.ops.object.mode_set(mode='OBJECT')
dB = diff(b1, "对照 B：删除一根与人体无关的骨（Piece_1）")

# ---------------- C. 模拟手术量级 ----------------
KEEP = set([
    "Root", "Pelvis", "Spine1", "Spine2", "Neck", "Head", "Jaw",
    "L_Hip", "L_KneeLower", "L_Foot", "L_Toe",
    "R_Hip", "R_KneeLower", "R_Foot", "R_Toe",
    "L_Clavicle", "L_Shoulder", "L_Elbow", "L_Hand",
    "R_Clavicle", "R_Shoulder", "R_Elbow", "R_Hand",
] + ["%s_%s%d" % (s, f, i) for s in "LR" for f in ("Thumb", "Index", "Middle", "Ring", "Pinky") for i in (1, 2)]
  + ["Cape"] + ["%s_Cape%d" % (p, i) for p in ("C", "L", "R") for i in range(1, 6)])

b2 = snap()
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
rest_snap = {}
for n in KEEP:
    b = eb.get(n)
    if b is not None:
        rest_snap[n] = (b.head.copy(), b.tail.copy(), b.roll)

for child, newp in (("L_KneeLower", "L_Hip"), ("R_KneeLower", "R_Hip"),
                    ("L_Elbow", "L_Shoulder"), ("R_Elbow", "R_Shoulder")):
    eb[child].parent = eb[newp]
    eb[child].use_connect = False

bpy.ops.armature.select_all(action='DESELECT')
for b in eb:
    if b.name not in KEEP:
        b.select = True
bpy.ops.armature.delete()

rest_dev = 0.0
for n in KEEP:
    b = eb.get(n)
    if b is not None:
        b.use_connect = False
for n in KEEP:
    b = eb.get(n)
    if b is None:
        continue
    h, t, r = rest_snap[n]
    b.head = h
    b.tail = t
    b.roll = r
    rest_dev = max(rest_dev, (b.head - h).length, (b.tail - t).length, abs(b.roll - r))
bpy.ops.object.mode_set(mode='OBJECT')

dC = diff(b2, "对照 C：删除 120 骨 + 重挂 KneeLower/Elbow + 写回 rest 快照")
P("")
P("  C 组 edit_bone head/tail/roll 与快照的偏差 = %.3e" % rest_dev)
P("  剩余骨 = %d" % len(arm.data.bones))

P("")
P("=== 判据 ===")
P("  A 全 0 且 B/C 中 R_Foot 出现 ~1e-4 量级偏差 ⇒ 偏差由「armature.delete() 触发")
P("  的 Bone.matrix_local 重建」产生，与本次手术的具体内容无关。")
P("  A 与 B 均全 0 而仅 C 出现 ⇒ 与重挂 KneeLower 的操作相关，需继续排查。")
P("=== DONE ===")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("WROTE %s" % OUT)
