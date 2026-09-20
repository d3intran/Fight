# -*- coding: utf-8 -*-
"""把转换后的 Mixamo 动作**烘焙绑到 Darius 骨架**上，导出「带动画的 Darius FBX」。

## 背景
用户要看的是「这两个走路动作套在德莱厄斯身上顺不顺眼」。UE 侧目前只出 SkeletalMesh
不出 AnimSequence（未解决），所以在 Blender 里直接绑：Darius 骨架是 Mannequin 命名，
转换后的 Mixamo 动作已是同一套骨名 ⇒ 可以逐骨烘焙。

## 为什么不能直接「把 action 赋给另一个骨架」
1. Blender 5 的 **slotted action** 绑在原骨架的 slot 上，赋给别的骨架不生效（实测脚一帧不动）
2. 两套骨架的 **rest 朝向约定不同**，直接拷 `rotation_quaternion` 会让四肢乱转
   ⇒ 必须做静止基准补偿：`R_dst = C ⊗ R_src ⊗ C⁻¹`，`C = rest_dst⁻¹ ⊗ rest_src`
   （与 `blender_51_retarget_v4` 的「逐骨骼静止基准对齐矩阵 K」同一思路）

## 平移只搬 pelvis 的**增量**
两套骨架的骨长/比例不同，绝对平移不能照搬；但骨盆的起伏与摆动是走动感的关键，
所以搬 delta（相对各自 rest 的偏移）。前进位移已在转换阶段去掉 ⇒ 原地走，不会飘走。

用法：
    blender -b -P <本脚本> -- <DariusFBX> <转换后的动作FBX> <输出FBX>
"""
import bpy
import sys
from mathutils import Matrix

argv = sys.argv
if "--" not in argv:
    print("!! 用法: blender -b -P <脚本> -- <DariusFBX> <动作FBX> <输出FBX>")
    sys.exit(1)
args = argv[argv.index("--") + 1:]
DARIUS, MIX, OUT = args[0], args[1], args[2]

bpy.ops.wm.read_factory_settings(use_empty=True)
print("=== 烘焙绑定 %s -> Darius ===" % MIX.split("\\")[-1])

bpy.ops.import_scene.fbx(filepath=DARIUS)
darm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
if darm is None:
    print("!! Darius 没有骨架")
    sys.exit(1)
print("   Darius: 骨=%d scale=%s" % (len(darm.data.bones), [round(s, 3) for s in darm.scale]))

bpy.ops.import_scene.fbx(filepath=MIX)
marm = next((o for o in bpy.data.objects if o.type == "ARMATURE" and o is not darm), None)
mact = None
if marm is not None:
    mact = marm.animation_data.action if (marm.animation_data and marm.animation_data.action) else None
if mact is None and bpy.data.actions:
    mact = bpy.data.actions[-1]
if mact is None:
    print("!! 没拿到动作")
    sys.exit(1)
if marm.animation_data is None:
    marm.animation_data_create()
marm.animation_data.action = mact
print("   动作: %s  %d..%d 帧" % (mact.name, int(mact.frame_range[0]), int(mact.frame_range[1])))

# ---------------------------------------------------------------- 目标骨集合
NAMES = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head",
         "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l",
         "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r",
         "thigh_l", "calf_l", "foot_l", "ball_l",
         "thigh_r", "calf_r", "foot_r", "ball_r"]
use = [n for n in NAMES if n in darm.data.bones and n in marm.data.bones]
missing = [n for n in NAMES if n not in darm.data.bones or n not in marm.data.bones]
print("   可绑骨 = %d / %d%s" % (len(use), len(NAMES),
                                 ("（缺：%s）" % missing) if missing else ""))

# 静止基准（**armature 空间**的四元数，含父链）
rq_s = {n: marm.data.bones[n].matrix_local.to_quaternion() for n in use}
rq_d = {n: darm.data.bones[n].matrix_local.to_quaternion() for n in use}
# pelvis 位移：只搬「相对各自 rest 的**增量**」，并转到目标 pelvis 的**局部空间**。
# ⚠️ 不能把 `matrix_local.translation`（armature 空间的**绝对** rest 位置）直接赋给
#    `pose_bone.location` —— 后者在骨头自己的局部坐标系里（Y 轴沿骨），
#    直接赋值会让骨盆沿局部轴飞到 y≈−104，把整个身体和网格拖歪（实测踩过）。
PELVIS = "pelvis"
if PELVIS in use:
    Ms_rest = marm.data.bones[PELVIS].matrix_local.copy()
    Md_rest = darm.data.bones[PELVIS].matrix_local.copy()
    R_inv = Md_rest.to_3x3().inverted()      # armature space → pelvis 局部空间
else:
    Ms_rest = Md_rest = R_inv = None

for n in use:
    darm.pose.bones[n].rotation_mode = "QUATERNION"

# ---------------------------------------------------------------- 逐帧烘焙
sc = bpy.context.scene
f0, f1 = int(mact.frame_range[0]), int(mact.frame_range[1])
act2 = bpy.data.actions.new("WalkBound")
if darm.animation_data is None:
    darm.animation_data_create()
darm.animation_data.action = act2

# ⚠️ 姿态传递必须在 **armature 空间**做「朝向映射」：`Q_dst = rest_dst ⊗ rest_src⁻¹ ⊗ Q_src`。
#    早先版本用共轭 `C ⊗ Q ⊗ C⁻¹`（C = rest_dst⁻¹⊗rest_src）——语义是「绕映射轴自转」，
#    满足「源在 rest ⇒ 目标在 rest」，但**搬不动两骨架 rest 姿态的基准差**，
#    结果手臂/锁骨（rest 差异最大处）整体偏 25~38°、躯干偏 4~7°（实测数据），腿却几乎不动。
#    写回用**父→子顺序的 arm 空间矩阵链**，不依赖逐骨 view_layer 刷新。
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    P = {}
    for n in use:
        bone = darm.data.bones[n]
        par = bone.parent
        pname = par.name if par is not None else None
        if pname is not None and pname in P:
            chain = P[pname] @ darm.data.bones[pname].matrix_local.inverted()
        else:
            chain = Matrix.Identity(4)
        rest = bone.matrix_local.copy()
        Qs = marm.pose.bones[n].matrix.to_quaternion()       # 源 armature 空间朝向
        Qd = rq_d[n] @ rq_s[n].inverted() @ Qs               # 映射到目标 armature 空间
        tgt = Qd.to_matrix().to_4x4()
        tgt.translation = rest.translation
        basis = (chain @ rest).inverted() @ tgt
        darm.pose.bones[n].rotation_quaternion = basis.to_quaternion()
        darm.pose.bones[n].keyframe_insert(data_path="rotation_quaternion", frame=f)
        P[n] = tgt
    if Ms_rest is not None:
        delta = marm.pose.bones[PELVIS].matrix.translation - Ms_rest.translation
        darm.pose.bones[PELVIS].location = R_inv @ delta
        darm.pose.bones[PELVIS].keyframe_insert(data_path="location", frame=f)

sc.frame_start, sc.frame_end = f0, f1
print("   已烘焙 %d 帧 × %d 骨" % (f1 - f0 + 1, len(use)))

# ---------------------------------------------------------------- 自检
def world(arm, bone, f):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    return (arm.matrix_world @ arm.pose.bones[bone].matrix).translation.copy()

if "foot_l" in use:
    a, b, c = (world(darm, "foot_l", f) for f in (f0, (f0 + f1) // 2, f1))
    print("   自检 foot_l 世界 首/中/末: %s | %s | %s"
          % ([round(v, 3) for v in a], [round(v, 3) for v in b], [round(v, 3) for v in c]))
    moved = max((a - b).length, (b - c).length)
    print("   ⇒ %s（位移 %.3f）" % ("脚在动 ✔" if moved > 0.02 else "!! 脚没动", moved))
if "pelvis" in use:
    p = world(darm, "pelvis", f0)
    print("   自检 pelvis 世界 = %s（髋高，应 ≈1.0~1.2）" % [round(v, 3) for v in p])

# ---------------------------------------------------------------- 归位到原点
# ⚠️ 2XKO 的 Darius FBX 在 Blender 里带一个 ~100 单位的 Y 偏移（髋骨世界 y ≈ −104），
#    相机定框会因此落空（渲染出来是纯背景灰）。把骨架挪到原点，网格随父级一起走。
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
if meshes:
    lo = [min(min((o.matrix_world @ v.co)[i] for v in o.data.vertices) for o in meshes)
          for i in range(3)]
    hi = [max(max((o.matrix_world @ v.co)[i] for v in o.data.vertices) for o in meshes)
          for i in range(3)]
    print("   网格包围盒 min=%s max=%s 尺寸=%s"
          % ([round(v, 2) for v in lo], [round(v, 2) for v in hi],
             [round(hi[i] - lo[i], 2) for i in range(3)]))
# 基于**网格包围盒中心**归位（不依赖 pose bone 矩阵，最稳）：
# 把角色几何中心挪到原点、髋高压到 ~1.0m，相机定框才落得准。
if meshes:
    center = [(lo[i] + hi[i]) / 2 for i in range(3)]
    darm.location.x -= center[0]
    darm.location.y -= center[1]
    darm.location.z -= (center[2] - 1.0)
    bpy.context.view_layer.update()
    print("   已归位：骨架 location = %s（包围盒中心原 = %s）"
          % ([round(v, 3) for v in darm.location], [round(v, 3) for v in center]))

# ---------------------------------------------------------------- 清理与导出
for o in list(bpy.data.objects):
    if o is darm:
        continue
    if o.type in ("ARMATURE",) or o.name in ("CarrierMesh", "Cube"):
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except Exception:
            pass
print("   清理后对象数 = %d" % len(bpy.data.objects))

bpy.ops.export_scene.fbx(
    filepath=OUT,
    use_selection=False,
    bake_anim=True,
    bake_anim_use_all_actions=False,
    bake_anim_use_nla_strips=False,
    bake_anim_force_startend_keying=True,
    add_leaf_bones=False,
    apply_unit_scale=True,
    global_scale=1.0,
)
print("   导出 → %s" % OUT)
print("=== DONE ===")
