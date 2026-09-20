"""
诊断：源骨架(glTF)的 bone.matrix_local 朝向 是否等于「关节->子关节」的真实几何方向？
     如果不等，说明 Blender glTF 导入对骨骼朝向的推算不可靠，
     而我的重定向公式 D = W_pose @ matrix_local^-1 会被污染 -> 系统性角度偏斜。
"""
import bpy, sys, math
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
SRC_GLB, TGT_FBX = argv[0], argv[1]

def imp(p, kind):
    before = set(bpy.data.objects)
    if kind == "fbx":
        bpy.ops.import_scene.fbx(filepath=p, automatic_bone_orientation=True)
    else:
        bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    return [o for o in new if o.type == 'ARMATURE'][0]

bpy.ops.wm.read_factory_settings(use_empty=True)
src = imp(SRC_GLB, "glb")
tgt = imp(TGT_FBX, "fbx")

# 只看父子链上的骨骼对
CHAINS = [
    ("Root", "Pelvis"), ("Pelvis", "L_Hip"), ("Pelvis", "R_Hip"),
    ("L_Hip", "L_KneeUpper"), ("L_KneeUpper", "L_KneeLower"), ("L_KneeLower", "L_Foot"),
    ("R_Hip", "R_KneeUpper"), ("R_KneeUpper", "R_KneeLower"), ("R_KneeLower", "R_Foot"),
    ("Spine1", "Spine2"), ("Spine2", "Neck"), ("Neck", "Head"),
    ("L_Clavicle", "L_Shoulder"), ("L_Shoulder", "L_ElbowUpper"), ("L_ElbowUpper", "L_Elbow"), ("L_Elbow", "L_Hand"),
    ("R_Clavicle", "R_Shoulder"), ("R_Shoulder", "R_ElbowUpper"), ("R_ElbowUpper", "R_Elbow"), ("R_Elbow", "R_Hand"),
]
CHAINS_T = [
    ("root", "pelvis"), ("pelvis", "thigh_l"), ("pelvis", "thigh_r"),
    ("thigh_l", "calf_l"), ("calf_l", "foot_l"), ("foot_l", "ball_l"),
    ("thigh_r", "calf_r"), ("calf_r", "foot_r"), ("foot_r", "ball_r"),
    ("spine_01", "spine_02"), ("spine_02", "spine_03"), ("spine_03", "neck_01"),
    ("clavicle_l", "upperarm_l"), ("upperarm_l", "lowerarm_l"), ("lowerarm_l", "hand_l"),
    ("clavicle_r", "upperarm_r"), ("upperarm_r", "lowerarm_r"), ("lowerarm_r", "hand_r"),
]

def report(arm, chains, label):
    print("=" * 96)
    print(f"【{label}】 骨骼朝向自检：bone.matrix_local 的 Y 轴(Blender 骨骼朝向) vs 关节->子关节几何方向")
    print("=" * 96)
    print(f"{'bone':26s} {'parent':22s} {'Y轴(矩阵)方向':>26s} {'几何方向':>26s} {'夹角':>8s}")
    print("-" * 96)
    errs = []
    for a, b in chains:
        ba = arm.data.bones.get(a); bb = arm.data.bones.get(b)
        if not ba or not bb:
            print(f"{a:26s} {'<缺失>':22s}")
            continue
        yaxis = (ba.matrix_local.to_3x3() @ Vector((0, 1, 0))).normalized()
        geo = (bb.head_local - ba.head_local)
        if geo.length < 1e-6:
            print(f"{a:26s} {b:22s}   <退化: 子关节与父关节重合>")
            continue
        geo = geo.normalized()
        ang = math.degrees(math.acos(max(-1.0, min(1.0, yaxis.dot(geo)))))
        errs.append(ang)
        flag = "一致" if ang < 10 else ("不一致!" if ang < 60 else "完全不同!!")
        print(f"{a:26s} {b:22s} ({yaxis.x:6.2f},{yaxis.y:6.2f},{yaxis.z:6.2f})  "
              f"({geo.x:6.2f},{geo.y:6.2f},{geo.z:6.2f})  {ang:6.1f}°  {flag}")
    if errs:
        print("-" * 96)
        print(f"  平均 {sum(errs)/len(errs):.1f}°  中位 {sorted(errs)[len(errs)//2]:.1f}°  最大 {max(errs):.1f}°")
    print()

report(src, CHAINS, "源 LOL (glTF 导入)")
report(tgt, CHAINS_T, "目标 2XKO (FBX 导入)")

# 附加：打印源骨架几个关键骨骼的 matrix_local 与几何朝向完整对比
print("=" * 96)
print("源骨架 Root / Pelvis 关节坐标（用于核对 Root->Pelvis 175.8° 的异常）")
print("=" * 96)
for n in ["Root", "Pelvis", "L_Hip", "R_Hip", "Spine1"]:
    b = src.data.bones.get(n)
    if b:
        print(f"   {n:10s} head_local=({b.head_local.x:8.3f},{b.head_local.y:8.3f},{b.head_local.z:8.3f})  "
              f"tail_local=({b.tail_local.x:8.3f},{b.tail_local.y:8.3f},{b.tail_local.z:8.3f})")
print()
print("目标骨架 root / pelvis")
for n in ["root", "pelvis", "thigh_l", "thigh_r", "spine_01"]:
    b = tgt.data.bones.get(n)
    if b:
        print(f"   {n:10s} head_local=({b.head_local.x:8.3f},{b.head_local.y:8.3f},{b.head_local.z:8.3f})  "
              f"tail_local=({b.tail_local.x:8.3f},{b.tail_local.y:8.3f},{b.tail_local.z:8.3f})")
print("=== DONE ===")
