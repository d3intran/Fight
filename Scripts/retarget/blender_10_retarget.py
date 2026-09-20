"""
================================================================================
 LOL 俯视角动画 -> 2XKO 次时代骨架  离线重定向 + 第三人称特调 (blender_10_retarget.py)
 --------------------------------------------------------------------------------
 流程：
   1. 导入目标骨架（2XKO God King FBX，309 骨，UE Mannequin 命名）
   2. 导入源骨架（LOL .anm -> .glb，179 骨，俯视角 MOBA 动画）
   3. 按骨骼映射表，用「世界旋转增量」算法把源动画逐帧搬运到目标骨架
      W_target = (W_src @ Rest_src^-1) @ Rest_target
   4. 叠加第三人称特调层：
        - 脊椎俯仰角补偿（Spine Pitch Offset）
        - 颈部反向补偿（保持视线水平）
        - 根骨骼位移等比缩放（100:1 单位归一）
   5. 烘焙为 Action 并导出 FBX 供 UE 导入

 用法:
   blender -b -P blender_10_retarget.py -- <SRC_GLB> <TGT_FBX> <OUT_FBX> [spine_pitch_deg] [scale]
================================================================================
"""
import bpy
import sys
import os
import math
from mathutils import Matrix, Vector, Quaternion

argv = sys.argv[sys.argv.index("--") + 1:]
SRC_GLB = argv[0]
TGT_FBX = argv[1]
OUT_FBX = argv[2]
SPINE_PITCH = float(argv[3]) if len(argv) > 3 else 12.0
NECK_COMP = 0.6            # 颈部反向补偿比例
FORCE_SCALE = float(argv[4]) if len(argv) > 4 else 0.0

os.makedirs(os.path.dirname(OUT_FBX), exist_ok=True)

# ---------------------------------------------------------------- 骨骼映射表
# (LOL 源骨骼, 2XKO 目标骨骼)  —— 顺序必须父级在前
BONE_MAP = [
    ("Root",       "root"),
    ("Pelvis",     "pelvis"),
    ("Spine1",     "spine_01"),
    ("Spine2",     "spine_02"),
    ("Neck",       "neck_01"),
    ("Head",       "head"),
    ("L_Clavicle", "clavicle_l"),
    ("L_Shoulder", "upperarm_l"),
    ("L_Elbow",    "lowerarm_l"),
    ("L_Hand",     "hand_l"),
    ("R_Clavicle", "clavicle_r"),
    ("R_Shoulder", "upperarm_r"),
    ("R_Elbow",    "lowerarm_r"),
    ("R_Hand",     "hand_r"),
    ("L_Hip",      "thigh_l"),
    ("L_KneeLower", "calf_l"),
    ("L_Foot",     "foot_l"),
    ("L_Toe",      "toe_l"),
    ("R_Hip",      "thigh_r"),
    ("R_KneeLower", "calf_r"),
    ("R_Foot",     "foot_r"),
    ("R_Toe",      "toe_r"),
]
# 受脊椎俯仰特调影响的骨骼
SPINE_CHAIN = {"spine_01": 0.45, "spine_02": 0.35, "spine_03": 0.20}
NECK_CHAIN = {"neck_01": -NECK_COMP}


def import_target(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=True)
    new = [o for o in bpy.data.objects if o not in before]
    arm = [o for o in new if o.type == 'ARMATURE'][0]
    return arm, [o for o in new if o.type == 'MESH']


def import_source(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    arm = [o for o in new if o.type == 'ARMATURE'][0]
    return arm, [o for o in new if o.type == 'MESH']


print("=== [1/5] 导入目标骨架 ===", TGT_FBX)
tgt_arm, tgt_meshes = import_target(TGT_FBX)
print("   target armature:", tgt_arm.name, "bones:", len(tgt_arm.data.bones))

print("=== [2/5] 导入源骨架 ===", SRC_GLB)
src_arm, src_meshes = import_source(SRC_GLB)
print("   source armature:", src_arm.name, "bones:", len(src_arm.data.bones))

sc = bpy.context.scene
src_act = src_arm.animation_data.action if (src_arm.animation_data and src_arm.animation_data.action) else None
if not src_act:
    raise RuntimeError("源文件没有动画")
F0, F1 = int(src_act.frame_range[0]), int(src_act.frame_range[1])
print("   源动画:", src_act.name, F0, "->", F1)

# 隐藏源网格，避免污染渲染
for m in src_meshes:
    m.hide_render = True
    m.hide_viewport = True
for m in tgt_meshes:
    m.hide_render = False
    m.hide_viewport = False

# ---------------------------------------------------------------- 尺度换算
def rest_head_z(arm, name):
    b = arm.data.bones.get(name)
    return (arm.matrix_world @ b.head_local).z if b else None

src_h = rest_head_z(src_arm, "Head")
tgt_h = rest_head_z(tgt_arm, "head")
src_f = min(v for v in [rest_head_z(src_arm, "L_Toe"), rest_head_z(src_arm, "R_Toe")] if v is not None)
tgt_f = min(v for v in [rest_head_z(tgt_arm, "toe_l"), rest_head_z(tgt_arm, "toe_r")] if v is not None)
auto_scale = (tgt_h - tgt_f) / max(1e-6, (src_h - src_f))
SCALE = FORCE_SCALE if FORCE_SCALE > 0 else auto_scale
print(f"=== [3/5] 单位换算: 源身高={src_h-src_f:.2f} 目标身高={tgt_h-tgt_f:.2f} SCALE={SCALE:.6f} ===")

# ---------------------------------------------------------------- 空间对齐
# 两套骨架的「左/右/前」基准朝向不同（LOL 源面朝 +Y，2XKO 目标面朝 -Y），
# 必须先用各自的「胯骨轴 + 世界上方」构建基准坐标系，求出对齐旋转 Q。
def rest_basis(arm, l_hip, r_hip):
    L = (arm.matrix_world @ arm.data.bones[l_hip].head_local)
    R = (arm.matrix_world @ arm.data.bones[r_hip].head_local)
    right = (R - L)
    right.z = 0.0
    if right.length < 1e-6:
        right = Vector((1, 0, 0))
    right.normalize()
    up = Vector((0.0, 0.0, 1.0))
    fwd = up.cross(right)
    return Matrix((right, fwd, up)).transposed()   # 列 = right / forward / up


B_src = rest_basis(src_arm, "L_Hip", "R_Hip")
B_tgt = rest_basis(tgt_arm, "thigh_l", "thigh_r")
Q = B_tgt @ B_src.inverted()
Q_inv = Q.inverted()
print("源基准系 B_src:\n", B_src)
print("目标基准系 B_tgt:\n", B_tgt)
print("空间对齐旋转 Q (deg):", round(math.degrees(Q.to_euler().z), 2), "deg about Z")

# ---------------------------------------------------------------- 采样源动画
print("=== [4/5] 采样源动画世界旋转 ===")
src_bones = [s for s, _ in BONE_MAP]
src_rest_rot = {}
for s in src_bones:
    b = src_arm.data.bones.get(s)
    src_rest_rot[s] = b.matrix_local.to_3x3() if b else None
    if not b:
        print("   !! 源缺失骨骼:", s)

src_samples = {}
src_root_delta = {}
src_root_rest_head = (src_arm.matrix_world @ src_arm.data.bones["Root"].head_local).copy()
tgt_root_rest_head = (tgt_arm.matrix_world @ tgt_arm.data.bones["root"].head_local).copy()

for f in range(F0, F1 + 1):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    rot = {}
    for s in src_bones:
        pb = src_arm.pose.bones.get(s)
        if pb is None:
            rot[s] = None
            continue
        # 统一在「源 armature 空间」下取旋转
        rot[s] = pb.matrix.to_3x3()
    src_samples[f] = rot
    src_pb = src_arm.pose.bones.get("Root")
    if src_pb is not None:
        head_now = (src_arm.matrix_world @ src_pb.matrix).translation
        src_root_delta[f] = (head_now - src_root_rest_head) * SCALE
    else:
        src_root_delta[f] = Vector((0, 0, 0))

# ---------------------------------------------------------------- 重定向
print("=== [5/5] 重定向 + 特调 ===")
tgt_rest_rot = {}
for _, t in BONE_MAP:
    b = tgt_arm.data.bones.get(t)
    tgt_rest_rot[t] = b.matrix_local.to_3x3() if b else None

# 清理目标上已有动画
if tgt_arm.animation_data:
    tgt_arm.animation_data.action = None
for pb in tgt_arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.location = (0, 0, 0)
    pb.scale = (1, 1, 1)

pitch_rad = math.radians(SPINE_PITCH)
pitch_mats = {}
for name, w in SPINE_CHAIN.items():
    pitch_mats[name] = Matrix.Rotation(pitch_rad * w, 3, 'X')      # +X 旋转 = 向 -Y 前倾
for name, w in NECK_CHAIN.items():
    pitch_mats[name] = Matrix.Rotation(pitch_rad * w, 3, 'X')      # 负值 = 反向抬头

tgt_arm.animation_data_create()
new_action = bpy.data.actions.new("A_Darius_LOL_Run_TP")
tgt_arm.animation_data.action = new_action

warned = set()

# 目标骨架层级顺序（父级在前），以及每根骨骼相对父级的静止旋转
order = []
def _walk(b):
    order.append(b.name)
    for c in b.children:
        _walk(c)
for b in tgt_arm.data.bones:
    if b.parent is None:
        _walk(b)

rest_rel_all = {}
for b in tgt_arm.data.bones:
    if b.parent is None:
        rest_rel_all[b.name] = b.matrix_local.to_3x3()
    else:
        rest_rel_all[b.name] = b.parent.matrix_local.to_3x3().inverted() @ b.matrix_local.to_3x3()

map_tgt = {t: s for s, t in BONE_MAP}
for s, t in BONE_MAP:
    if tgt_arm.data.bones.get(t) is None:
        print("   !! 目标缺失骨骼:", t)
    if src_arm.data.bones.get(s) is None:
        print("   !! 源缺失骨骼:", s)
print("   目标骨架层级节点数:", len(order), " 映射骨骼数:", len(BONE_MAP))

for f in range(F0, F1 + 1):
    final_rot = {}
    for name in order:
        bone = tgt_arm.data.bones[name]
        pb = tgt_arm.pose.bones[name]
        parent = bone.parent
        Rp = final_rot[parent.name] if parent is not None else Matrix.Identity(3)
        rest_rel = rest_rel_all[name]

        s_name = map_tgt.get(name)
        spb = src_arm.pose.bones.get(s_name) if s_name else None
        if s_name and spb is not None:
            D = Q @ (src_samples[f][s_name] @ src_rest_rot[s_name].inverted()) @ Q_inv
            Wt = D @ tgt_rest_rot[name]
            if name in pitch_mats:
                Wt = pitch_mats[name] @ Wt
            final_rot[name] = Wt
            basis = rest_rel.inverted() @ Rp.inverted() @ Wt
            pb.rotation_quaternion = basis.to_quaternion()
            if name == "root":
                d = src_root_delta[f]
                pb.location = tgt_rest_rot[name].inverted() @ d
        else:
            # 未映射骨骼：保持静止姿态，仅继承父级旋转
            final_rot[name] = Rp @ rest_rel

    for name in order:
        pb = tgt_arm.pose.bones[name]
        pb.keyframe_insert("rotation_quaternion", frame=f)
        if name == "root":
            pb.keyframe_insert("location", frame=f)

def iter_fcurves(action):
    """兼容 Blender 4.4+ 的 Slotted Action API"""
    try:
        return list(action.fcurves)
    except AttributeError:
        pass
    out = []
    for layer in getattr(action, "layers", []):
        for strip in getattr(layer, "strips", []):
            for cb in getattr(strip, "channelbags", []):
                out.extend(cb.fcurves)
    return out


_fcs = iter_fcurves(new_action)
for fc in _fcs:
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'

sc.frame_start, sc.frame_end = F0, F1
print("   烘焙完成，帧数:", F1 - F0 + 1, "关键帧曲线:", len(_fcs))

# ---------------------------------------------------------------- 导出
# ⚠️ 关键修复（2026-09-18）：导出前必须把骨架复位到 rest pose。
#    否则 Blender 会把「导出瞬间的 pose」（此处就是刚烘焙完的最后一帧）写成骨架的
#    节点变换，产物 bind pose 完全错误 —— 实测同类写法偏差 5.843e-02，
#    plan_16 审计历史产物 17 个 FBX 中 15 个 BROKEN（间距偏差最高 15.4%）。
#
# ⚠️ DEPRECATED：本脚本是重定向管线的最早版本，已被 blender_51_retarget_v4.py 取代
#    （AGENTS.md §3.3 未收录本文件）。它的「单文件单动作 + all_actions=False」输出契约
#    未经过 plan_17 探针的完整验证 —— 清 pose 后导出器究竟选哪个 action 仍有不确定性。
#    需要批量重定向请使用 blender_51_retarget_v4.py（已改为「清 pose + all_actions=True」）。
tgt_arm.animation_data.action = None
for _pb in tgt_arm.pose.bones:
    _pb.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()

bpy.ops.object.select_all(action='DESELECT')
tgt_arm.select_set(True)
bpy.context.view_layer.objects.active = tgt_arm
for m in tgt_meshes:
    m.select_set(True)

bpy.ops.export_scene.fbx(
    filepath=OUT_FBX,
    use_selection=True,
    bake_anim=True,
    bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=False,
    bake_anim_use_all_actions=False,
    add_leaf_bones=False,
    primary_bone_axis='Y',
    secondary_bone_axis='X',
    apply_unit_scale=True,
    global_scale=1.0,
    mesh_smooth_type='FACE',
    armature_nodetype='NULL',
)
print("=== 导出完成:", OUT_FBX, "===")
print("=== BLENDER RETARGET DONE ===")
