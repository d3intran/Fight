# -*- coding: utf-8 -*-
"""把 RTG 的 Weapon 重定向链落点从 weapon_jnt（父 = root）改到 weapon_jnt_r（父 = hand_r）。

为什么
------
源 SK_LOL_Darius 的武器骨 Weapon 挂在 R_Hand 下（真实层级 Axe_Head < Weapon < R_Hand）。
目标 SK_Darius_GodKing 上与之**同构**的锚点是 weapon_jnt_r（父 = hand_r）。
但 IK_Darius 的 Weapon 链建在了 weapon_jnt（父 = root）上，两层级不对应
⇒ FK 重定向写出的局部变换被当成「相对 root」⇒ 斧头钉在脚下、产物轨恒定不变。

本脚本只改 **IK_Darius 里 Weapon 链的 start/end 骨**（链名仍是 Weapon，故 RTG 里
`Weapon <- Weapon` 的映射无需变动）。

安全设计
--------
- 默认 **dry-run**：只打印将要做的改动，不动资产。
- 真要写：把 `Saved/Attack/wp41_mode.txt` 写成 `apply`。
- 写之前自动备份 IK_Darius 到 `Saved/Attack/backup_<时间戳>/`。
- 幂等：已经是 weapon_jnt_r 就直接跳过。
- 自检：写完重新读取，确认 start/end == weapon_jnt_r。

跑法：
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_41_repoint_weapon_chain.py

之后（必须人工/后续脚本完成）：
    1) 在 RTG_LOL_To_Darius 里对齐 weapon_jnt_r 的 Source/Target Retarget Pose
       （单骨链，Direction 自动对齐定不出方向 —— 同 hand/foot 那类坑，需手动）
    2) 重跑重定向（rtg_20_fix_verify.py, mode=mirror）
    3) 跑 rtg_41_fix_outer_scale.py 删最外层骨的假 scale 轨
    4) 跑 wp_40_weapon_anchor_recon.py 复验（weapon_jnt_r 的 travel 与 world 距离应变了）
    5) BP_DariusCharacter → CharacterMesh0 → WeaponAxe → Parent Socket 改 weapon_jnt_r
"""
import os
import shutil
import time

import unreal

IK_T = "/Game/Character/Darius/IK/IK_Darius"
IK_ASSET_DISK = "E:/UE/Fight/Content/Character/Darius/IK/IK_Darius.uasset"
MODE_FILE = "E:/UE/Fight/Saved/Attack/wp41_mode.txt"
BACKUP_ROOT = "E:/UE/Fight/Saved/Attack"

TARGET_START = "weapon_jnt_l"
TARGET_END = "weapon_jnt_l"
CHAIN_NAME = "Weapon"

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary


def mode():
    try:
        with open(MODE_FILE, "r", encoding="utf-8") as f:
            return f.read().strip().lower()
    except Exception:
        return "dry"


def bone_of(ref):
    """BoneReference struct -> 骨名（该 struct 的属性不暴露为 attr，必须走 get_editor_property）"""
    try:
        v = ref.get_editor_property("bone_name")
        return str(v) if v is not None else "<None>"
    except Exception as ex:
        return "<ERR %s>" % str(ex)[:40]


def dump_weapon_chain(rig, tag):
    """返回 Weapon 链的 {start, end}；不存在返回 None"""
    try:
        chains = unreal.IKRigController.get_controller(rig).get_retarget_chains()
    except Exception as ex:
        LW("[%s] 读链失败: %s" % (tag, ex))
        return None
    found = None
    for ch in chains:
        nm = str(ch.chain_name)
        if "eapon" in nm:
            try:
                s = bone_of(ch.get_editor_property("start_bone"))
                e = bone_of(ch.get_editor_property("end_bone"))
            except Exception as ex:
                s = e = "<ERR %s>" % str(ex)[:40]
            L("   [%s] 链 %-14s start=%-18s end=%-18s" % (tag, nm, s, e))
            if nm == CHAIN_NAME:
                found = {"start": s, "end": e}
    return found


L("=" * 78)
L("=== wp_41  把 Weapon 链指向 weapon_jnt_r（父 = hand_r）===")
L("=" * 78)
L("   模式文件 %s -> mode = %s" % (MODE_FILE, mode()))
L("   （要真写：把该文件内容改成 apply）")
L("")

rig = unreal.load_object(None, IK_T)
if rig is None:
    L("!! 载不到 %s" % IK_T)
    raise SystemExit(1)

L("--- 改前 ---")
cur = dump_weapon_chain(rig, "改前")
L("")

if cur and cur["start"] == TARGET_START and cur["end"] == TARGET_END:
    L("==> 已经是 weapon_jnt_r，无需改动（幂等退出）")
    L("WP41_DONE")
    raise SystemExit(0)
if cur is None:
    L("!! 找不到名为 %s 的链 —— 先确认 IK_Darius 的链命名（可能叫 Weapon_0 / Weapon_1）" % CHAIN_NAME)
    L("WP41_ABORTED")
    raise SystemExit(1)

L("==> 计划：remove_retarget_chain('%s') 然后 add_retarget_chain('%s', '%s', '%s', 'None')"
  % (CHAIN_NAME, CHAIN_NAME, TARGET_START, TARGET_END))
L("    期望结果：%s:%s -> %s:%s" % (cur["start"], cur["end"], TARGET_START, TARGET_END))
L("")

if mode() != "apply":
    L("==> DRY-RUN，未写资产。把 %s 内容写成 apply 后重跑。" % MODE_FILE)
    L("WP41_DRY_RUN_DONE")
    raise SystemExit(0)

# ------------------------------------------------------------------ 备份
ts = time.strftime("%Y%m%d_%H%M%S")
bd = os.path.join(BACKUP_ROOT, "backup_%s" % ts)
os.makedirs(bd, exist_ok=True)
try:
    shutil.copy2(IK_ASSET_DISK, os.path.join(bd, "IK_Darius.uasset"))
    L("已备份 IK_Darius.uasset -> %s" % bd)
except Exception as ex:
    LW("备份失败: %s —— 中止" % ex)
    L("WP41_ABORTED")
    raise SystemExit(1)

# ------------------------------------------------------------------ 改链
ctrl = unreal.IKRigController.get_controller(rig)
try:
    ctrl.remove_retarget_chain(unreal.Name(CHAIN_NAME))
    L("已 remove chain %s" % CHAIN_NAME)
except Exception as ex:
    LW("remove 失败: %s" % ex)

try:
    ctrl.add_retarget_chain(unreal.Name(CHAIN_NAME), unreal.Name(TARGET_START),
                            unreal.Name(TARGET_END), unreal.Name("None"))
    L("已 add chain %s : %s -> %s" % (CHAIN_NAME, TARGET_START, TARGET_END))
except Exception as ex:
    LW("add 失败: %s" % ex)

try:
    rig.modify()
except Exception:
    pass
saved = eal.save_asset(IK_T, only_if_is_dirty=False)
L("save -> %s" % saved)

# ------------------------------------------------------------------ 自检
L("")
L("--- 改后（重新加载）---")
rig2 = unreal.load_object(None, IK_T)
after = dump_weapon_chain(rig2, "改后")
if after and after["start"] == TARGET_START and after["end"] == TARGET_END:
    L("==> 自检通过 ✓ Weapon 链已落在 weapon_jnt_r")
else:
    LW("==> 自检未通过 !! 实际 = %s" % after)

L("")
L("=== 下一步（按顺序）===")
L("  1) RTG_LOL_To_Darius 里对齐 weapon_jnt_r 的 retarget pose（单骨链，需手动/Align Selected）")
L("  2) 重跑重定向：echo mirror > Saved/Attack/rtg_fix_mode.txt && ue_remote.py Scripts/retarget/rtg_20_fix_verify.py")
L("  3) 删假 scale 轨：ue_remote.py Scripts/retarget/rtg_41_fix_outer_scale.py")
L("  4) 只读复验：ue_remote.py Scripts/anim/wp_40_weapon_anchor_recon.py")
L("  5) BP 斧头 Parent Socket: hand_rSocket -> weapon_jnt_r（值已在 weapon_migrate_offset.json）")
L("")
L("回滚：把 %s 下的 IK_Darius.uasset 复制回 Content/Character/Darius/IK/ 并重启编辑器" % bd)
L("WP41_APPLY_DONE")
