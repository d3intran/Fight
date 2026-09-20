# -*- coding: utf-8 -*-
"""对比两套骨架在动画下的**相对夹角**（与骨架朝向约定、比例无关）。

用法: blender -b -P <本脚本> -- <FBX> <标签>

指标（逐帧，输出均值/极值/帧幅）：
    躯干倾角  = angle(pelvis->head, +Z)
    左臂-躯干 = angle(upperarm_l->hand_l, pelvis->head)
    右臂-躯干 = angle(upperarm_r->hand_r, pelvis->head)
    左腿-垂直 = angle(thigh_l->foot_l, +Z)
    右腿-垂直 = angle(thigh_r->foot_r, +Z)

帧幅（max-min）用于判断该段「有没有在动」：帧幅≈0 ⇒ 被锁死。
"""
import bpy
import sys
import math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, LABEL = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]


def pick(*names):
    for n in names:
        if n in arm.pose.bones:
            return n
    raise SystemExit("!! 缺骨: %s" % (names,))


B = {
    "pelvis": pick("pelvis", "mixamorig:Hips"),
    "head": pick("head", "mixamorig:Head"),
    "ua_l": pick("upperarm_l", "mixamorig:LeftArm"),
    "hd_l": pick("hand_l", "mixamorig:LeftHand"),
    "ua_r": pick("upperarm_r", "mixamorig:RightArm"),
    "hd_r": pick("hand_r", "mixamorig:RightHand"),
    "th_l": pick("thigh_l", "mixamorig:LeftUpLeg"),
    "ft_l": pick("foot_l", "mixamorig:LeftFoot"),
    "th_r": pick("thigh_r", "mixamorig:RightUpLeg"),
    "ft_r": pick("foot_r", "mixamorig:RightFoot"),
}


def wp(n):
    return arm.matrix_world @ arm.pose.bones[n].head


def ang(u, v):
    if u.length < 1e-9 or v.length < 1e-9:
        return None
    return math.degrees(u.angle(v))


act = arm.animation_data.action if (arm.animation_data and arm.animation_data.action) else None
if act is None:
    print("%s !! 无动作" % LABEL)
    sys.exit(1)
f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
sc = bpy.context.scene
UP = Vector((0.0, 0.0, 1.0))
rows = []
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    trunk = wp(B["head"]) - wp(B["pelvis"])
    rows.append(dict(
        trunk=ang(trunk, UP),
        armL=ang(wp(B["hd_l"]) - wp(B["ua_l"]), trunk),
        armR=ang(wp(B["hd_r"]) - wp(B["ua_r"]), trunk),
        legL=ang(wp(B["ft_l"]) - wp(B["th_l"]), UP),
        legR=ang(wp(B["ft_r"]) - wp(B["th_r"]), UP),
    ))

KEYS = [("trunk", "躯干倾角"), ("armL", "左臂-躯干"), ("armR", "右臂-躯干"),
        ("legL", "左腿-垂直"), ("legR", "右腿-垂直")]
print("=== %s（帧 %d..%d）===" % (LABEL, f0, f1))
for k, name in KEYS:
    vals = [r[k] for r in rows if r[k] is not None]
    if not vals:
        continue
    print("   %-10s 均值=%5.1f  最小=%5.1f  最大=%5.1f  帧幅=%5.1f"
          % (name, sum(vals) / len(vals), min(vals), max(vals), max(vals) - min(vals)))
