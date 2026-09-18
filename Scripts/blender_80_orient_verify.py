"""
绝对朝向误差验证：angle( Q·源骨方向 , 目标骨方向 )   0° = 两者朝向完全一致
这是「看起来一样吗」的客观标准，与各自的静止姿态无关。
用法: blender -b -P blender_80_orient_verify.py -- <SRC_GLB> <TGT_FBX> <RT_FBX> <ANIM>
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
sn = {src.animation_data.action.name} if (src.animation_data and src.animation_data.action) else set()
cand = [a for a in bpy.data.actions if a.name not in sn]
if cand and rt.animation_data: rt.animation_data.action = cand[-1]

# 源(self,child) -> 目标(self,child)
CH = [
    ("L_Hip", "L_KneeUpper", "thigh_l", "calf_l", "左大腿"),
    ("L_KneeLower", "L_Foot", "calf_l", "foot_l", "左小腿"),
    ("R_Hip", "R_KneeUpper", "thigh_r", "calf_r", "右大腿"),
    ("R_KneeLower", "R_Foot", "calf_r", "foot_r", "右小腿"),
    ("Spine1", "Spine2", "spine_01", "spine_02", "下脊椎"),
    ("Spine2", "Neck", "spine_02", "spine_03", "上脊椎"),
    ("Neck", "Head", "neck_01", "head", "颈头"),
    ("L_Clavicle", "L_Shoulder", "clavicle_l", "upperarm_l", "左锁骨"),
    ("L_Shoulder", "L_ElbowUpper", "upperarm_l", "lowerarm_l", "左上臂"),
    ("L_Elbow", "L_Hand", "lowerarm_l", "hand_l", "左前臂"),
    ("R_Clavicle", "R_Shoulder", "clavicle_r", "upperarm_r", "右锁骨"),
    ("R_Shoulder", "R_ElbowUpper", "upperarm_r", "lowerarm_r", "右上臂"),
    ("R_Elbow", "R_Hand", "lowerarm_r", "hand_r", "右前臂"),
    ("Pelvis", "L_Hip", "pelvis", "thigh_l", "骨盆-左胯"),
]
def rest_basis(arm, l, r):
    L = arm.matrix_world @ arm.data.bones[l].head_local
    R = arm.matrix_world @ arm.data.bones[r].head_local
    v = R - L; v.z = 0.0
    if v.length < 1e-6: v = Vector((1,0,0))
    v.normalize(); up = Vector((0,0,1))
    return Matrix((v, up.cross(v), up)).transposed()
Q = rest_basis(tgt, "thigh_l", "thigh_r") @ rest_basis(src, "L_Hip", "R_Hip").inverted()

def P(arm, n, rest):
    if rest:
        b = arm.data.bones.get(n)
        return (arm.matrix_world @ b.head_local) if b else None
    pb = arm.pose.bones.get(n)
    return (arm.matrix_world @ pb.matrix).translation if pb else None
def D(arm, a, b, rest):
    pa, pb_ = P(arm, a, rest), P(arm, b, rest)
    if pa is None or pb_ is None: return None
    v = pb_ - pa
    return v.normalized() if v.length > 1e-6 else None

sact = None
for a in bpy.data.actions:
    if a.name == ANIM or a.name.endswith("_"+ANIM) or a.name.endswith(ANIM): sact = a
if sact: src.animation_data.action = sact
F0, F1 = int(sact.frame_range[0]), int(sact.frame_range[1])
ract = rt.animation_data.action if rt.animation_data else None
rF0 = int(ract.frame_range[0]) if ract else 1

# ⚠️ 必须分开采样：frame_set 会同时求值场景内所有对象，
#    若连续两次 frame_set 后再读两边数据，源骨架会被求值到目标帧上，产生 1 帧相位差
per = {}
for f in range(F0, F1 + 1):
    sc.frame_set(f); bpy.context.view_layer.update()
    src_dirs = {}
    for sa, sb, ta, tb, lbl in CH:
        src_dirs[lbl] = D(src, sa, sb, False)
    sc.frame_set(rF0 + (f - F0)); bpy.context.view_layer.update()
    for sa, sb, ta, tb, lbl in CH:
        us, ut = src_dirs.get(lbl), D(rt, ta, tb, False)
        if us is None or ut is None: continue
        e = (Q @ us).normalized()
        per.setdefault(lbl, []).append(math.degrees(math.acos(max(-1, min(1, e.dot(ut))))))

print("=" * 84)
print(f"【绝对朝向误差】angle(Q·源骨方向, 目标骨方向)   {ANIM}   0°=完全一致")
print("=" * 84)
print(f"{'关节':12s} {'均值':>8s} {'最大':>8s} {'P90':>8s}   判定")
print("-" * 84)
allv = []
for lbl, v in per.items():
    v2 = sorted(v); mean = sum(v2)/len(v2)
    p90 = v2[min(len(v2)-1, int(0.9*(len(v2)-1)))]
    allv.extend(v2)
    fl = "优秀" if mean < 8 else ("良好" if mean < 15 else ("可接受" if mean < 25 else "偏大!"))
    print(f"{lbl:12s} {mean:7.1f}° {v2[-1]:7.1f}° {p90:7.1f}°   {fl}")
print("-" * 84)
allv.sort()
print(f"全部 {len(allv)} 样本：均值 {sum(allv)/len(allv):.1f}°  中位 {allv[len(allv)//2]:.1f}°  "
      f"P90 {allv[int(0.9*(len(allv)-1))]:.1f}°  最大 {allv[-1]:.1f}°")
print("=== DONE ===")
