# -*- coding: utf-8 -*-
"""wp_51 —— 把 `WeaponAxe` 的相对变换迁到 `weapon_jnt_l` 上。

为什么
------
`wp_50` 把 `weapon_jnt_l` 烘焙成「源 `Weapon` 骨在目标 `hand_l` 局部系里的完整位姿」。
于是斧头组件只需表达「axe mesh 相对武器骨」的固定偏移，与源**完全同构**：

    F = Axe_Head 相对 Weapon 的 rest 变换（源骨架读）
    写进 BP：relative_loc = F.loc × 0.01（源 cm -> 目标 local 米）
             relative_rot = F.rot
             relative_scale = (0.01, 0.01, 0.01)   ← 抵消 weapon_jnt_l 继承的 100×

默认 **dry-run**（只打印），要写资产把 `Saved/Attack/wp51_mode.txt` 写成 apply。
写之前自动备份 BP。

⚠️ Parent Socket 没有 Python API，仍需在编辑器里手点：`hand_rSocket` -> `weapon_jnt_l`。

跑法：
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_51_axe_rel_migrate.py
"""
import json
import math
import os
import shutil
import time

import unreal

AL = unreal.AnimationLibrary
ML = unreal.MathLibrary
eal = unreal.EditorAssetLibrary
L = unreal.log
LW = unreal.log_warning

MODE_FILE = "E:/UE/Fight/Saved/Attack/wp51_mode.txt"
BP = "/Game/Character/Darius/Blueprints/BP_DariusCharacter"
BP_DISK = "E:/UE/Fight/Content/Character/Darius/Blueprints/BP_DariusCharacter.uasset"
SRC_IDLE = "/Game/Character/Darius/LOL_Source/A_LOL_Darius_idle1"
SRC_ATTACK = "/Game/Character/Darius/LOL_Source/A_LOL_Darius_attack1"
BACKUP_ROOT = "E:/UE/Fight/Saved/Attack"
ANCHOR = "weapon_jnt_l"
UNIT = 0.01


def mode():
    try:
        with open(MODE_FILE, encoding="utf-8") as f:
            return f.read().strip().lower()
    except Exception:
        return "dry"


def tq(t):
    return ((t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w),
            (t.translation.x, t.translation.y, t.translation.z),
            (t.scale3d.x, t.scale3d.y, t.scale3d.z))


def mag(v):
    return math.sqrt(sum(c * c for c in v))


def find_axe(bp):
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for h in sub.k2_gather_subobject_data_for_blueprint(bp):
        d = sub.k2_find_subobject_data_from_handle(h)
        o = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(d)
        if isinstance(o, unreal.StaticMeshComponent) and "Weapon" in o.get_name():
            return o
    return None


L("=" * 78)
L("=== wp_51  WeaponAxe 相对变换迁移到 %s   mode=%s ===" % (ANCHOR, mode()))
L("=" * 78)

# ---------------------------------------------------------------- 读源的固定偏移
L("--- 源骨架里 Axe_Head / Weapon / Axe_Handle 的局部值（f0）---")
src = unreal.load_object(None, SRC_IDLE)
off = {}
for b in ("Weapon", "Axe_Head", "Axe_Handle"):
    try:
        t = AL.get_bone_pose_for_frame(src, unreal.Name(b), 0, False)
        off[b] = tq(t)
        L("   %-12s loc=(%9.4f, %9.4f, %9.4f)  |loc|=%8.4f  scale=(%.3f, %.3f, %.3f)" % (
            b, t.translation.x, t.translation.y, t.translation.z, mag(off[b][1]),
            t.scale3d.x, t.scale3d.y, t.scale3d.z))
    except Exception as ex:
        LW("   %-12s 读不到: %s" % (b, str(ex)[:60]))

# attack1 对照（看 Axe_Head 的局部是否恒定 —— 恒定才说明它是「固定挂点」）
L("--- attack1 同项对照（Axe_Head 局部若恒定 = 固定挂点）---")
atk = unreal.load_object(None, SRC_ATTACK)
if atk and "Axe_Head" in off:
    nf = AL.get_num_frames(atk)
    vals = []
    for f in range(0, nf + 1, max(1, nf // 6)):
        try:
            t = AL.get_bone_pose_for_frame(atk, unreal.Name("Axe_Head"), f, False)
            vals.append((t.translation.x, t.translation.y, t.translation.z))
        except Exception:
            pass
    if vals:
        dmax = max(mag(tuple(vals[i][k] - vals[0][k] for k in range(3))) for i in range(len(vals)))
        L("   Axe_Head 相对 Weapon 的平移在 attack1 内最大变化 = %.4f cm  %s" % (
            dmax, "⇒ 固定挂点 ✓" if dmax < 0.01 else "⇒ 有动画（不是纯挂点）"))

if "Axe_Head" not in off:
    LW("!! 没读到 Axe_Head，无法计算 F")
    raise SystemExit(1)

F_rot = off["Axe_Head"][0]
F_loc = tuple(off["Axe_Head"][1][i] * UNIT for i in range(3))
F_scl = (UNIT, UNIT, UNIT)
L("")
L("==> 拟写入 BP 的 F：")
L("      relative_location = (%.6f, %.6f, %.6f)   |loc|=%.4f m" % (F_loc[0], F_loc[1], F_loc[2], mag(F_loc)))
q = unreal.Quat(x=F_rot[0], y=F_rot[1], z=F_rot[2], w=F_rot[3]).rotator()
L("      relative_rotation = (pitch %.4f, yaw %.4f, roll %.4f)" % (q.pitch, q.yaw, q.roll))
L("      relative_scale3d  = (0.01, 0.01, 0.01)")

bp = unreal.load_object(None, BP)
axe = find_axe(bp)
if axe is None:
    LW("!! 没找到 WeaponAxe 组件")
    raise SystemExit(1)
cl = axe.get_editor_property("relative_location")
cr = axe.get_editor_property("relative_rotation")
cs = axe.get_editor_property("relative_scale3d")
L("")
L("--- 当前 WeaponAxe ---")
L("   parent = %s   socket = %s" % (
    axe.get_attach_parent().get_name() if axe.get_attach_parent() else None,
    axe.get_attach_socket_name()))
L("   loc=(%.6f, %.6f, %.6f) rot=(%.3f, %.3f, %.3f) scale=(%.6f, %.6f, %.6f)" % (
    cl.x, cl.y, cl.z, cr.pitch, cr.yaw, cr.roll, cs.x, cs.y, cs.z))

if mode() != "apply":
    L("")
    L("==> DRY-RUN，未写资产。确认 F 合理后把 %s 写成 apply 重跑。" % MODE_FILE)
    L("WP51_DRY_RUN_DONE")
    raise SystemExit(0)

# ---------------------------------------------------------------- 备份 + 写
ts = time.strftime("%Y%m%d_%H%M%S")
bd = os.path.join(BACKUP_ROOT, "backup_%s" % ts)
os.makedirs(bd, exist_ok=True)
try:
    shutil.copy2(BP_DISK, os.path.join(bd, "BP_DariusCharacter.uasset"))
    L("已备份 BP -> %s" % bd)
except Exception as ex:
    LW("备份失败: %s —— 中止" % ex)
    raise SystemExit(1)

axe.set_editor_property("relative_location", unreal.Vector(*F_loc))
axe.set_editor_property("relative_rotation", q)
axe.set_editor_property("relative_scale3d", unreal.Vector(*F_scl))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
L("compile + save -> %s" % eal.save_asset(BP, only_if_is_dirty=False))

bp2 = unreal.load_object(None, BP)
axe2 = find_axe(bp2)
l2 = axe2.get_editor_property("relative_location")
r2 = axe2.get_editor_property("relative_rotation")
s2 = axe2.get_editor_property("relative_scale3d")
L("复核: loc=(%.6f, %.6f, %.6f) rot=(%.3f, %.3f, %.3f) scale=(%.6f, %.6f, %.6f)" % (
    l2.x, l2.y, l2.z, r2.pitch, r2.yaw, r2.roll, s2.x, s2.y, s2.z))
L("")
L("=== 还需手工一步 ===")
L("   BP_DariusCharacter -> Components -> CharacterMesh0 -> WeaponAxe -> Details -> Parent Socket")
L("   从 hand_rSocket 改成 %s（无 Python API）" % ANCHOR)
L("   回滚：%s" % bd)
L("WP51_APPLY_DONE")
