# -*- coding: utf-8 -*-
"""
plan_17_export_probe.py —— 确定「导出动画 FBX 时如何保证 bind pose 正确」的正确做法

背景（plan_16 审计结果）：历史产物 17 个 FBX 中 15 个 bind pose 已损坏，
关节间距偏差 1.4%~15.4%。四个批量重定向脚本（blender_10/30/50/51）都是
「循环内先 action=None，随即又挂回 action，且不 frame_set」——需要确定修法。

本脚本在同一场景内用三种方式各导出一个 FBX，再逐个重新导入比对，
回答：`bake_anim_use_all_actions=False` 的逐 action 导出能否保证 bind pose 正确？

  A. 复现历史做法：挂 action + frame_set(20) → 导出（all_actions=False）
  B. 只复位不复位 action：action=None + 清 basis → 导出（all_actions=False）
  C. plan_10 已验证的做法：action=None + 清 basis → 导出（all_actions=True）

用法:
  blender -b -P Scripts/plan_17_export_probe.py -- <SRC_GLB> <OUTDIR> <REPORT_TXT>
"""
import bpy
import sys
import os
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC_GLB = argv[0]
OUTDIR = argv[1]
OUT = argv[2]
os.makedirs(OUTDIR, exist_ok=True)

lines = []


def P(s=""):
    lines.append(str(s))


PROBE = ["Root", "Pelvis", "L_Hip", "L_KneeLower", "L_Foot", "L_Toe", "Head", "L_Hand", "R_Hand"]
PAIRS = [("L_Hip", "L_KneeLower"), ("L_KneeLower", "L_Foot"), ("L_Foot", "L_Toe"),
         ("Pelvis", "Head"), ("L_Hip", "R_Hip")]

# ---------------------------------------------------------------- 导入源
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
sc.render.fps_base = 1.0
bpy.ops.import_scene.gltf(filepath=SRC_GLB)

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
mw = arm.matrix_world


def heads_now():
    return {b.name: (mw @ b.head_local).copy() for b in arm.data.bones if b.name in PROBE}


REST = heads_now()
REST_DIST = {("%s-%s" % p): (REST[p[0]] - REST[p[1]]).length for p in PAIRS if p[0] in REST and p[1] in REST}

P("=" * 96)
P("### plan_17 —— 导出行为探针")
P("=" * 96)
P("SRC = %s" % SRC_GLB)
P("源骨架 rest 间距：")
for k, v in REST_DIST.items():
    P("   %-26s %10.5f" % (k, v))

ACT = "darius_skin15_run"
act = bpy.data.actions.get(ACT)
if act is None:
    raise SystemExit("找不到 action %s" % ACT)
P("测试用 action = %s  frames %s" % (ACT, tuple(int(x) for x in act.frame_range)))


def set_action(a):
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = a
    if a is not None and hasattr(arm.animation_data, "action_slot") and len(getattr(a, "slots", [])) > 0:
        for s in a.slots:
            if getattr(s, "target_id_type", None) == 'OBJECT':
                arm.animation_data.action_slot = s
                break


def clear_pose():
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()


def export(path, all_actions):
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    kw = dict(filepath=path, use_selection=True, bake_anim=True,
              bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
              bake_anim_use_all_actions=all_actions,
              bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0,
              add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X',
              apply_unit_scale=True, global_scale=1.0, armature_nodetype='NULL')
    bpy.ops.export_scene.fbx(**kw)


# ---------------- A: 复现历史做法 ----------------
set_action(act)
sc.frame_set(20)
bpy.context.view_layer.update()
PA = os.path.join(OUTDIR, "PROBE_A_action_mounted.fbx").replace("\\", "/")
export(PA, False)
P("")
P("A 导出完成（挂 action + frame_set(20)，all_actions=False）: %s" % os.path.basename(PA))

# ---------------- B: 只清 pose，all_actions=False ----------------
clear_pose()
PB = os.path.join(OUTDIR, "PROBE_B_cleared_noall.fbx").replace("\\", "/")
export(PB, False)
P("B 导出完成（清 pose，all_actions=False）: %s" % os.path.basename(PB))

# ---------------- C: plan_10 做法 ----------------
clear_pose()
PC = os.path.join(OUTDIR, "PROBE_C_cleared_all.fbx").replace("\\", "/")
export(PC, True)
P("C 导出完成（清 pose，all_actions=True）: %s" % os.path.basename(PC))

# ---------------------------------------------------------------- 逐个重新导入检查
P("")
P("=== 重新导入比对 ===")
P("  %-34s %6s %6s %12s  %s" % ("file", "bones", "anims", "maxRelDev", "verdict"))

for tag, path in (("A", PA), ("B", PB), ("C", PC)):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=False)
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    if not arms:
        P("  %-34s <无骨架>" % os.path.basename(path))
        continue
    a2 = arms[0]
    m2 = a2.matrix_world
    h2 = {b.name: (m2 @ b.head_local).copy() for b in a2.data.bones if b.name in PROBE}
    nanim = len(bpy.data.actions)
    devs = []
    for k, d0 in REST_DIST.items():
        p = k.split("-")
        if p[0] in h2 and p[1] in h2:
            d1 = (h2[p[0]] - h2[p[1]]).length
            devs.append(abs(d1 - d0) / d0 if d0 > 1e-9 else 0.0)
    mx = max(devs) if devs else -1
    verdict = "OK" if 0 <= mx < 1e-3 else ("**BROKEN**" if mx >= 1e-3 else "?")
    P("  %-34s %6d %6d %12.3e  %s" % (os.path.basename(path), len(a2.data.bones), nanim, mx, verdict))

P("")
P("=== 判据 ===")
P("  A 若 BROKEN ⇒ 「挂 action 导出」本身就污染 bind pose，逐 action 导出不可行，")
P("               必须改为 all_actions=True 单文件导出（并同步下游导入脚本）。")
P("  B 若 OK 但 anims=0 ⇒ 清 pose 能修 bind pose，但该模式导不出动画。")
P("  C 应为 OK 且 anims≈46（plan_10 已验证过的做法）。")
P("=== DONE ===")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("WROTE %s" % OUT)
