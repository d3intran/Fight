# -*- coding: utf-8 -*-
"""rtg_51_add_middle_chains —— 给源 rig 补上缺失的中指链（L/R_Middle1 -> Middle2），并对照目标列出缺口"""

import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

SRC_RIG = "/Game/Character/Darius/IK/IK_LOL_Darius"
TGT_RIG = "/Game/Character/Darius/IK/IK_Darius"
RTG = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"

WANT = [("LeftMiddle", "L_Middle1", "L_Middle2"), ("RightMiddle", "R_Middle1", "R_Middle2")]

rs = unreal.load_object(None, SRC_RIG)
rc = unreal.IKRigController.get_controller(rs)
existing = {str(ch.chain_name) for ch in rc.get_retarget_chains()}
L(f"[MC] 源 rig 现有链 {len(existing)} 条")

# 先确认源的骨架里确实有这两根骨
anim = unreal.load_object(None, "/Game/Character/Darius/LOL_Source/A_LOL_Darius_idle1")
names = [str(t).lower() for t in unreal.AnimationLibrary.get_animation_track_names(anim)]
L(f"[MC] 源骨架骨数 {len(names)}；含 l_middle1/2 = {'l_middle1' in names and 'l_middle2' in names}；"
  f"含 r_middle1/2 = {'r_middle1' in names and 'r_middle2' in names}")

added = 0
for name, sb, eb in WANT:
    if name in existing:
        L(f"[MC]   {name} 已存在，跳过")
        continue
    try:
        ok = rc.add_retarget_chain(unreal.Name(name), unreal.Name(sb), unreal.Name(eb), unreal.Name("None"))
        L(f"[MC]   add_retarget_chain({name}, {sb} -> {eb}) = {ok}")
        added += 1
    except Exception as ex:
        LW(f"[MC]   add {name} err {str(ex)[:120]}")

if added:
    rs.modify()
    L(f"[MC] save IK_LOL_Darius = {eal.save_asset(SRC_RIG, only_if_is_dirty=False)}")

# 复读
rc2 = unreal.IKRigController.get_controller(unreal.load_object(None, SRC_RIG))
cur = {str(ch.chain_name) for ch in rc2.get_retarget_chains()}
L(f"[MC] 源 rig 现在 {len(cur)} 条链；Middle 链 = {[c for c in cur if 'Middle' in c]}")

# 目标链 vs 源链的缺口（按名字）
tgt = {str(ch.chain_name) for ch in unreal.IKRigController.get_controller(
    unreal.load_object(None, TGT_RIG)).get_retarget_chains()}
c = unreal.IKRetargeterController.get_controller(unreal.load_object(None, RTG))
L("[MC] 目标链映射现状（未映射的 = 缺口）：")
for name in sorted(tgt):
    try:
        src = str(c.get_source_chain(unreal.Name(name)))
    except Exception:
        src = "ERR"
    mark = "  <== 缺" if src == "None" else ""
    L(f"[MC]   {name:<24} <- {src}{mark}")
L("MC_DONE")
