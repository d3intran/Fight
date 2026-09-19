# -*- coding: utf-8 -*-
"""把 `ik_55` / `ik_56` 对 IK Rig 的改动**全部回滚**到已知良好状态。

## 为什么要回滚
`ik_56` 把链拉长（`LeftFoot` 改成 `foot_l→ball_l`、`Neck` 改成 `neck_01→head`、
`Clavicle` 改成 `clavicle_*→upperarm_*`）之后，`auto_align_all_bones(CHAIN_TO_CHAIN)`
的成绩**没有改善，反而把手臂搞坏了**（手L 90.77→127.85、手R 16.00→45.82）。
原因是 `clavicle_*→upperarm_*` 与 `LeftArm`(`upperarm_l→hand_l`) **在 `upperarm_l` 上重叠**，
同一根骨被两条链各对齐一次 ⇒ 冲突。

⇒ 按 AGENTS.md §0.4「假设被否就立刻换方向，不许硬撑」，回滚。

## 回滚内容
1. 8 处链起止骨改回原值。
2. 删掉 `ik_55` 给源加的 `LeftFoot` / `RightFoot` 两条链。
3. 把目标 `LeftFoot`/`RightFoot` 的映射接回原来的源链 `LeftLeg`/`RightLeg`。
4. 存盘。

字节级备份另存于 `Saved/Backup_ikrig/*.uasset.bak`（需关编辑器才能用）。
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
kc = unreal.IKRigController

IK_SRC = "/Game/Character/Darius/Retarget/IK_LOL_Source"
IK_TGT = "/Game/Character/Darius/Retarget/IK_Darius_Target"
RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"

# 回滚成 (侧, 链名, 起始骨, 结束骨)
REVERT = [
    ("tgt", "LeftFoot",  "ball_l", "ball_l"),
    ("tgt", "RightFoot", "ball_r", "ball_r"),
    ("tgt", "LeftClavicle",  "clavicle_l", "clavicle_l"),
    ("tgt", "RightClavicle", "clavicle_r", "clavicle_r"),
    ("src", "LeftClavicle",  "L_Clavicle", "L_Clavicle"),
    ("src", "RightClavicle", "R_Clavicle", "R_Clavicle"),
    ("tgt", "Neck", "neck_01", "neck_01"),
    ("src", "Neck", "Neck", "Neck"),
]

CTRL = {"tgt": kc.get_controller(eal.load_asset(IK_TGT)),
        "src": kc.get_controller(eal.load_asset(IK_SRC))}
rtg = eal.load_asset(RTG)
ctrl = unreal.IKRetargeterController.get_controller(rtg)

L("################ 1. 链起止骨回滚")
for side, name, s, e in REVERT:
    c = CTRL[side]
    for fn, val, tag in (("set_retarget_chain_start_bone", s, "start"),
                         ("set_retarget_chain_end_bone", e, "end")):
        for arg in (val, unreal.Name(val)):
            try:
                getattr(c, fn)(name, arg)
                break
            except Exception:
                continue
    try:
        L("   %-3s %-16s %s -> %s" % (side, name,
                                     c.get_retarget_chain_start_bone(name),
                                     c.get_retarget_chain_end_bone(name)))
    except Exception as ex:
        LW("   %-3s %-16s 复核失败: %s" % (side, name, str(ex)[:80]))

L("")
L("################ 2. 映射接回原状 + 删掉后加的源链")
for src, tgt in (("LeftLeg", "LeftFoot"), ("RightLeg", "RightFoot")):
    try:
        L("   set_source_chain(%s -> %s) = %s ；读回 %s"
          % (src, tgt, ctrl.set_source_chain(src, tgt), ctrl.get_source_chain(tgt)))
    except Exception as ex:
        LW("   失败: %s" % str(ex)[:110])
cs = CTRL["src"]
for nm in ("LeftFoot", "RightFoot"):
    try:
        L("   remove_retarget_chain(%s) = %s" % (nm, cs.remove_retarget_chain(nm)))
    except Exception as ex:
        LW("   remove %s 失败: %s" % (nm, str(ex)[:110]))
L("   源链数 = %d" % len(cs.get_retarget_chains()))

L("")
L("################ 3. 存盘")
for p in (IK_SRC, IK_TGT, RTG):
    try:
        L("   save %-20s -> %s" % (p.split("/")[-1], eal.save_asset(p, only_if_is_dirty=False)))
    except Exception as ex:
        LW("   save %s 失败: %s" % (p, str(ex)[:110]))
L("=== DONE ===")
