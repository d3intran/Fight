"""
===============================================================================
 重定向保真度验证器 v2 (blender_42_fidelity.py)
 -------------------------------------------------------------------------------
 核心指标（与静止姿态无关，与骨骼朝向矩阵无关，纯粹基于关节几何）：
   对每根骨骼 b 及其映射子骨骼 c：
     u = normalize(rest(c) - rest(b))        # 静止姿态下的骨骼方向
     v = normalize(pose(c) - pose(b))        # 动画姿态下的骨骼方向
     Swing = 从 u 转到 v 的最小旋转（四元数）
   保真条件：Swing_target ≈ Q · Swing_source · Q⁻¹
   误差 = 两个四元数之间的夹角（0° = 完美，>20° = 有问题）

 用法:
   blender -b -P blender_42_fidelity.py -- <SRC_GLB> <TGT_FBX> <RETARGET_FBX> <ANIM_NAME> [max_frames]
===============================================================================
"""
import bpy, sys, math
from mathutils import Vector, Matrix, Quaternion

argv = sys.argv[sys.argv.index("--") + 1:]
SRC_GLB, TGT_FBX, RT_FBX = argv[0], argv[1], argv[2]
ANIM = argv[3] if len(argv) > 3 else "run"
MAXF = int(argv[4]) if len(argv) > 4 else 0

def imp(p, kind):
    before = set(bpy.data.objects)
    if kind == "fbx":
        bpy.ops.import_scene.fbx(filepath=p, automatic_bone_orientation=True)
    else:
        bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    return [o for o in new if o.type == 'ARMATURE'][0]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
tgt = imp(TGT_FBX, "fbx"); src = imp(SRC_GLB, "glb"); rt = imp(RT_FBX, "fbx")

# 映射对：源(父,子) -> 目标(父,子)，父子都必须有映射，方向才非退化
PAIRS = [
    ("Pelvis", "L_Hip", "pelvis", "thigh_l"),
    ("Pelvis", "R_Hip", "pelvis", "thigh_r"),
    ("L_Hip", "L_KneeLower", "thigh_l", "calf_l"),
    ("L_KneeLower", "L_Foot", "calf_l", "foot_l"),
    ("R_Hip", "R_KneeLower", "thigh_r", "calf_r"),
    ("R_KneeLower", "R_Foot", "calf_r", "foot_r"),
    ("Spine1", "Spine2", "spine_01", "spine_02"),
    ("Spine2", "Neck", "spine_02", "spine_03"),
    ("Neck", "Head", "neck_01", "head"),
    ("L_Clavicle", "L_Shoulder", "clavicle_l", "upperarm_l"),
    ("L_Shoulder", "L_Elbow", "upperarm_l", "lowerarm_l"),
    ("L_Elbow", "L_Hand", "lowerarm_l", "hand_l"),
    ("R_Clavicle", "R_Shoulder", "clavicle_r", "upperarm_r"),
    ("R_Shoulder", "R_Elbow", "upperarm_r", "lowerarm_r"),
    ("R_Elbow", "R_Hand", "lowerarm_r", "hand_r"),
]

def rest_basis(arm, l, r):
    L = arm.matrix_world @ arm.data.bones[l].head_local
    R = arm.matrix_world @ arm.data.bones[r].head_local
    v = R - L; v.z = 0.0
    if v.length < 1e-6: v = Vector((1, 0, 0))
    v.normalize()
    up = Vector((0, 0, 1))
    return Matrix((v, up.cross(v), up)).transposed()

Q = rest_basis(tgt, "thigh_l", "thigh_r") @ rest_basis(src, "L_Hip", "R_Hip").inverted()
Qq = Q.to_quaternion()
Qq_inv = Qq.inverted()
print("Q =", round(math.degrees(Q.to_euler().z), 2), "deg about Z")

def jp(arm, n, rest=False):
    if rest:
        b = arm.data.bones.get(n)
        return arm.matrix_world @ b.head_local if b else None
    pb = arm.pose.bones.get(n)
    return (arm.matrix_world @ pb.matrix).translation if pb else None

def swing(arm, a, b, rest):
    pa, pb_ = jp(arm, a, rest), jp(arm, b, rest)
    if pa is None or pb_ is None: return None
    d = pb_ - pa
    if d.length < 1e-6: return None
    return d.normalized()

def swing_quat(u, v):
    return u.rotation_difference(v)   # 最小弧旋转四元数

# 源动作
src_act = None
for a in bpy.data.actions:
    if a.name == ANIM or a.name.endswith("_" + ANIM) or a.name.endswith(ANIM):
        src_act = a
if src_act is None:
    print("!! 找不到动作", ANIM); raise SystemExit
src.animation_data.action = src_act
F0, F1 = int(src_act.frame_range[0]), int(src_act.frame_range[1])
if MAXF: F1 = min(F1, F0 + MAXF)
print(f"源动作 {src_act.name}  frames {F0}~{F1}")

print()
print("=" * 100)
print(f"【保真度】Swing 误差 = angle( Q·Swing_src·Q⁻¹ , Swing_tgt )   0°=完美   {ANIM}")
print("=" * 100)
print(f"{'骨骼（源->目标）':40s} {'均值':>7s} {'最大':>7s} {'P90':>7s}  判定")
print("-" * 100)
per = {}
for f in range(F0, F1 + 1):
    sc.frame_set(f); bpy.context.view_layer.update()
    for sa, sb, ta, tb in PAIRS:
        ur = swing(src, sa, sb, True); vr = swing(src, sa, sb, False)
        ut = swing(rt, ta, tb, True); vt = swing(rt, ta, tb, False)
        if None in (ur, vr, ut, vt): continue
        qs = swing_quat(ur, vr)
        qt = swing_quat(ut, vt)
        exp = Qq @ qs @ Qq_inv
        dot = abs(max(-1.0, min(1.0, exp.dot(qt))))
        ang = math.degrees(2.0 * math.acos(dot))
        per.setdefault((sa, sb, ta, tb), []).append(ang)

allv = []
for k, v in per.items():
    sa, sb, ta, tb = k
    v2 = sorted(v); mean = sum(v2) / len(v2)
    p90 = v2[min(len(v2)-1, int(0.9*(len(v2)-1)))]
    allv.extend(v2)
    flag = "完美" if mean < 5 else ("良好" if mean < 12 else ("可接受" if mean < 20 else "有问题!"))
    print(f"{sa+' -> '+sb+'  ==>  '+ta+' -> '+tb:40s} {mean:6.1f}° {v2[-1]:6.1f}° {p90:6.1f}°  {flag}")
print("-" * 100)
allv.sort()
print(f"全部 {len(allv)} 样本：均值 {sum(allv)/len(allv):.1f}°  中位 {allv[len(allv)//2]:.1f}°  "
      f"P90 {allv[int(0.9*(len(allv)-1))]:.1f}°  最大 {allv[-1]:.1f}°")
print("=== DONE ===")
