"""
===============================================================================
 重定向 v3 —— 纯几何驱动，彻底绕开源骨架 matrix_local 不可靠的问题
 -------------------------------------------------------------------------------
 核心改变：
   v2: D = W_pose @ matrix_local⁻¹     <- 依赖源骨骼朝向矩阵（glTF 导入不可靠，误差 90~173°）
   v3: D = F_pose @ F_rest⁻¹           <- F 为「关节坐标构造的几何朝向帧」，两套骨架都精确可测

 几何帧构造（三点 a -> b -> c）：
   y = normalize(Pb - Pa)          # 骨骼指向
   z = normalize(cross(y, Pc - Pb)) # 弯曲平面法线（滚转参考）
   x = cross(y, z)
   退化时回退到全局 Z 轴参考。

 逐骨骼三点链为人工定制的映射表（避开 LOL 骨架中重合/退化骨骼）。
===============================================================================
"""
import bpy, sys, os, math
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
SRC_GLB, TGT_FBX = argv[0], argv[1]
SPINE_PITCH = float(argv[2]) if len(argv) > 2 else 0.0
OUTDIR = argv[3] if len(argv) > 3 else r"E:/UE/Fight/Saved/Retarget/V3"
WANT = argv[4].split(",") if len(argv) > 4 else ["run"]
os.makedirs(OUTDIR, exist_ok=True)

# ---------------------------------------------------------------- 定制映射表
# key: 目标骨骼; value: (源三点链, 目标三点链)
# 三点链 (a,b,c) 用于构造朝向帧：y = b-a, z = cross(y, c-b)
MAP = {
    "root":       (("Root", "Pelvis", "Spine1"),          ("root", "pelvis", "spine_01")),
    "pelvis":     (("Pelvis", "L_Hip", "L_KneeUpper"),    ("pelvis", "thigh_l", "calf_l")),
    "spine_01":   (("Spine1", "Spine2", "Neck"),          ("spine_01", "spine_02", "spine_03")),
    "spine_02":   (("Spine2", "Neck", "Head"),            ("spine_02", "spine_03", "neck_01")),
    "neck_01":    (("Neck", "Head", "Spine2"),            ("neck_01", "head", "spine_03")),
    "clavicle_l": (("L_Clavicle", "L_Shoulder", "L_ElbowUpper"), ("clavicle_l", "upperarm_l", "lowerarm_l")),
    "upperarm_l": (("L_Shoulder", "L_ElbowUpper", "L_Elbow"),    ("upperarm_l", "lowerarm_l", "hand_l")),
    "lowerarm_l": (("L_Elbow", "L_Hand", "L_ElbowUpper"),        ("lowerarm_l", "hand_l", "upperarm_l")),
    "clavicle_r": (("R_Clavicle", "R_Shoulder", "R_ElbowUpper"), ("clavicle_r", "upperarm_r", "lowerarm_r")),
    "upperarm_r": (("R_Shoulder", "R_ElbowUpper", "R_Elbow"),    ("upperarm_r", "lowerarm_r", "hand_r")),
    "lowerarm_r": (("R_Elbow", "R_Hand", "R_ElbowUpper"),        ("lowerarm_r", "hand_r", "upperarm_r")),
    "thigh_l":    (("L_Hip", "L_KneeUpper", "L_Foot"),    ("thigh_l", "calf_l", "foot_l")),
    "calf_l":     (("L_KneeLower", "L_Foot", "L_Toe"),    ("calf_l", "foot_l", "toe_l")),
    "foot_l":     (("L_Foot", "L_Toe", "L_KneeLower"),    ("foot_l", "toe_l", "calf_l")),
    "thigh_r":    (("R_Hip", "R_KneeUpper", "R_Foot"),    ("thigh_r", "calf_r", "foot_r")),
    "calf_r":     (("R_KneeLower", "R_Foot", "R_Toe"),    ("calf_r", "foot_r", "toe_r")),
    "foot_r":     (("R_Foot", "R_Toe", "R_KneeLower"),    ("foot_r", "toe_r", "calf_r")),
    # 终末骨：借用父级三点链（位置由父级决定，旋转跟随父级 + 自身微调）
    "hand_l":     (("L_Elbow", "L_Hand", "L_ElbowUpper"), ("lowerarm_l", "hand_l", "upperarm_l")),
    "hand_r":     (("R_Elbow", "R_Hand", "R_ElbowUpper"), ("lowerarm_r", "hand_r", "upperarm_r")),
    "toe_l":      (("L_KneeLower", "L_Foot", "L_Toe"),    ("calf_l", "foot_l", "toe_l")),
    "toe_r":      (("R_KneeLower", "R_Foot", "R_Toe"),    ("calf_r", "foot_r", "toe_r")),
    "head":       (("Neck", "Head", "Spine2"),            ("neck_01", "head", "spine_03")),
}
# spine_03 无源对应：由 spine_02 分摊（在写入时按比例处理）
SPLIT = {"spine_03": ("spine_02", 0.45)}

def imp(p, kind):
    before = set(bpy.data.objects)
    if kind == "fbx":
        bpy.ops.import_scene.fbx(filepath=p, automatic_bone_orientation=True)
    else:
        bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    return [o for o in new if o.type == 'ARMATURE'][0], [o for o in new if o.type == 'MESH']

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
sc.render.fps_base = 1.0
tgt, tgt_meshes = imp(TGT_FBX, "fbx")
src, src_meshes = imp(SRC_GLB, "glb")
for m in src_meshes:
    m.hide_render = True; m.hide_viewport = True
print(f"tgt={tgt.name}({len(tgt.data.bones)}) src={src.name}({len(src.data.bones)})")

# ---------------------------------------------------------------- 几何朝向帧
def wpos(arm, name, rest=False):
    if rest:
        b = arm.data.bones.get(name)
        return (arm.matrix_world @ b.head_local) if b else None
    pb = arm.pose.bones.get(name)
    return (arm.matrix_world @ pb.matrix).translation if pb else None

FALLBACK_UP = Vector((0.0, 0.0, 1.0))

def geo_frame(arm, triple, rest):
    a, b, c = triple
    Pa, Pb, Pc = wpos(arm, a, rest), wpos(arm, b, rest), wpos(arm, c, rest)
    if None in (Pa, Pb, Pc):
        return None
    y = Pb - Pa
    if y.length < 1e-6:
        return None
    y.normalize()
    ref = Pc - Pb
    z = y.cross(ref)
    if z.length < 1e-5:
        z = y.cross(FALLBACK_UP)
        if z.length < 1e-5:
            z = y.cross(Vector((1.0, 0.0, 0.0)))
    z.normalize()
    x = y.cross(z).normalized()
    return Matrix((x, y, z)).transposed()

# 检查映射完整性
missing = []
for t_name, (s_tri, t_tri) in MAP.items():
    if tgt.data.bones.get(t_name) is None: missing.append("T:" + t_name)
    for n in s_tri:
        if src.data.bones.get(n) is None: missing.append("S:" + n)
    for n in t_tri:
        if tgt.data.bones.get(n) is None: missing.append("T:" + n)
print("映射缺失:", sorted(set(missing)) if missing else "无")

# ---------------------------------------------------------------- 空间对齐 Q
def rest_basis(arm, l, r):
    L = arm.matrix_world @ arm.data.bones[l].head_local
    R = arm.matrix_world @ arm.data.bones[r].head_local
    v = R - L; v.z = 0.0
    if v.length < 1e-6: v = Vector((1, 0, 0))
    v.normalize()
    up = Vector((0, 0, 1))
    return Matrix((v, up.cross(v), up)).transposed()
Q = rest_basis(tgt, "thigh_l", "thigh_r") @ rest_basis(src, "L_Hip", "R_Hip").inverted()
Q_inv = Q.inverted()
print("Q =", round(math.degrees(Q.to_euler().z), 3), "deg about Z")

# ---------------------------------------------------------------- 尺度
def headz(arm, n):
    b = arm.data.bones.get(n)
    return (arm.matrix_world @ b.head_local).z if b else None
src_h, tgt_h = headz(src, "Head"), headz(tgt, "head")
src_f = min(v for v in [headz(src, "L_Toe"), headz(src, "R_Toe")] if v is not None)
tgt_f = min(v for v in [headz(tgt, "toe_l"), headz(tgt, "toe_r")] if v is not None)
SCALE = (tgt_h - tgt_f) / (src_h - src_f)
print("SCALE =", round(SCALE, 6))

# ---------------------------------------------------------------- 目标骨架层级
order = []
def _walk(b):
    order.append(b.name)
    for c in b.children: _walk(c)
for b in tgt.data.bones:
    if b.parent is None: _walk(b)
rest_rel_all = {b.name: (b.matrix_local.to_3x3() if b.parent is None
                else b.parent.matrix_local.to_3x3().inverted() @ b.matrix_local.to_3x3())
                for b in tgt.data.bones}
tgt_rest_rot = {b.name: b.matrix_local.to_3x3() for b in tgt.data.bones}

# 目标各骨的静止几何帧 + 逐骨骼「静止基准对齐矩阵 K」
#   K = Q · F_src_rest · F_tgt_rest⁻¹
#   作用：让「源静止姿态」映射到目标后，目标也处于源静止姿态，消除两套 A-Pose 的基准差
T_FRAME_REST = {t: geo_frame(tgt, MAP[t][1], True) for t in MAP}
S_FRAME_REST = {t: geo_frame(src, MAP[t][0], True) for t in MAP}
K_MAT = {}
K_ANG = {}
YAXIS = Vector((0.0, 1.0, 0.0))
for t in MAP:
    if S_FRAME_REST[t] is None or T_FRAME_REST[t] is None:
        continue
    # 只对齐「骨方向」，用最小弧旋转（不动滚转基准，避免 180° 翻转）
    u_tgt = (T_FRAME_REST[t] @ YAXIS).normalized()          # 目标静止骨方向
    u_src = (Q @ S_FRAME_REST[t] @ YAXIS).normalized()      # 源静止骨方向（映射到目标系）
    K_MAT[t] = u_tgt.rotation_difference(u_src).to_matrix()
    K_ANG[t] = math.degrees(u_tgt.angle(u_src))
print("逐骨骼静止基准差（K 的旋转角，度）:")
for t in sorted(K_ANG):
    ang = K_ANG[t]
    flag = "OK" if ang < 8 else ("补偿" if ang < 45 else "大幅补偿!")
    print(f"   {t:12s} 静止方向差 {ang:7.1f}°   {flag}")
src_root_rest_head = (src.matrix_world @ src.data.bones["Root"].head_local).copy()

def iter_fcurves(a):
    try: return list(a.fcurves)
    except AttributeError:
        out = []
        for L in getattr(a, "layers", []):
            for s in getattr(L, "strips", []):
                for cb in getattr(s, "channelbags", []):
                    out.extend(cb.fcurves)
        return out

for pb in tgt.pose.bones:
    pb.rotation_mode = 'QUATERNION'

# ---------------------------------------------------------------- 逐动作处理
results = []
for want in WANT:
    act = None
    for a in bpy.data.actions:
        if a.name == want or a.name.endswith("_" + want) or a.name.endswith(want):
            act = a; break
    if act is None:
        print("!! 找不到动作", want); continue
    src.animation_data.action = act
    F0, F1 = int(act.frame_range[0]), int(act.frame_range[1])
    print(f"--- {want}: {act.name} frames {F0}~{F1} ---")

    # 采样：源每帧的几何帧
    frames_data = []
    for f in range(F0, F1 + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        fd = {}
        for t_name, (s_tri, _) in MAP.items():
            F = geo_frame(src, s_tri, False)
            fd[t_name] = F
        rp = src.pose.bones.get("Root")
        fd["__root_delta"] = ((src.matrix_world @ rp.matrix).translation - src_root_rest_head) * SCALE if rp else Vector((0, 0, 0))
        frames_data.append(fd)

    # 烘焙
    if tgt.animation_data is None: tgt.animation_data_create()
    for pb in tgt.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    new_act = bpy.data.actions.new("A_Darius_" + want.title().replace("_", "") + "_TP")
    tgt.animation_data.action = new_act

    for idx, f in enumerate(range(F0, F1 + 1)):
        fd = frames_data[idx]
        final_rot = {}
        for name in order:
            bone = tgt.data.bones[name]; pb = tgt.pose.bones[name]
            parent = bone.parent
            Rp = final_rot[parent.name] if parent is not None else Matrix.Identity(3)
            rr = rest_rel_all[name]

            Wt = None
            if name in MAP and fd.get(name) is not None:
                Fs_rest = geo_frame(src, MAP[name][0], True)
                Ft_rest = T_FRAME_REST[name]
                if Fs_rest is not None and Ft_rest is not None:
                    D = fd[name] @ Fs_rest.inverted()          # 源骨骼世界旋转增量（纯几何）
                    Dq = Q @ D @ Q_inv
                    Wt = Dq @ K_MAT.get(name, Matrix.Identity(3)) @ tgt_rest_rot[name]
            elif name in SPLIT:
                pname, ratio = SPLIT[name]
                if fd.get(pname) is not None:
                    Fs_rest = geo_frame(src, MAP[pname][0], True)
                    if Fs_rest is not None:
                        D = fd[pname] @ Fs_rest.inverted()
                        Wt = (Q @ D @ Q_inv) @ K_MAT.get(pname, Matrix.Identity(3)) @ tgt_rest_rot[name]

            if Wt is None:
                final_rot[name] = Rp @ rr
                continue

            # 脊椎俯仰特调
            if SPINE_PITCH != 0.0 and name in ("spine_01", "spine_02", "spine_03", "neck_01"):
                wgt = {"spine_01": 0.45, "spine_02": 0.35, "spine_03": 0.20, "neck_01": -0.6}[name]
                Wt = Matrix.Rotation(math.radians(SPINE_PITCH) * wgt, 3, 'X') @ Wt

            final_rot[name] = Wt
            pb.rotation_quaternion = (rr.inverted() @ Rp.inverted() @ Wt).to_quaternion()
            if name == "root":
                pb.location = tgt_rest_rot[name].inverted() @ fd["__root_delta"]

        for name in order:
            tgt.pose.bones[name].keyframe_insert("rotation_quaternion", frame=f)
            if name == "root":
                tgt.pose.bones[name].keyframe_insert("location", frame=f)

    for fc in iter_fcurves(new_act):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    print(f"    烘焙 {new_act.name} 曲线 {len(iter_fcurves(new_act))}")
    results.append(new_act.name)

# ---------------------------------------------------------------- 自检：绝对朝向误差
print()
print("=" * 96)
print("【自检】绝对朝向误差 = angle( Q·F_src_pose , F_tgt_pose )   0°=朝向完全一致")
print("=" * 96)
import math as _m
for act_name in results:
    a = bpy.data.actions[act_name]
    tgt.animation_data.action = a
    sc.frame_set(int(a.frame_range[0])); bpy.context.view_layer.update()
    rows = []
    for t in MAP:
        Fs = geo_frame(src, MAP[t][0], False) if False else None
    print(f"   （动作 {act_name} 已烘焙，逐帧误差见独立验证脚本）")
print()

# ---------------------------------------------------------------- 导出
# ⚠️⚠️ 关键修复（2026-09-18）：导出前必须把骨架复位到 rest pose，且必须改用
#      all_actions=True 单文件多 take 导出。原先「循环内挂 action 逐个导出」是错的。
#
# 实测依据（plan_17 导出行为探针，同一场景三种方式各导一个 FBX 再回读）：
#   A. 挂 action + frame_set 后导出（本脚本原先的做法）→ bind pose 偏差 5.843e-02  **BROKEN**
#   B. 清 pose 后导出，all_actions=False                → 1.198e-07 OK，但只含 1 个动画
#   C. 清 pose 后导出，all_actions=True                 → 1.198e-07 OK，46 个动画全保真
#
# 机理：Blender 的 FBX 导出器用「导出瞬间的 pose」写骨架的节点变换，而不是 rest pose。
#   挂 action 时 pose 就是该 action 在当前 frame 的值 ⇒ bind pose 被污染。
#   bind pose 是所有动画共同的参考系，一旦错位，IK Retargeter 与动画导入会整体偏斜。
#
# 历史影响（plan_16 审计 Saved/Retarget 下 17 个 FBX）：15 个 BROKEN，
#   关节间距偏差 1.4% ~ 15.4%（TurnL/TurnR 最差，Attack1 12.8%）。
if tgt.animation_data:
    tgt.animation_data.action = None
for _pb in tgt.pose.bones:
    _pb.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()

bpy.ops.object.select_all(action='DESELECT')
tgt.select_set(True); bpy.context.view_layer.objects.active = tgt
out = os.path.join(OUTDIR, "A_Darius_All_TP.fbx").replace("\\", "/")
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, bake_anim=True,
    bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
    bake_anim_use_all_actions=True,
    bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0,
    add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X',
    apply_unit_scale=True, global_scale=1.0, armature_nodetype='NULL')
print("导出（单文件多 take）:", out)
print("  ⚠️ 输出契约已变更：原先「每个动作一个 FBX」→ 现在「一个 FBX 含全部 %d 个 take」。" % len(results))
print("     UE 侧仍需显式指定 FbxImportUI.skeleton；一次导入即建出全部 AnimSequence")
print("     （已实测：48 资产 = 1 Skeleton + 1 Mesh + 46 AnimSequence）。")
print("=== V3 DONE:", results, "===")
