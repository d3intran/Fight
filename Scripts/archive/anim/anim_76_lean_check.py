# -*- coding: utf-8 -*-
"""量躯干前倾角：逐帧计算 (head - pelvis) 向量相对垂直轴的夹角。

用于区分「前倾来自动画本身」还是「绑定时引入」：
    blender -b -P <本脚本> -- <FBX> <标签>
两套骨架自动选骨名（UE Mannequin / Mixamo mixamorig）。
"""
import bpy
import sys
import math

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, LABEL = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]


def first(*names):
    for n in names:
        if n in arm.pose.bones:
            return n
    return None


hip = first("pelvis", "mixamorig:Hips", "Hips")
head = first("head", "mixamorig:Head", "Head")
if hip is None or head is None:
    print("%s !! 找不到 pelvis/head（hip=%s head=%s）" % (LABEL, hip, head))
    sys.exit(1)
print("%s  骨: hip=%s head=%s" % (LABEL, hip, head))

act = arm.animation_data.action if (arm.animation_data and arm.animation_data.action) else None
if act is None:
    print("%s !! 无动作" % LABEL)
    sys.exit(1)

f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
sc = bpy.context.scene
angles = []
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    p = arm.matrix_world @ arm.pose.bones[hip].head
    h = arm.matrix_world @ arm.pose.bones[head].head
    v = h - p
    if v.length < 1e-6:
        continue
    v.normalize()
    angles.append(math.degrees(math.acos(max(-1.0, min(1.0, v.z)))))

print("%s  躯干前倾角（相对垂直）: 均值=%.1f°  最小=%.1f°  最大=%.1f°  帧=%d"
      % (LABEL, sum(angles) / len(angles), min(angles), max(angles), len(angles)))
