"""前置侦察：确认 GLB 源与 Darius 目标骨架在 Blender 里能不能对上。

只读 —— 不改任何工程资产。产出 Saved/Attack/recon.txt。

用法：
  blender -b -P Scripts/anim/atk_05_recon.py -- <GLB> <DariusFBX> <OUT_TXT>
"""
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
GLB, TGT_FBX, OUT = argv[0], argv[1], argv[2]

LOG = []


def P(*a):
    s = " ".join(str(x) for x in a)
    LOG.append(s)
    print(s)


def armatures():
    return [o for o in bpy.data.objects if o.type == "ARMATURE"]


def hip_axis_world(arm, lbone, rbone):
    """右侧髋骨指向左侧髋骨的向量（水平投影），再取反 = 角色右轴。"""
    bl, br = arm.data.bones.get(lbone), arm.data.bones.get(rbone)
    if not bl or not br:
        return None
    pl = (arm.matrix_world @ bl.head_local)
    pr = (arm.matrix_world @ br.head_local)
    v = Vector((pr.x - pl.x, pr.y - pl.y, 0.0))
    return v.normalized() if v.length > 1e-6 else None


def yaw_of(v):
    return math.degrees(math.atan2(v.y, v.x))


# ------------------------------------------------------------------ 源
bpy.ops.wm.read_factory_settings(use_empty=True)
P("=" * 74)
P("### 导入源 GLB:", GLB)
bpy.ops.import_scene.gltf(filepath=GLB)
src = armatures()
P("  骨架对象数 =", len(src))
for a in src:
    P("    -", a.name, "| 骨数 =", len(a.data.bones), "| scale =", tuple(round(s, 4) for s in a.scale))
sarm = src[0]

acts = sorted(a.name for a in bpy.data.actions)
P("  动作数 =", len(acts))
P("  含 attack 的动作:", [n for n in acts if "attack" in n.lower()])
P("  含 crit 的动作  :", [n for n in acts if "crit" in n.lower()])
P("  含 idle1 的动作 :", [n for n in acts if "idle1" in n.lower()])

WANT = ["Root", "Pelvis", "Spine1", "Spine2", "Neck", "Head", "Jaw",
        "L_Clavicle", "R_Clavicle", "L_Shoulder", "R_Shoulder",
        "L_Elbow", "R_Elbow", "L_Hand", "R_Hand",
        "L_Hip", "R_Hip", "L_KneeLower", "R_KneeLower", "L_Foot", "R_Foot", "L_Toe", "R_Toe",
        "Weapon", "Axe_Handle", "Axe_Head", "SnapWeapon", "SnapWeapon2Hand"]
have = {b.name for b in sarm.data.bones}
P("  关注骨是否齐:")
for w in WANT:
    P("    %-16s %s" % (w, "OK" if w in have else "!! 缺"))

for an in ("darius_skin15_attack1", "darius_skin15_idle1"):
    a = bpy.data.actions.get(an)
    if a:
        fr = a.frame_range
        P("  动作 %-26s 帧范围 = %.1f .. %.1f" % (an, fr[0], fr[1]))
    else:
        P("  动作 %s 未找到" % an)

sright = hip_axis_world(sarm, "L_Hip", "R_Hip")
P("  源 髋轴(指向右) =", tuple(round(c, 4) for c in sright) if sright else None,
  "| yaw = %.2f°" % yaw_of(sright) if sright else "")
for nm in ("Root", "Pelvis", "Spine1", "Spine2", "Neck"):
    b = sarm.data.bones.get(nm)
    if b:
        P("    源 %-8s rest head = %s" % (nm, tuple(round(c, 4) for c in (sarm.matrix_world @ b.head_local))))

# ------------------------------------------------------------------ 目标
P("=" * 74)
P("### 导入目标 FBX:", TGT_FBX)
bpy.ops.import_scene.fbx(filepath=TGT_FBX)
tgt = [a for a in armatures() if a is not sarm]
P("  骨架对象数 =", len(tgt))
for a in tgt:
    P("    -", a.name, "| 骨数 =", len(a.data.bones), "| scale =", tuple(round(s, 4) for s in a.scale))
tarm = tgt[0]

thave = {b.name for b in tarm.data.bones}
TMAP = ["root", "pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head",
        "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r",
        "hand_l", "hand_r", "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r",
        "ball_l", "ball_r", "weapon_jnt", "weapon_jnt_l", "weapon_jnt_r", "weapon_jnt_offset",
        "darius_godking_mesh_LOD0_Skeleton"]
P("  目标关注骨是否齐:")
for w in TMAP:
    P("    %-32s %s" % (w, "OK" if w in thave else "!! 缺"))

P("  weapon_jnt 的父级 =", tarm.data.bones["weapon_jnt"].parent.name if "weapon_jnt" in thave and tarm.data.bones["weapon_jnt"].parent else "(无/未找到)")
for nm in ("root", "pelvis", "spine_01", "spine_02", "spine_03", "weapon_jnt"):
    b = tarm.data.bones.get(nm)
    if b:
        P("    目标 %-12s rest head = %s  parent = %s" % (
            nm, tuple(round(c, 4) for c in (tarm.matrix_world @ b.head_local)),
            b.parent.name if b.parent else "-"))

tright = hip_axis_world(tarm, "thigh_l", "thigh_r")
P("  目标 髋轴(指向右) =", tuple(round(c, 4) for c in tright) if tright else None,
  "| yaw = %.2f°" % yaw_of(tright) if tright else "")

# ------------------------------------------------------------------ 对齐
P("=" * 74)
if sright and tright:
    fix = yaw_of(tright) - yaw_of(sright)
    while fix > 180:
        fix -= 360
    while fix < -180:
        fix += 360
    P("### 全局对齐：R_fix = 绕 Z 转 %.3f° （目标髋轴 yaw − 源髋轴 yaw）" % fix)
    P("    → 常量 YAW_FIX_DEG = %.3f" % fix)
else:
    P("### !! 髋轴算不出来，无法自动对齐")

P("=" * 74)
P("### 尺寸核对（世界包围盒高度）")
for tag, arm in (("源", sarm), ("目标", tarm)):
    zs = [(arm.matrix_world @ b.head_local).z for b in arm.data.bones]
    if zs:
        P("  %s 骨架 rest 高度范围 z = %.4f .. %.4f (跨度 %.4f)" % (tag, min(zs), max(zs), max(zs) - min(zs)))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(LOG))
P("已写:", OUT)
