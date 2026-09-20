# -*- coding: utf-8 -*-
"""修正 IK Rig 里**链的起止骨** —— 这才是「上半身 + 手脚对不上」的最终根因。

## 实测（`_probe_spans.py`）
`auto_align_all_bones(CHAIN_TO_CHAIN)` 靠「链里**子骨的方向**」定朝向，所以
**链尾骨**（没有子骨）和**单骨链**里的骨，偏移恒为 0。目标侧实测：

| 链 | 实际跨度 | 后果 |
| :--- | :--- | :--- |
| `Spine` | `spine_01 → spine_03` | `spine_03` 是**链尾** ⇒ 偏移 0 ⇒ 锁骨L/R + 颈 全歪 |
| `Neck` | `neck_01 → neck_01` | **单骨链** ⇒ 尾 ⇒ 偏移 0 |
| `Head` | `Head → Head` | **单骨链** ⇒ 尾 ⇒ 偏移 0 |
| `LeftClavicle` | `clavicle_l → clavicle_l` | **单骨链** ⇒ 尾 ⇒ 偏移 0 |
| **`LeftFoot`** | **`ball_l → ball_l`** | **`foot_l` 根本不在这条链里**！它只在 `LeftLeg`(`thigh_l→foot_l`) 里当**尾** ⇒ 偏移 0 ⇒ 脚掌拧 66.6° |

⇒ 修法：用 `IKRigController.set_retarget_chain_start_bone / end_bone` 把链**拉长**，
让这些骨不再当尾。**两侧都要改**（源侧的 `Neck`/`Head`/`Clavicle` 同样是单骨链）。

## 本脚本改的（保守子集，对应关系干净）
| 侧 | 链 | 现在 | 改成 |
| :--- | :--- | :--- | :--- |
| 目标 | `LeftFoot` / `RightFoot` | `ball_* → ball_*` | `foot_* → ball_*` |
| 源 | `LeftFoot` / `RightFoot` | 已是 `L_Foot→L_Toe` | 不动 |
| 目标 | `LeftClavicle` / `RightClavicle` | `clavicle_* → clavicle_*` | `clavicle_* → upperarm_*` |
| 源 | `LeftClavicle` / `RightClavicle` | `L_Clavicle → L_Clavicle` | `L_Clavicle → L_Shoulder` |
| 目标 | `Neck` | `neck_01 → neck_01` | `neck_01 → head` |
| 源 | `Neck` | `Neck → Neck` | `Neck → Head` |

⚠️ **`Spine` 链故意不动**：把 `spine_01→spine_03` 拉成 `spine_01→neck_01` 会和 `Neck` 链重叠，
重叠骨被两条链各对齐一次，行为未验证 —— 留作下一步单独实验。
⚠️ 改前已备份：`Saved/Backup_ikrig/*.uasset.bak`。
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
kc = unreal.IKRigController

IK_SRC = "/Game/Character/Darius/Retarget/IK_LOL_Source"
IK_TGT = "/Game/Character/Darius/Retarget/IK_Darius_Target"
RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"

# (侧, 链名, 新起始骨, 新结束骨)；None = 不改那一端
FIXES = [
    ("tgt", "LeftFoot",  "foot_l", "ball_l"),
    ("tgt", "RightFoot", "foot_r", "ball_r"),
    ("tgt", "LeftClavicle",  "clavicle_l", "upperarm_l"),
    ("tgt", "RightClavicle", "clavicle_r", "upperarm_r"),
    ("src", "LeftClavicle",  "L_Clavicle", "L_Shoulder"),
    ("src", "RightClavicle", "R_Clavicle", "R_Shoulder"),
    ("tgt", "Neck", "neck_01", "head"),
    ("src", "Neck", "Neck", "Head"),
]

CTRL = {"tgt": kc.get_controller(eal.load_asset(IK_TGT)),
        "src": kc.get_controller(eal.load_asset(IK_SRC))}
L("set_retarget_chain_start_bone: %s" % kc.set_retarget_chain_start_bone.__doc__)
L("set_retarget_chain_end_bone: %s" % kc.set_retarget_chain_end_bone.__doc__)

L("")
L("################ 1. 改前")
for side, name, s, e in FIXES:
    c = CTRL[side]
    try:
        L("   %-3s %-16s %s -> %s" % (side, name,
                                     c.get_retarget_chain_start_bone(name),
                                     c.get_retarget_chain_end_bone(name)))
    except Exception as ex:
        LW("   %-3s %-16s 读失败: %s" % (side, name, str(ex)[:80]))

L("")
L("################ 2. 改")
for side, name, s, e in FIXES:
    c = CTRL[side]
    for fn, val, tag in (("set_retarget_chain_start_bone", s, "start"),
                         ("set_retarget_chain_end_bone", e, "end")):
        if val is None:
            continue
        ok = False
        for arg in (val, unreal.Name(val)):
            try:
                r = getattr(c, fn)(name, arg)
                L("   %-3s %-16s %s = %-14s -> %s" % (side, name, tag, val, r))
                ok = True
                break
            except Exception as ex:
                last = str(ex)[:90]
        if not ok:
            LW("   %-3s %-16s %s 失败: %s" % (side, name, tag, last))

L("")
L("################ 3. 改后复核")
for side, name, s, e in FIXES:
    c = CTRL[side]
    try:
        L("   %-3s %-16s %s -> %s" % (side, name,
                                     c.get_retarget_chain_start_bone(name),
                                     c.get_retarget_chain_end_bone(name)))
    except Exception as ex:
        LW("   %-3s %-16s 读失败: %s" % (side, name, str(ex)[:80]))

L("")
L("################ 4. 存盘")
for p in (IK_SRC, IK_TGT, RTG):
    try:
        L("   save %-20s -> %s" % (p.split("/")[-1], eal.save_asset(p, only_if_is_dirty=False)))
    except Exception as ex:
        LW("   save %s 失败: %s" % (p, str(ex)[:110]))
L("=== DONE ===")
