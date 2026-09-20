"""
逐关节「弯曲角」审计：源 vs 重定向结果，精确定位偏差来自哪个关节
弯曲角 = 该骨骼方向相对其静止方向的夹角（与骨骼朝向矩阵无关，纯几何）
"""
import bpy, sys, math
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
SRC_GLB, TGT_FBX, RT_FBX, ANIM = argv[0], argv[1], argv[2], argv[3]

def imp(p, k):
    before = set(bpy.data.objects)
    if k == "fbx": bpy.ops.import_scene.fbx(filepath=p, automatic_bone_orientation=True)
    else: bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    return [o for o in new if o.type == 'ARMATURE'][0]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = 30
src = imp(SRC_GLB, "glb"); tgt = imp(TGT_FBX, "fbx"); rt = imp(RT_FBX, "fbx")
names = {src.animation_data.action.name} if (src.animation_data and src.animation_data.action) else set()
cand = [a for a in bpy.data.actions if a.name not in names]
if cand and rt.animation_data: rt.animation_data.action = cand[-1]

# 链：源(self,child) -> 目标(self,child)
CH = [
    ("L_Hip", "L_KneeUpper", "thigh_l", "calf_l", "左大腿"),
    ("L_KneeLower", "L_Foot", "calf_l", "foot_l", "左小腿"),
    ("R_Hip", "R_KneeUpper", "thigh_r", "calf_r", "右大腿"),
    ("R_KneeLower", "R_Foot", "calf_r", "foot_r", "右小腿"),
    ("Spine1", "Spine2", "spine_01", "spine_02", "下脊椎"),
    ("Spine2", "Neck", "spine_02", "spine_03", "上脊椎"),
    ("Neck", "Head", "neck_01", "head", "颈头"),
    ("L_Shoulder", "L_ElbowUpper", "upperarm_l", "lowerarm_l", "左上臂"),
    ("L_Elbow", "L_Hand", "lowerarm_l", "hand_l", "左前臂"),
    ("R_Shoulder", "R_ElbowUpper", "upperarm_r", "lowerarm_r", "右上臂"),
    ("R_Elbow", "R_Hand", "lowerarm_r", "hand_r", "右前臂"),
]

def P(arm, n, rest):
    if rest:
        b = arm.data.bones.get(n)
        return (arm.matrix_world @ b.head_local) if b else None
    pb = arm.pose.bones.get(n)
    return (arm.matrix_world @ pb.matrix).translation if pb else None

def d(arm, a, b, rest):
    pa, pb_ = P(arm, a, rest), P(arm, b, rest)
    if pa is None or pb_ is None: return None
    v = pb_ - pa
    return v.normalized() if v.length > 1e-6 else None

print("=" * 118)
print("【静止姿态几何自检】源与目标的骨骼方向（关节->子关节）")
print("=" * 118)
print(f"{'链':10s} {'源方向':>26s} {'目标方向':>26s} {'静止夹角':>9s}  源骨长    目标骨长")
print("-" * 118)
for sa, sb, ta, tb, lbl in CH:
    us, ut = d(src, sa, sb, True), d(tgt, ta, tb, True)
    ls = ((P(src, sb, True) - P(src, sa, True)).length) if P(src, sb, True) else 0
    lt = ((P(tgt, tb, True) - P(tgt, ta, True)).length) if P(tgt, tb, True) else 0
    if us is None or ut is None:
        print(f"{lbl:10s} <退化/缺失>"); continue
    ang = math.degrees(math.acos(max(-1, min(1, us.dot(ut)))))
    print(f"{lbl:10s} ({us.x:6.2f},{us.y:6.2f},{us.z:6.2f})  ({ut.x:6.2f},{ut.y:6.2f},{ut.z:6.2f})  {ang:8.1f}°  {ls:8.2f}  {lt:8.3f}")

print()
print("=" * 118)
print(f"【逐帧弯曲角】源 vs 目标（{ANIM}）  单位：度   Δ=目标-源")
print("=" * 118)
src_act = None
for a in bpy.data.actions:
    if a.name == ANIM or a.name.endswith("_"+ANIM) or a.name.endswith(ANIM): src_act = a
if src_act: src.animation_data.action = src_act
F0, F1 = (int(src_act.frame_range[0]), int(src_act.frame_range[1])) if src_act else (0, 28)
rt_act = rt.animation_data.action if rt.animation_data else None
rtF0 = int(rt_act.frame_range[0]) if rt_act else 1
print(f"源帧 {F0}~{F1}   重定向帧 {rt_act.frame_range if rt_act else None}")
hdr = f"{'帧':>4s} " + " ".join([f"{lbl:>14s}" for _,_,_,_,lbl in CH])
print(hdr)
for f in range(F0, min(F1, F0+28) + 1):
    sc.frame_set(f); bpy.context.view_layer.update()
    sc.frame_set(rtF0 + (f - F0)); bpy.context.view_layer.update()
    row = f"{f:4d} "
    for sa, sb, ta, tb, lbl in CH:
        us, ut = d(src, sa, sb, True), d(tgt, ta, tb, True)
        vs, vt = d(src, sa, sb, False), d(rt, ta, tb, False)
        if None in (us, ut, vs, vt):
            row += f"{'--':>15s}"; continue
        bs = math.degrees(math.acos(max(-1, min(1, us.dot(vs)))))
        bt = math.degrees(math.acos(max(-1, min(1, ut.dot(vt)))))
        row += f"{bs:6.0f}/{bt:<4.0f}({bt-bs:+4.0f})"
    print(row)
print("=== DONE ===")
