# -*- coding: utf-8 -*-
"""
plan_11_action_probe.py —— 验证 Blender 5.2 slotted action 能否可靠逐 action 采样

这是净化脚本的前置可行性验证。必须回答三个问题：
  Q1. glTF 导入后，46 个 action 是否都能挂到 armature 上（slotted action 的 slot 绑定）？
  Q2. frame_set 后 pose bone 的世界矩阵是否随帧变化（依赖图是否真的在求值）？
  Q3. 孪生骨（L_KneeLower / L_Elbow）相对其父骨的局部变换在动画中是否真的静止？

用法:
  blender -b -P Scripts/plan_11_action_probe.py -- <SRC_GLB> <OUT_TXT>
"""
import bpy
import sys
import os
import math

argv = sys.argv[sys.argv.index("--") + 1:]
SRC = argv[0]
OUT = argv[1]

lines = []


def P(s=""):
    lines.append(str(s))


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
sc.render.fps_base = 1.0
bpy.ops.import_scene.gltf(filepath=SRC)

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
P("armature = %s" % arm.name)
P("armature.matrix_world is identity: %s" % (arm.matrix_world == arm.matrix_world.Identity(4)))

ad = arm.animation_data
P("")
P("=== animation_data ===")
P("animation_data = %s" % ad)
if ad is None:
    arm.animation_data_create()
    ad = arm.animation_data
    P("created animation_data")

P("current action = %s" % (ad.action.name if ad.action else None))
P("has action_slot attr = %s" % hasattr(ad, "action_slot"))
if hasattr(ad, "action_slot"):
    P("current action_slot = %s" % ad.action_slot)
P("nla_tracks = %d" % len(ad.nla_tracks))
for t in ad.nla_tracks:
    P("  track '%s' mute=%s strips=%s" % (
        t.name, t.mute,
        [(s.name, s.action.name if s.action else None, s.frame_start, s.frame_end) for s in t.strips]))

P("")
P("=== actions: slots ===")
for a in sorted(bpy.data.actions, key=lambda x: x.name)[:6]:
    slots = getattr(a, "slots", [])
    P("%-42s slots=%d  %s" % (
        a.name, len(slots),
        [(getattr(s, "name_display", getattr(s, "name", "?")), getattr(s, "target_id_type", "?")) for s in slots]))


def set_action(act):
    """把 action 挂到 armature 上，兼容 Blender 4.4+ slotted action。返回是否成功。"""
    if arm.animation_data is None:
        arm.animation_data_create()
    a = arm.animation_data
    a.action = act
    if hasattr(a, "action_slot") and len(getattr(act, "slots", [])) > 0:
        # 优先选 target 为 OBJECT 的 slot
        chosen = None
        for s in act.slots:
            if getattr(s, "target_id_type", None) == 'OBJECT':
                chosen = s
                break
        a.action_slot = chosen if chosen is not None else act.slots[0]
    return a.action is act


P("")
P("=== switch test over ALL %d actions ===" % len(bpy.data.actions))
ok_cnt = 0
fail = []
for a in sorted(bpy.data.actions, key=lambda x: x.name):
    try:
        set_action(a)
        bound = (arm.animation_data.action is a)
        fr = a.frame_range
        f_mid = int((fr[0] + fr[1]) / 2)
        sc.frame_set(int(fr[0]))
        m0 = arm.pose.bones["Pelvis"].matrix.translation.copy()
        sc.frame_set(f_mid)
        m1 = arm.pose.bones["Pelvis"].matrix.translation.copy()
        delta = (m1 - m0).length
        if bound:
            ok_cnt += 1
        else:
            fail.append((a.name, "not bound"))
        if a.name in ("darius_skin15_idle1", "darius_skin15_run", "darius_skin15_attack1",
                      "darius_skin15_turn_l", "darius_skin15_spell1"):
            P("  %-42s bound=%s  frames=%d..%d  pelvis delta(0->mid)=%8.4f" % (
                a.name, bound, fr[0], fr[1], delta))
    except Exception as ex:
        fail.append((a.name, repr(ex)))

P("bound ok = %d / %d" % (ok_cnt, len(bpy.data.actions)))
for n, e in fail[:20]:
    P("  FAIL %-42s %s" % (n, e))


# ---------- 深度采样三个代表动作 ----------
P("")
P("=== per-action deep sample ===")
WATCH = ["Root", "Pelvis", "Spine1", "Spine2", "Neck", "Head", "Jaw",
         "L_Hip", "L_KneeUpper", "L_KneeLower", "L_Foot", "L_Toe",
         "R_Hip", "R_KneeUpper", "R_KneeLower", "R_Foot", "R_Toe",
         "L_Clavicle", "L_Shoulder", "L_ElbowUpper", "L_Elbow", "L_Hand",
         "R_Clavicle", "R_Shoulder", "R_ElbowUpper", "R_Elbow", "R_Hand",
         "Cape", "C_Cape1", "L_Cape1", "R_Cape1",
         "Lion_Root", "Lion_Spine1", "Weapon", "Axe_Head", "Throne"]

for nm in ("darius_skin15_idle1", "darius_skin15_run", "darius_skin15_run_fast"):
    act = bpy.data.actions.get(nm)
    if act is None:
        P("MISSING %s" % nm)
        continue
    set_action(act)
    fr = act.frame_range
    f0, f1 = int(fr[0]), int(fr[1])
    P("")
    P("== %s   frames %d..%d ==" % (nm, f0, f1))

    # 世界位置变化幅度（判断该骨是否真的被动）
    P("  -- world-position spread (max pairwise) per bone --")
    for bn in WATCH:
        pb = arm.pose.bones.get(bn)
        if pb is None:
            continue
        pts = []
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            pts.append(pb.matrix.translation.copy())
        spread = 0.0
        for i in range(0, len(pts), max(1, len(pts) // 12)):
            for j in range(0, len(pts), max(1, len(pts) // 12)):
                d = (pts[i] - pts[j]).length
                if d > spread:
                    spread = d
        P("     %-16s %10.4f" % (bn, spread))

    # 孪生骨的局部 basis 变化
    P("  -- twin-bone matrix_basis drift (relative to rest) --")
    for bn in ("L_KneeLower", "R_KneeLower", "L_Elbow", "R_Elbow",
               "L_KneeUpper", "R_KneeUpper", "L_ElbowUpper", "R_ElbowUpper"):
        pb = arm.pose.bones.get(bn)
        if pb is None:
            continue
        sc.frame_set(f0)
        base = pb.matrix_basis.copy()
        max_ang = 0.0
        max_tr = 0.0
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            mb = pb.matrix_basis
            q = base.to_quaternion().rotation_difference(mb.to_quaternion())
            max_ang = max(max_ang, math.degrees(q.angle))
            max_tr = max(max_tr, (mb.translation - base.translation).length)
        P("     %-16s rot=%8.3f deg   loc=%9.5f" % (bn, max_ang, max_tr))

P("")
P("=== DONE ===")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("WROTE %s (%d lines)" % (OUT, len(lines)))
