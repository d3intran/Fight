"""
===============================================================================
 重定向精度数值验证器 (blender_40_verify_retarget.py)
 -------------------------------------------------------------------------------
 目的：不靠肉眼，用关节坐标客观量化「源动画 vs 重定向后动画」的偏差。

 方法：
   1. 对每根「有映射子骨骼」的骨骼，取其自身关节 -> 映射子骨骼关节 的方向向量
      （关节坐标 = bone.head_local 经姿态变换后的世界坐标，两套骨架都精确可测，
        不依赖 glTF 导入时对 bone.tail 的猜测）
   2. 源方向经基准系对齐矩阵 Q 变换后，与目标方向比较夹角
   3. 同时报告：
      - 静止姿态(REST)下的方向偏差  -> 这就是「系统性偏斜」的度量
      - 动画各帧的方向偏差（均值/最大/分位）-> 这是「动态精度」
      - 关节位置的相对误差（排除整体尺度后）

 用法:
   blender -b -P blender_40_verify_retarget.py -- <SRC_GLB> <TGT_FBX_REST> <RETARGET_FBX> <ANIM_NAME> [max_frames]
===============================================================================
"""
import bpy, sys, math
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
SRC_GLB, TGT_FBX, RT_FBX = argv[0], argv[1], argv[2]
ANIM = argv[3] if len(argv) > 3 else "run"
MAXF = int(argv[4]) if len(argv) > 4 else 0

def imp(path, kind):
    before = set(bpy.data.objects)
    if kind == "fbx":
        bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=True)
    else:
        bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    return [o for o in new if o.type == 'ARMATURE'][0]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
tgt = imp(TGT_FBX, "fbx")
src = imp(SRC_GLB, "glb")
rt = imp(RT_FBX, "fbx")
print(f"tgt={tgt.name}({len(tgt.data.bones)}) src={src.name}({len(src.data.bones)}) rt={rt.name}({len(rt.data.bones)})")

# ---- 映射表：父->子 都是已映射的骨骼，才能得到非退化的方向 ----
PAIRS = [
    ("Root", "Pelvis", "root", "pelvis"),
    ("Pelvis", "L_Hip", "pelvis", "thigh_l"),
    ("Pelvis", "R_Hip", "pelvis", "thigh_r"),
    ("L_Hip", "L_KneeLower", "thigh_l", "calf_l"),
    ("L_KneeLower", "L_Foot", "calf_l", "foot_l"),
    ("L_Foot", "L_Toe", "foot_l", "toe_l"),
    ("R_Hip", "R_KneeLower", "thigh_r", "calf_r"),
    ("R_KneeLower", "R_Foot", "calf_r", "foot_r"),
    ("R_Foot", "R_Toe", "foot_r", "toe_r"),
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

def jpos(arm, name):
    pb = arm.pose.bones.get(name)
    if pb is None:
        return None
    return (arm.matrix_world @ pb.matrix).translation

def rest_jpos(arm, name):
    b = arm.data.bones.get(name)
    if b is None:
        return None
    return arm.matrix_world @ b.head_local

# ---- 空间对齐矩阵 Q（与重定向脚本同一套逻辑）----
def rest_basis(arm, l, r):
    L = arm.matrix_world @ arm.data.bones[l].head_local
    R = arm.matrix_world @ arm.data.bones[r].head_local
    v = R - L; v.z = 0.0
    if v.length < 1e-6: v = Vector((1, 0, 0))
    v.normalize()
    up = Vector((0, 0, 1))
    return Matrix((v, up.cross(v), up)).transposed()

Q = rest_basis(tgt, "thigh_l", "thigh_r") @ rest_basis(src, "L_Hip", "R_Hip").inverted()
print("Q(deg about Z) =", round(math.degrees(Q.to_euler().z), 3))

def dir_of(arm, a, b, rest=False):
    f = rest_jpos if rest else jpos
    pa, pb_ = f(arm, a), f(arm, b)
    if pa is None or pb_ is None:
        return None
    d = pb_ - pa
    if d.length < 1e-6:
        return None
    return d.normalized()

print()
print("=" * 104)
print("【A】静止姿态(REST)方向偏差 —— 这就是「系统性偏斜」的度量")
print("=" * 104)
print(f"{'源骨骼链':28s} {'目标骨骼链':28s} {'偏斜角':>9s}   判定")
print("-" * 104)
rest_err = {}
for sa, sb, ta, tb in PAIRS:
    d_s = dir_of(src, sa, sb, rest=True)
    d_t = dir_of(tgt, ta, tb, rest=True)
    if d_s is None or d_t is None:
        print(f"{sa+'->'+sb:28s} {ta+'->'+tb:28s}   <数据缺失>")
        continue
    exp = (Q @ d_s).normalized()
    ang = math.degrees(math.acos(max(-1.0, min(1.0, exp.dot(d_t)))))
    rest_err[(sa, sb, ta, tb)] = ang
    flag = "OK" if ang < 8 else ("偏斜!" if ang < 25 else "严重偏斜!!")
    print(f"{sa+'->'+sb:28s} {ta+'->'+tb:28s} {ang:8.1f}°   {flag}")
if rest_err:
    vals = sorted(rest_err.values())
    print("-" * 104)
    print(f"静止偏斜：均值 {sum(vals)/len(vals):.1f}°  中位 {vals[len(vals)//2]:.1f}°  最大 {vals[-1]:.1f}°")

# ---- 动画逐帧 ----
src_act = None
for a in bpy.data.actions:
    if a.name == ANIM or a.name.endswith("_" + ANIM) or a.name.endswith(ANIM):
        src_act = a
if src_act is None:
    print("!! 找不到源动作", ANIM); raise SystemExit
src.animation_data.action = src_act
rt_act = rt.animation_data.action if (rt.animation_data and rt.animation_data.action) else None
print()
print(f"源动作 {src_act.name} frames {src_act.frame_range} | 重定向动作 {rt_act.name if rt_act else None} frames {rt_act.frame_range if rt_act else None}")

F0, F1 = int(src_act.frame_range[0]), int(src_act.frame_range[1])
if MAXF:
    F1 = min(F1, F0 + MAXF)

print()
print("=" * 104)
print(f"【B】动画逐帧方向偏差（{ANIM}）")
print("=" * 104)
print(f"{'骨骼链':30s} {'均值':>7s} {'最大':>7s} {'P90':>7s}   与静止偏斜对比")
print("-" * 104)
per_bone = {}
for f in range(F0, F1 + 1):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    for sa, sb, ta, tb in PAIRS:
        d_s = dir_of(src, sa, sb)
        d_t = dir_of(rt, ta, tb)
        if d_s is None or d_t is None:
            continue
        exp = (Q @ d_s).normalized()
        ang = math.degrees(math.acos(max(-1.0, min(1.0, exp.dot(d_t)))))
        per_bone.setdefault((sa, sb, ta, tb), []).append(ang)

all_vals = []
for k, v in per_bone.items():
    sa, sb, ta, tb = k
    v2 = sorted(v)
    mean = sum(v2) / len(v2)
    p90 = v2[min(len(v2) - 1, int(0.9 * (len(v2) - 1)))]
    all_vals.extend(v2)
    re_ = rest_err.get(k, float("nan"))
    delta = mean - re_
    print(f"{sa+'->'+sb:30s} {mean:6.1f}° {v2[-1]:6.1f}° {p90:6.1f}°   rest={re_:5.1f}°  动态-静止={delta:+6.1f}°")
print("-" * 104)
all_vals.sort()
print(f"全部样本 {len(all_vals)} 个：均值 {sum(all_vals)/len(all_vals):.1f}°  "
      f"中位 {all_vals[len(all_vals)//2]:.1f}°  P90 {all_vals[int(0.9*(len(all_vals)-1))]:.1f}°  最大 {all_vals[-1]:.1f}°")

print()
print("=" * 104)
print("【C】关键关节位置误差（源经 Q+缩放后 vs 目标，均以各自 root 为原点）")
print("=" * 104)
def headz(arm, n):
    b = arm.data.bones.get(n)
    return (arm.matrix_world @ b.head_local).z if b else None
src_h, tgt_h = headz(src, "Head"), headz(tgt, "head")
src_f = min(v for v in [headz(src, "L_Toe"), headz(src, "R_Toe")] if v is not None)
tgt_f = min(v for v in [headz(tgt, "toe_l"), headz(tgt, "toe_r")] if v is not None)
SCALE = (tgt_h - tgt_f) / (src_h - src_f)
print(f"SCALE = {SCALE:.6f}")
JOINTS = [("Pelvis", "pelvis"), ("L_Foot", "foot_l"), ("R_Foot", "foot_r"), ("Head", "head"),
          ("L_Hand", "hand_l"), ("R_Hand", "hand_r")]
for sa, ta in JOINTS:
    errs = []
    for f in range(F0, F1 + 1, max(1, (F1 - F0) // 8 or 1)):
        sc.frame_set(f); bpy.context.view_layer.update()
        ps, pt = jpos(src, sa), jpos(rt, ta)
        ps0, pt0 = jpos(src, "Root"), jpos(rt, "root")
        if None in (ps, pt, ps0, pt0):
            continue
        a = Q @ ((ps - ps0) * SCALE)
        b = (pt - pt0)
        errs.append((a - b).length)
    if errs:
        print(f"   {sa:10s} -> {ta:10s}  平均位置误差 {sum(errs)/len(errs):7.2f} cm   最大 {max(errs):7.2f} cm")
print("=== DONE ===")
