# -*- coding: utf-8 -*-
"""Mixamo 动作转换器：骨名改 Mannequin 命名 + 去根位移 + 平移量纲对齐。

## 为什么要这一步
试用的 `Mutant Walking.fbx` / `Walking Backward.fbx` 是 **Mixamo 骨架**
（65 骨、`mixamorig:` 前缀、**无网格**、60fps、**带根位移**）。
目标 `SK_Darius_GodKing` 是 Mannequin 命名（pelvis / spine_01 / thigh_l …），
**把骨名改成一致后，动画可以直接挂到 Darius 骨架上播放** —— 不需要 IK Retargeter，
也因此绕开整套 Retarget Pose 标定（那正是交叉腿的问题来源）。

## 本脚本做四件事
1. 骨名映射（只保留主干链，其余删掉；缺失的骨由目标骨架 ref pose 补齐）
2. **平移通道 ×0.01**：Darius 最外层骨有 scale=100，骨骼局部平移是「除以 100 之前」的量纲
   （pelvis 局部平移 ≈1.0967 = 109.67cm 髋高）。Mixamo 的数值是 cm ⇒ 必须 ×0.01
3. **去根位移**：把骨盆的水平位移逐帧抵消掉（保留垂直起伏），得到 in-place，
   才能喂给 `CharacterMovement` 驱动的角色（否则滑步或原地踏步）
4. 导出前**复位 rest pose** + `bake_anim_use_all_actions=True`
   （不复位 ⇒ bind pose 被污染，这是本项目踩过的坑）

用法：
    blender -b -P <本脚本> -- <输入FBX> <输出FBX>
"""
import bpy
import sys
from mathutils import Matrix, Vector

argv = sys.argv
if "--" not in argv:
    print("!! 用法: blender -b -P <脚本> -- <输入FBX> <输出FBX>")
    sys.exit(1)
args = argv[argv.index("--") + 1:]
IN_FBX, OUT_FBX = args[0], args[1]

# Mixamo -> Mannequin（UE）主干映射
MAP = {
    "mixamorig:Hips": "pelvis",
    "mixamorig:Spine": "spine_01",
    "mixamorig:Spine1": "spine_02",
    "mixamorig:Spine2": "spine_03",
    "mixamorig:Neck": "neck_01",
    "mixamorig:Head": "head",
    "mixamorig:LeftShoulder": "clavicle_l",
    "mixamorig:RightShoulder": "clavicle_r",
    "mixamorig:LeftArm": "upperarm_l",
    "mixamorig:RightArm": "upperarm_r",
    "mixamorig:LeftForeArm": "lowerarm_l",
    "mixamorig:RightForeArm": "lowerarm_r",
    "mixamorig:LeftHand": "hand_l",
    "mixamorig:RightHand": "hand_r",
    "mixamorig:LeftUpLeg": "thigh_l",
    "mixamorig:RightUpLeg": "thigh_r",
    "mixamorig:LeftLeg": "calf_l",
    "mixamorig:RightLeg": "calf_r",
    "mixamorig:LeftFoot": "foot_l",
    "mixamorig:RightFoot": "foot_r",
    "mixamorig:LeftToeBase": "ball_l",
    "mixamorig:RightToeBase": "ball_r",
}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=IN_FBX)
arm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
if arm is None:
    print("!! FBX 里没有骨架")
    sys.exit(1)

print("=== 转换 %s ===" % IN_FBX)
print("   原始骨数 = %d" % len(arm.data.bones))

# ---------------------------------------------------------------- 1. 删骨 + 改名
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
eb = arm.data.edit_bones
# 先删不在映射里的骨（从深到浅，避免父级丢失）
order = sorted(eb[:], key=lambda b: -len(b.parent_recursive))
removed = 0
for b in order:
    if b.name not in MAP:
        try:
            eb.remove(b)
            removed += 1
        except Exception:
            pass
renamed = 0
for b in eb:
    if b.name in MAP:
        old = b.name
        b.name = MAP[old]
        renamed += 1
bpy.ops.object.mode_set(mode="OBJECT")
print("   删除 %d 根 / 改名 %d 根 ⇒ 剩 %d 根" % (removed, renamed, len(arm.data.bones)))

# ---------------------------------------------------------------- fcurve 的骨名也要改
# ⚠️ 改 edit_bone.name **不会**更新 fcurve 的 data_path（里面有引号包住的旧骨名）
act = arm.animation_data.action if arm.animation_data else None
if act is None and bpy.data.actions:
    act = bpy.data.actions[0]
    arm.animation_data_create()
    arm.animation_data.action = act
if act is None:
    print("!! 没有动作数据")
    sys.exit(1)

fixed = 0


def iter_fcurves(action):
    for layer in action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    yield fc


for fc in iter_fcurves(act):
    dp = fc.data_path
    for old, new in MAP.items():
        if old in dp:
            fc.data_path = dp.replace(old, new)
            fixed += 1
            break
print("   fcurve data_path 改写 = %d 条" % fixed)

# ---------------------------------------------------------------- 2. 去根位移（in-place）
scene = bpy.context.scene
f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
pb = arm.pose.bones.get("pelvis")
root_src = None
for old in ("mixamorig:Hips",):
    if old in MAP:
        root_src = old
if pb is not None:
    scene.frame_set(f0)
    bpy.context.view_layer.update()
    W0 = (arm.matrix_world @ pb.matrix).translation.copy()
    R_inv = arm.matrix_world.to_3x3().inverted()
    travel = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        W = (arm.matrix_world @ pb.matrix).translation
        horiz = Vector((W.x - W0.x, W.y - W0.y, 0.0))
        delta = -(R_inv @ horiz)
        pb.location = pb.location + delta
        pb.keyframe_insert(data_path="location", frame=f)
        travel.append(horiz.length)
    # 记录剩余水平位移（应≈0）
    scene.frame_set(f1)
    bpy.context.view_layer.update()
    Wn = (arm.matrix_world @ pb.matrix).translation
    print("   去位移后 首末帧水平差 = %.3f（原最大位移 %.1f）" %
          ((Vector((Wn.x, Wn.y, 0)) - Vector((W0.x, W0.y, 0))).length, max(travel)))
else:
    print("   !! 找不到 pelvis，跳过去位移")

# ---------------------------------------------------------------- 3. 平移通道 ×0.01
scaled = 0
for fc in iter_fcurves(act):
    if fc.data_path.rstrip(']').endswith("location"):
        for kp in fc.keyframe_points:
            kp.co[1] *= 0.01
        scaled += 1
print("   location 通道 ×0.01 = %d 条" % scaled)

# ---------------------------------------------------------------- 3.5 节点缩放归一
# Mixamo FBX 的骨架对象自带 scale=0.01（文件是厘米，Blender 场景是米），
# 实测髋骨世界高 1.02m、前进方向是世界 −Y、位移 1.88m/1.43s ≈ 1.3m/s。
# 平移通道已经 ×0.01（cm → m），所以对象缩放必须改回 1.0，
# 否则 FBX 里残留的 0.01 会被 UE 烘成**根骨 scale 轨道** ⇒ 角色缩成 1.85cm（坑 E 同款）。
arm.scale = (1.0, 1.0, 1.0)
print("   骨架节点缩放 → 1.0（避免 UE 烘出根骨 scale 轨道）")

# ---------------------------------------------------------------- 3.6 加网格载体
# 🔴 已知坑：**纯骨架 FBX 导入 UE 产出 0 资产**（不报错）。UE 需要至少一个
#    SkeletalMesh 当骨架载体。这里挂一个 1cm 立方体，顶点全权重给 pelvis。
#    导入后它会变成一个垃圾 SkeletalMesh 资产，动画才是我们要的（垃圾资产随后清理）。
bpy.ops.mesh.primitive_cube_add(size=0.01, location=(0.0, 0.0, 0.0))
cube = bpy.context.object
cube.name = "CarrierMesh"
cube.parent = arm
mod = cube.modifiers.new("Armature", "ARMATURE")
mod.object = arm
vg = cube.vertex_groups.new(name="pelvis")
vg.add(list(range(len(cube.data.vertices))), 1.0, "REPLACE")
print("   已挂网格载体 CarrierMesh（顶点 %d，全权重 pelvis）" % len(cube.data.vertices))

# ---------------------------------------------------------------- 4. 导出（必须复位 rest pose）
arm.animation_data.action = None
for p in arm.pose.bones:
    p.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()

# 🔴 关键：**孤立 action 不会被 FBX 导出器带走**（实测：action=None 后导出 0 个 take）。
#    解法：把 action 推到 NLA 轨道（strip），导出的 take 来自 NLA，
#    而当前 pose 仍是 rest ⇒ 既不丢动画，也不污染 bind pose。
# ⚠️ take 名必须干净：Mixamo 原名 `Armature|mixamo.com|Layer0` 含 `|` 与非 ASCII 片段，
#    怀疑 UE 的资产命名/Interchange 因此静默不建 AnimSequence（实测两种导入模式都只有 Mesh）。
act.name = "Walk"
track = arm.animation_data.nla_tracks.new()
track.name = "Walk"
strip = track.strips.new(act.name, int(act.frame_range[0]), act)
strip.action_frame_start = int(act.frame_range[0])
strip.action_frame_end = int(act.frame_range[1])
bpy.context.view_layer.update()
print("   已推入 NLA：%s（%d..%d 帧）" % (act.name, int(act.frame_range[0]), int(act.frame_range[1])))

# ⚠️ 参数照抄 plan_10_src_clean.py 里**实测能导出 46 个 take** 的那组。
#    我自己写的精简版（object_types + use_selection=False）实测导出 **0 个 action**
#    —— 动画在导出环节被丢掉了，血亏一次。
for o in bpy.data.objects:
    o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(
    filepath=OUT_FBX,
    use_selection=True,
    bake_anim=True,
    bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=True,
    bake_anim_use_all_actions=True,
    bake_anim_force_startend_keying=True,
    bake_anim_simplify_factor=0.0,
    add_leaf_bones=False,
    primary_bone_axis="Y",
    secondary_bone_axis="X",
    apply_unit_scale=True,
    global_scale=1.0,
    armature_nodetype="NULL",
)
print("   导出 → %s" % OUT_FBX)
print("=== DONE ===")
