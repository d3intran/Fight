"""数值校验：对比源/目标骨架在关键链上的「世界朝向」是否一致"""
import bpy, sys
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, TGT, RT = argv[0], argv[1], argv[2]

bpy.ops.wm.read_factory_settings(use_empty=True)

def imp(path, kind):
    before = set(bpy.data.objects)
    if kind == "fbx":
        bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=True)
    else:
        bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    return [o for o in new if o.type == 'ARMATURE'][0]

tgt = imp(TGT, "fbx")
print("tgt:", tgt.name, len(tgt.data.bones))
src = imp(SRC, "glb")
print("src:", src.name, len(src.data.bones))
rt = imp(RT, "fbx")
print("rt:", rt.name, len(rt.data.bones))

sc = bpy.context.scene
if rt.animation_data and rt.animation_data.action:
    a = rt.animation_data.action
    print("rt action:", a.name, a.frame_range)

# 用「父关节->子关节」的向量方向做对比（不依赖骨骼 tail 猜测）
SRC_CHAINS = [("Pelvis", "L_Hip"), ("L_Hip", "L_KneeUpper"), ("L_KneeUpper", "L_KneeLower"),
              ("L_KneeLower", "L_Foot"), ("L_Clavicle", "L_Shoulder"), ("L_Shoulder", "L_ElbowUpper"),
              ("L_ElbowUpper", "L_Elbow"), ("L_Elbow", "L_Hand"),
              ("R_Hip", "R_KneeUpper"), ("R_KneeLower", "R_Foot"),
              ("Spine1", "Spine2"), ("Spine2", "Neck"), ("Neck", "Head")]
TGT_CHAINS = [("pelvis", "thigh_l"), ("thigh_l", "calf_l"), ("calf_l", "foot_l"), ("foot_l", "ball_l"),
              ("clavicle_l", "upperarm_l"), ("upperarm_l", "lowerarm_l"), ("lowerarm_l", "hand_l"),
              ("thigh_r", "calf_r"), ("calf_r", "foot_r"),
              ("spine_01", "spine_02"), ("spine_02", "spine_03"), ("neck_01", "head")]


def wpos(arm, name):
    pb = arm.pose.bones.get(name)
    return (arm.matrix_world @ pb.matrix).translation if pb else None


def dirs(arm, chains, scale=1.0):
    out = []
    for a, b in chains:
        pa, pb_ = wpos(arm, a), wpos(arm, b)
        if pa is None or pb_ is None:
            out.append(None)
            continue
        out.append(((pb_ - pa) * scale).normalized())
    return out


for f in [0, 7, 14, 21]:
    sc.frame_set(f)
    bpy.context.view_layer.update()
    ds = dirs(src, SRC_CHAINS, 1.0)
    dt = dirs(rt, TGT_CHAINS, 1.0)
    print(f"--- frame {f} ---")
    for (sa, sb), v1, v2 in zip(SRC_CHAINS, ds, dt):
        if v1 is None or v2 is None:
            print(f"   {sa}->{sb}: missing")
            continue
        dot = max(-1.0, min(1.0, v1.dot(v2)))
        import math
        ang = math.degrees(math.acos(dot))
        flag = "  <== 偏差大" if ang > 25 else ""
        print(f"   {sa:14s} src=({v1.x:6.2f},{v1.y:6.2f},{v1.z:6.2f})  tgt=({v2.x:6.2f},{v2.y:6.2f},{v2.z:6.2f})  Δ={ang:6.1f}°{flag}")
print("=== DONE ===")
