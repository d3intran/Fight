# -*- coding: utf-8 -*-
"""
plan_13_verify_fbx.py —— M1-① 端到端验收：净化后的 FBX 是否保真

这是净化管线的最终判据。前一层验证（plan_10 内部）只在同一 Blender 会话内
比较「净化前 vs 净化后」，无法发现 FBX 导出/导入环节的损失。本脚本换成
「独立两次导入」：一次导入源 GLB，一次导入净化后的 FBX，在**不同会话**里
各自测量，再对比 —— 与任何内部实现假设无关（AGENTS.md §0.3）。

对比项（全部用缩放不变量，避免 Blender↔FBX 的单位换算干扰）：
  1. 骨数 / 动画数 / 每个动画的帧数
  2. 骨骼关节间距（用 head_local 算；head 是唯一可靠的关节真值，tail 不可信）
  3. 代表动画逐帧的关节世界坐标，按身高归一化后比对

用法:
  blender -b -P Scripts/plan_13_verify_fbx.py -- <SRC_GLB> <CLEAN_FBX> <OUT_TXT>
"""
import bpy
import sys
import os
import math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC_GLB = argv[0]
CLEAN_FBX = argv[1]
OUT = argv[2]

lines = []


def P(s=""):
    lines.append(str(s))


# 应保留的关节（head_local 才有意义）
JOINTS = ["Root", "Pelvis", "L_Hip", "L_KneeLower", "L_Foot", "L_Toe",
          "R_Hip", "R_KneeLower", "R_Foot", "L_Clavicle", "L_Shoulder",
          "L_Elbow", "L_Hand", "R_Shoulder", "R_Elbow", "R_Hand", "Neck", "Head"]

# 缩放不变的间距对（源侧实测值，见 probe_src_bones.txt）
DIST_PAIRS = [
    ("L_Hip", "L_KneeLower"),        # 大腿 48.84
    ("L_KneeLower", "L_Foot"),       # 小腿 50.63
    ("L_Hip", "R_Hip"),              # 髋宽 26.55
    ("L_Shoulder", "L_Elbow"),       # 上臂 40.54
    ("L_Elbow", "L_Hand"),           # 前臂 29.73
    ("L_Shoulder", "R_Shoulder"),    # 肩宽 46.69
    ("Pelvis", "Head"),              # 躯干链
    ("L_Foot", "L_Toe"),             # 脚长 13.82
]

PROBE_ACTS = ["idle1", "run", "run_fast", "turn_l", "spell4_5", "idle2"]

# 身高标尺必须用**固定的同一组骨**在两侧各算一次。
# 若用"全部骨"，GLB 侧会混入 Gem(z=396.8) / Axe_Handle(z=-90.8) 等道具骨，
# 而 FBX 侧只有 59 骨，会算出 2.36 倍的假缩放因子（已踩过）。
REF_BONES = ["Root", "Pelvis", "Spine1", "Spine2", "Neck", "Head", "Jaw",
             "L_Hip", "L_KneeLower", "L_Foot", "L_Toe",
             "R_Hip", "R_KneeLower", "R_Foot", "R_Toe",
             "L_Clavicle", "L_Shoulder", "L_Elbow", "L_Hand",
             "R_Clavicle", "R_Shoulder", "R_Elbow", "R_Hand",
             "Cape", "C_Cape1", "L_Cape1", "R_Cape1"]


def action_fcurves(act):
    out = []
    for layer in getattr(act, "layers", []):
        for strip in getattr(layer, "strips", []):
            for cb in (getattr(strip, "channelbags", None) or []):
                out.extend(cb.fcurves)
    if out:
        return out
    try:
        return list(act.fcurves)
    except AttributeError:
        return []


def set_action(arm, act):
    if arm.animation_data is None:
        arm.animation_data_create()
    ad = arm.animation_data
    ad.action = act
    if hasattr(ad, "action_slot") and len(getattr(act, "slots", [])) > 0:
        chosen = None
        for s in act.slots:
            if getattr(s, "target_id_type", None) == 'OBJECT':
                chosen = s
                break
        ad.action_slot = chosen if chosen is not None else act.slots[0]


def load_and_measure(path, is_fbx):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.render.fps_base = 1.0
    if is_fbx:
        bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=False)
    else:
        bpy.ops.import_scene.gltf(filepath=path)

    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    if not arms:
        raise SystemExit("NO ARMATURE in %s" % path)
    arm = arms[0]
    mw = arm.matrix_world

    bones = set(b.name for b in arm.data.bones)
    head = {}
    for b in arm.data.bones:
        head[b.name] = (mw @ b.head_local).copy()
    # 同时记录 armature-local 的 head（不乘 matrix_world）。
    # 若 FBX 导入给 object 施加了变换，则 mw 版与 local 版会系统性不同，
    # 而 FBX **文件本身**的正确性应当用 local 版来判断。
    head_local = {b.name: b.head_local.copy() for b in arm.data.bones}
    mw_copy = mw.copy()

    # 身高标尺：固定骨集合 + 只用 head_local。
    # ⚠️ 不能混入 tail_local —— glTF 与 FBX 对 bone tail 的定义完全不同（tail 在 glTF
    #    导入后不可信，见 AGENTS.md），混入会把标尺污染成两套不相干的量。
    allz = [(mw @ arm.data.bones[n].head_local).z for n in REF_BONES if n in bones]
    height_raw = max(allz) - min(allz)

    # 间距用 armature-local 坐标算 —— 排除 object 级变换的干扰
    dists = {}
    for a, b in DIST_PAIRS:
        if a in head_local and b in head_local:
            dists["%s-%s" % (a, b)] = (head_local[a] - head_local[b]).length

    anims = {}
    for act in bpy.data.actions:
        fcs = action_fcurves(act)
        if not fcs:
            continue
        fr = act.frame_range
        f0, f1 = int(round(fr[0])), int(round(fr[1]))
        # FBX 导入的 action 名形如 "skinned_mesh|skinned_mesh|darius_skin15_idle1"，剥掉前缀
        key = act.name.split("|")[-1]
        anims[key] = {
            "raw_name": act.name, "f0": f0, "f1": f1, "frames": f1 - f0 + 1,
            "fcurves": len(fcs),
        }

    # 代表动画的关节世界坐标
    joint_anim = {}
    for key in PROBE_ACTS:
        m = "darius_skin15_" + key
        if m not in anims:
            joint_anim[key] = None
            continue
        act = bpy.data.actions[anims[m]["raw_name"]]
        set_action(arm, act)
        f0, f1 = anims[m]["f0"], anims[m]["f1"]
        traj = {jn: [] for jn in JOINTS}
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            for jn in JOINTS:
                pb = arm.pose.bones.get(jn)
                if pb is not None:
                    traj[jn].append(pb.matrix.translation.copy())
        joint_anim[key] = {"action": m, "traj": traj}

    return {
        "path": path, "arm": arm.name, "bone_count": len(bones), "bones": bones,
        "head": head, "head_local": head_local, "mw": mw_copy,
        "height_raw": height_raw, "dists": dists,
        "anims": anims, "joint_anim": joint_anim,
    }


P("=" * 96)
P("### plan_13 —— M1-① 端到端验收（源 GLB vs 净化 FBX）")
P("=" * 96)

P("")
P(">>> 载入源 GLB ...")
G = load_and_measure(SRC_GLB, False)
P("    armature=%s  bones=%d  actions=%d  height_raw=%.4f" % (
    G["arm"], G["bone_count"], len(G["anims"]), G["height_raw"]))

P(">>> 载入净化 FBX ...")
F = load_and_measure(CLEAN_FBX, True)
P("    armature=%s  bones=%d  actions=%d  height_raw=%.4f" % (
    F["arm"], F["bone_count"], len(F["anims"]), F["height_raw"]))

P("")
P("--- action 名对照（前 6 个）---")
P("  GLB: %s" % sorted(G["anims"].keys())[:6])
P("  FBX: %s" % sorted(F["anims"].keys())[:6])

P("")
P("--- armature object 变换（matrix_world）---")
for tag, M in (("GLB", G["mw"]), ("FBX", F["mw"])):
    P("  %s:" % tag)
    for r in M:
        P("     " + "  ".join("%10.6f" % v for v in r))

P("")
P("=== [0] 关节 head 坐标明细 ===")
P("  (a) armature-local（排除 object 变换，用于判断 FBX 文件本身的正确性）")
P("  %-14s %28s %28s %10s" % ("joint", "GLB local", "FBX local", "delta"))
_hdr = []
for jn in JOINTS:
    if jn in G["head_local"] and jn in F["head_local"]:
        a = G["head_local"][jn]
        b = F["head_local"][jn]
        _hdr.append(((a - b).length, jn))
for d, jn in sorted(_hdr, reverse=True):
    a = G["head_local"][jn]
    b = F["head_local"][jn]
    P("  %-14s (%9.4f,%9.4f,%9.4f) (%9.4f,%9.4f,%9.4f) %10.6f" % (
        jn, a.x, a.y, a.z, b.x, b.y, b.z, d))
P("")
P("  (b) 乘 matrix_world 后")
P("  %-14s %28s %28s %10s" % ("joint", "GLB world", "FBX world", "delta"))
_hdr2 = []
for jn in JOINTS:
    if jn in G["head"] and jn in F["head"]:
        _hdr2.append(((G["head"][jn] - F["head"][jn]).length, jn))
for d, jn in sorted(_hdr2, reverse=True):
    a = G["head"][jn]
    b = F["head"][jn]
    P("  %-14s (%9.4f,%9.4f,%9.4f) (%9.4f,%9.4f,%9.4f) %10.6f" % (
        jn, a.x, a.y, a.z, b.x, b.y, b.z, d))

P("")
P("=== [1] 骨数与动画数 ===")
P("  骨数：    %d -> %d" % (G["bone_count"], F["bone_count"]))
P("  动画数：  %d -> %d" % (len(G["anims"]), len(F["anims"])))
gb = G["bones"]
fb = F["bones"]
P("  白名单骨在 FBX 中缺失：%s" % (sorted(n for n in ["Root", "Pelvis", "Spine1", "Spine2", "Neck",
    "Head", "Jaw", "L_Hip", "L_KneeLower", "L_Foot", "L_Toe", "R_Hip", "R_KneeLower", "R_Foot",
    "R_Toe", "L_Clavicle", "L_Shoulder", "L_Elbow", "L_Hand", "R_Clavicle", "R_Shoulder",
    "R_Elbow", "R_Hand", "Cape"] if n not in fb) or "无"))
P("  已删骨在 FBX 中残留：%s" % (sorted(n for n in ["Lion_Root", "Throne", "Gem", "Weapon",
    "Axe_Head", "L_KneeUpper", "R_KneeUpper", "L_ElbowUpper", "R_ElbowUpper", "SnapWeapon",
    "Backpack_Bot", "L_ShoulderPad"] if n in fb) or "无"))

P("")
P("=== [2] 骨骼关节间距（缩放不变量，最硬的结构判据）===")
P("  %-28s %14s %14s %12s" % ("pair", "GLB", "FBX", "相对差"))
worst_dist = 0.0
for k in sorted(G["dists"]):
    if k not in F["dists"]:
        P("  %-28s %14.6f %14s" % (k, G["dists"][k], "MISSING"))
        worst_dist = 1e9
        continue
    a, b = G["dists"][k], F["dists"][k]
    rel = abs(a - b) / a if a else 0.0
    worst_dist = max(worst_dist, rel)
    P("  %-28s %14.6f %14.6f %11.3e" % (k, a, b, rel))
P("  最大相对差 = %.3e   %s" % (worst_dist, "PASS" if worst_dist < 1e-4 else "FAIL (< 1e-4)"))

P("")
P("=== [3] 每个动画的帧数 ===")
ga, fa = G["anims"], F["anims"]
allnames = sorted(set(list(ga.keys()) + list(fa.keys())))
P("  %-44s %8s %8s %8s" % ("action", "GLB帧", "FBX帧", "帧差"))
nframe_bad = []
for nm in allnames:
    g = ga.get(nm)
    f = fa.get(nm)
    gf = g["frames"] if g else -1
    ff = f["frames"] if f else -1
    if gf != ff:
        nframe_bad.append(nm)
    P("  %-44s %8s %8s %8s" % (nm, gf, ff, ff - gf if (g and f) else "-"))
P("  帧数不一致的动画 = %d 个  %s" % (len(nframe_bad), nframe_bad[:8] if nframe_bad else "(全部一致)"))

P("")
P("=== [4] 代表动画的关节轨迹（按身高归一化后比对）===")
scale = G["height_raw"] / F["height_raw"] if F["height_raw"] else 1.0
P("  身高标尺：GLB=%.4f  FBX=%.4f  ⇒ FBX→GLB 缩放因子 = %.8f" % (
    G["height_raw"], F["height_raw"], scale))
P("  %-12s %-30s %14s" % ("probe", "matched action", "maxRelDev"))
worst_traj = 0.0
for key in PROBE_ACTS:
    gd = G["joint_anim"].get(key)
    fd = F["joint_anim"].get(key)
    if not gd or not fd:
        P("  %-12s %-30s %14s" % (key, (gd or {}).get("action", "NONE") if gd else "NONE",
                                  (fd or {}).get("action", "MISSING") if fd else "MISSING"))
        worst_traj = max(worst_traj, 1.0)
        continue
    mx = 0.0
    cnt = 0
    for jn in JOINTS:
        tg = gd["traj"].get(jn, [])
        tf = fd["traj"].get(jn, [])
        for i in range(min(len(tg), len(tf))):
            d = (tg[i] - tf[i] * scale).length
            mx = max(mx, d / G["height_raw"])
            cnt += 1
    worst_traj = max(worst_traj, mx)
    P("  %-12s %-30s %14.3e" % (key, gd["action"] + " | " + fd["action"], mx))

P("")
P("=== [5] 判据 ===")
P("  [2] 关节间距相对差   < 1e-4     实测 %.3e   %s" % (worst_dist, "PASS" if worst_dist < 1e-4 else "FAIL"))
P("  [3] 动画帧数全部一致            %s" % ("PASS" if not nframe_bad else "FAIL"))
P("  [4] 轨迹归一化偏差   < 3e-3     实测 %.3e   %s" % (
    worst_traj, "PASS" if worst_traj < 3e-3 else "FAIL"))
P("  (3e-3 相对身高 ≈ 5.7mm，仍远严于 G2 门禁的 1.5e-2)")
P("=== DONE ===")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("WROTE %s" % OUT)
