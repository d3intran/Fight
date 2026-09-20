# -*- coding: utf-8 -*-
"""
plan_16_audit_fbx.py —— 扫描一批 FBX 的 bind pose 是否正确

判据：与参考骨架（同一套目标骨架、无动画的干净导出）比对**关节间距**。
间距是缩放不变量，免疫单位换算与骨骼朝向约定差异 —— 若某文件的 bind pose 被
「导出时的当前 pose」污染，间距会整体偏移，且偏差随骨链累积放大。

用法:
  blender -b -P Scripts/retarget/plan_16_audit_fbx.py -- <REF_FBX> <OUT_TXT> <DIR1;DIR2;...>

参考骨架建议用 `Saved/Retarget/SK_Darius_GodKing_Clean.fbx`（bake_anim=False 产出，无 pose 污染）。
"""
import bpy
import sys
import os
import glob

argv = sys.argv[sys.argv.index("--") + 1:]
REF_FBX = argv[0]
OUT = argv[1]
DIRS = argv[2].split(";") if len(argv) > 2 else []

lines = []


def P(s=""):
    lines.append(str(s))


# 目标骨架（UE Mannequin 命名）的关节与间距对
JOINTS = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head",
          "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l",
          "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r",
          "thigh_l", "calf_l", "foot_l", "ball_l",
          "thigh_r", "calf_r", "foot_r", "ball_r"]
PAIRS = [
    ("thigh_l", "calf_l"), ("calf_l", "foot_l"), ("foot_l", "ball_l"),
    ("thigh_l", "thigh_r"), ("pelvis", "head"),
    ("clavicle_l", "upperarm_l"), ("upperarm_l", "lowerarm_l"), ("lowerarm_l", "hand_l"),
    ("clavicle_l", "clavicle_r"),
]


def load_heads(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = 30
    bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=False)
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    if not arms:
        return None, 0
    arm = arms[0]
    mw = arm.matrix_world
    heads = {}
    for b in arm.data.bones:
        heads[b.name] = (mw @ b.head_local).copy()
    return heads, len(arm.data.bones)


P("=" * 100)
P("### plan_16 —— FBX bind pose 审计")
P("=" * 100)
P("REF = %s" % REF_FBX)

ref, refn = load_heads(REF_FBX)
if ref is None:
    raise SystemExit("参考骨架载入失败")
P("参考骨架骨数 = %d" % refn)

ref_dist = {}
for a, b in PAIRS:
    if a in ref and b in ref:
        ref_dist["%s-%s" % (a, b)] = (ref[a] - ref[b]).length
P("参考间距对 = %d 个" % len(ref_dist))

targets = []
for d in DIRS:
    if d and os.path.isdir(d):
        targets += sorted(glob.glob(os.path.join(d, "*.fbx")))
P("待检文件 = %d 个" % len(targets))

P("")
P("  %-46s %7s %12s %12s %s" % ("file", "bones", "maxRelDev", "meanRelDev", "verdict"))
summary = []
for t in targets:
    try:
        heads, nb = load_heads(t)
    except Exception as ex:
        P("  %-46s  <导入失败: %s>" % (os.path.basename(t), ex))
        continue
    if heads is None:
        P("  %-46s  <无骨架>" % os.path.basename(t))
        continue
    devs = []
    for k, d0 in ref_dist.items():
        a, b = k.split("-")
        if a in heads and b in heads:
            d1 = (heads[a] - heads[b]).length
            if d0 > 1e-6:
                devs.append(abs(d1 - d0) / d0)
    if not devs:
        P("  %-46s %7d  <无可用间距对>" % (os.path.basename(t), nb))
        continue
    mx = max(devs)
    mn = sum(devs) / len(devs)
    verdict = "OK" if mx < 1e-3 else ("WARN" if mx < 1e-2 else "**BROKEN**")
    P("  %-46s %7d %12.3e %12.3e %s" % (os.path.basename(t), nb, mx, mn, verdict))
    summary.append((mx, t, verdict))

P("")
P("=== 汇总 ===")
if summary:
    summary.sort(reverse=True)
    P("  最差 5 个:")
    for mx, t, v in summary[:5]:
        P("     %.3e  %s  %s" % (mx, v, os.path.basename(t)))
    broken = [t for mx, t, v in summary if v == "**BROKEN**"]
    P("  判定 BROKEN（相对偏差 > 1%%）的文件数 = %d / %d" % (len(broken), len(summary)))
else:
    P("  无有效样本")

P("")
P("判据：bind pose 正确时，同一套骨架的不同 FBX 的关节间距应几乎完全一致（< 1e-3）。")
P("      若被「导出时的当前 pose」污染，间距会整体偏移，偏差随骨链累积放大。")
P("=== DONE ===")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("WROTE %s" % OUT)
