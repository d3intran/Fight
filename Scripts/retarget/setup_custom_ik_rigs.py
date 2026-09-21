# -*- coding: utf-8 -*-
"""setup_custom_ik_rigs —— 规范化配置 IK_LOL_Darius、IK_Darius 与 RTG_LOL_To_Darius 链映射"""
import unreal

eal = unreal.EditorAssetLibrary

IK_LOL_PATH = "/Game/Character/Darius/IK/IK_LOL_Darius"
IK_TGT_PATH = "/Game/Character/Darius/IK/IK_Darius"
RTG_PATH = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"

# 1. 规范化配置 IK_LOL_Darius
unreal.log("=== 1. 规范化配置 IK_LOL_Darius ===")
ik_lol = unreal.load_object(None, IK_LOL_PATH)
c_lol = unreal.IKRigController.get_controller(ik_lol)

c_lol.set_retarget_root(unreal.Name("Pelvis"))

# 定义 LOL Source 的骨骼链（注意：明确添加 LeftFoot / RightFoot，杜绝被手指误匹配！）
LOL_CHAINS = [
    ("Spine", "Spine1", "Spine2"),
    ("Neck", "Neck", "Neck"),
    ("Head", "Head", "Head"),
    ("LeftLeg", "L_Hip", "L_Foot"),
    ("LeftFoot", "L_Toe", "L_Toe"),
    ("RightLeg", "R_Hip", "R_Foot"),
    ("RightFoot", "R_Toe", "R_Toe"),
    ("LeftClavicle", "L_Clavicle", "L_Clavicle"),
    ("LeftArm", "L_Shoulder", "L_Hand"),
    ("RightClavicle", "R_Clavicle", "R_Clavicle"),
    ("RightArm", "R_Shoulder", "R_Hand"),
    ("LeftThumb", "L_Thumb1", "L_Thumb2"),
    ("LeftIndex", "L_Index1", "L_Index2"),
    ("LeftRing", "L_Ring1", "L_Ring2"),
    ("LeftPinky", "L_Pinky1", "L_Pinky2"),
    ("RightThumb", "R_Thumb1", "R_Thumb2"),
    ("RightIndex", "R_Index1", "R_Index2"),
    ("RightRing", "R_Ring1", "R_Ring2"),
    ("RightPinky", "R_Pinky1", "R_Pinky2"),
    ("Weapon", "Weapon", "Weapon"),
]

existing_lol_chains = {ch.chain_name: ch for ch in c_lol.get_retarget_chains()}
for ch_name, s_bone, e_bone in LOL_CHAINS:
    if ch_name in existing_lol_chains:
        c_lol.set_retarget_chain_start_bone(unreal.Name(ch_name), unreal.Name(s_bone))
        c_lol.set_retarget_chain_end_bone(unreal.Name(ch_name), unreal.Name(e_bone))
    else:
        c_lol.add_retarget_chain(unreal.Name(ch_name), unreal.Name(s_bone), unreal.Name(e_bone), unreal.Name("None"))
        unreal.log(f"  IK_LOL_Darius 添加链: {ch_name} -> ({s_bone} .. {e_bone})")

ik_lol.modify()
eal.save_asset(IK_LOL_PATH, only_if_is_dirty=False)
unreal.log("IK_LOL_Darius 配置保存成功")

# 2. 检查 Target IK_Darius 武器链
unreal.log("\n=== 2. 检查 Target IK_Darius 武器链 ===")
ik_tgt = unreal.load_object(None, IK_TGT_PATH)
c_tgt = unreal.IKRigController.get_controller(ik_tgt)

existing_tgt_chains = {ch.chain_name: ch for ch in c_tgt.get_retarget_chains()}
if "Weapon" not in existing_tgt_chains:
    try:
        c_tgt.add_retarget_chain(unreal.Name("Weapon"), unreal.Name("weapon_jnt"), unreal.Name("weapon_jnt"), unreal.Name("None"))
        unreal.log("  IK_Darius 添加 Weapon 链 -> (weapon_jnt)")
        ik_tgt.modify()
        eal.save_asset(IK_TGT_PATH, only_if_is_dirty=False)
    except Exception as ex:
        unreal.log(f"  添加 Weapon 链 note: {ex}")

# 3. 严格 1:1 配置 RTG_LOL_To_Darius 链映射
unreal.log("\n=== 3. 配置 RTG_LOL_To_Darius 链映射 ===")
rtg = unreal.load_object(None, RTG_PATH)
c_rtg = unreal.IKRetargeterController.get_controller(rtg)

# 清理重设 Retarget Pose 偏移
c_rtg.reset_retarget_pose(unreal.Name("Default Pose"), [], unreal.RetargetSourceOrTarget.TARGET)
c_rtg.reset_retarget_pose(unreal.Name("Default Pose"), [], unreal.RetargetSourceOrTarget.SOURCE)
c_rtg.set_root_offset_in_retarget_pose(unreal.Vector(0.0, 0.0, 0.0), unreal.RetargetSourceOrTarget.TARGET)

# 先将所有 Target 链的 Source 链清空为 None，杜绝任何模糊匹配脏数据
for ch in c_tgt.get_retarget_chains():
    c_rtg.set_source_chain(unreal.Name("None"), ch.chain_name)

EXPLICIT_MAPPINGS = [
    ("Spine", "Spine"),
    ("Neck", "Neck"),
    ("Head", "Head"),
    ("LeftLeg", "LeftLeg"),
    ("LeftFoot", "LeftFoot"),
    ("RightLeg", "RightLeg"),
    ("RightFoot", "RightFoot"),
    ("LeftClavicle", "LeftClavicle"),
    ("LeftArm", "LeftArm"),
    ("RightClavicle", "RightClavicle"),
    ("RightArm", "RightArm"),
    ("LeftThumb", "LeftThumb"),
    ("LeftIndex", "LeftIndex"),
    ("LeftRing", "LeftRing"),
    ("LeftPinky", "LeftPinky"),
    ("RightThumb", "RightThumb"),
    ("RightIndex", "RightIndex"),
    ("RightRing", "RightRing"),
    ("RightPinky", "RightPinky"),
    ("Weapon", "Weapon"),
]

tgt_chain_names = {str(ch.chain_name) for ch in c_tgt.get_retarget_chains()}
src_chain_names = {str(ch.chain_name) for ch in c_lol.get_retarget_chains()}

mapped_count = 0
for tgt_ch, src_ch in EXPLICIT_MAPPINGS:
    if tgt_ch in tgt_chain_names and src_ch in src_chain_names:
        # 注意：API 参数顺序为 (source_chain_name, target_chain_name)
        ok = c_rtg.set_source_chain(unreal.Name(src_ch), unreal.Name(tgt_ch))
        if ok:
            mapped_count += 1
            unreal.log(f"  映射成功: Target[{tgt_ch:<18}] <- Source[{src_ch:<18}]")
        else:
            unreal.log(f"  映射失败: Target[{tgt_ch:<18}] <- Source[{src_ch:<18}]")

unreal.log(f"显式映射完成: {mapped_count} 条有效链（已彻底清除手指导向脚的脏映射）")

rtg.modify()
eal.save_asset(RTG_PATH, only_if_is_dirty=False)
unreal.log("RTG_LOL_To_Darius 保存成功！")
