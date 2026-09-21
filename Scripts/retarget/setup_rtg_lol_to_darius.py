# -*- coding: utf-8 -*-
"""setup_rtg_lol_to_darius —— 修复 IK_LOL_Darius 骨骼链，并将 RTG 中 Darius 降到地面并排放置"""
import unreal

eal = unreal.EditorAssetLibrary

IK_LOL_PATH = "/Game/Character/Darius/IK/IK_LOL_Darius"
RTG_PATH = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"

# 1. 修复 IK_LOL_Darius 骨骼链
unreal.log("=== 1. 修复 IK_LOL_Darius 骨骼链 ===")
ik_lol = unreal.load_object(None, IK_LOL_PATH)
c_lol = unreal.IKRigController.get_controller(ik_lol)

# 设置 Retarget Root 为 Pelvis
c_lol.set_retarget_root(unreal.Name("Pelvis"))
unreal.log("Retarget Root 设为 Pelvis")

# 清理重设关键链
CHAIN_CONFIGS = [
    ("Spine", "Spine1", "Spine2"),
    ("Neck", "Neck", "Neck"),
    ("Head", "Head", "Head"),
    ("LeftClavicle", "L_Clavicle", "L_Clavicle"),
    ("LeftArm", "L_Shoulder", "L_Hand"),
    ("RightClavicle", "R_Clavicle", "R_Clavicle"),
    ("RightArm", "R_Shoulder", "R_Hand"),
    ("LeftLeg", "L_Hip", "L_Foot"),
    ("RightLeg", "R_Hip", "R_Foot"),
    ("LeftThumb", "L_Thumb1", "L_Thumb2"),
    ("LeftIndex", "L_Index1", "L_Index2"),
    ("LeftRing", "L_Ring1", "L_Ring2"),
    ("LeftPinky", "L_Pinky1", "L_Pinky2"),
    ("RightThumb", "R_Thumb1", "R_Thumb2"),
    ("RightIndex", "R_Index1", "R_Index2"),
    ("RightRing", "R_Ring1", "R_Ring2"),
    ("RightPinky", "R_Pinky1", "R_Pinky2"),
]

for ch_name, s_bone, e_bone in CHAIN_CONFIGS:
    existing = None
    for ch in c_lol.get_retarget_chains():
        if ch.chain_name == ch_name:
            existing = ch
            break
    if existing:
        c_lol.set_retarget_chain_start_bone(unreal.Name(ch_name), unreal.Name(s_bone))
        c_lol.set_retarget_chain_end_bone(unreal.Name(ch_name), unreal.Name(e_bone))
        unreal.log(f"更新链: {ch_name} -> {s_bone} .. {e_bone}")
    else:
        c_lol.add_retarget_chain(unreal.Name(ch_name), unreal.Name(s_bone), unreal.Name(e_bone), unreal.Name("None"))
        unreal.log(f"新建链: {ch_name} -> {s_bone} .. {e_bone}")

ik_lol.modify()
eal.save_asset(IK_LOL_PATH, only_if_is_dirty=False)
unreal.log("IK_LOL_Darius 保存成功")

# 2. 修复 RTG_LOL_To_Darius 空间摆放与高度
unreal.log("\n=== 2. 修复 RTG_LOL_To_Darius 空间摆放与高度 ===")
rtg = unreal.load_object(None, RTG_PATH)
c_rtg = unreal.IKRetargeterController.get_controller(rtg)

# (1) 根骨位移重置归零：将 Darius 从 206cm 高空落回地面
c_rtg.reset_retarget_pose(unreal.Name("Default Pose"), [], unreal.RetargetSourceOrTarget.TARGET)
c_rtg.set_root_offset_in_retarget_pose(unreal.Vector(0.0, 0.0, 0.0), unreal.RetargetSourceOrTarget.TARGET)
unreal.log("Target Root Offset 已重置归零 (Z=0)")

# (2) 水平横向偏移 150cm：并排放置在旁边做对比
rtg.set_editor_property("target_mesh_offset", unreal.Vector(150.0, 0.0, 0.0))
unreal.log("Target Mesh Offset 已设为 (150.0, 0.0, 0.0)")

# (3) 自动映射链 (Auto Map Chains)
# 遍历 Target 链，按名字匹配 Source 链
ik_tgt = c_rtg.get_ik_rig(unreal.RetargetSourceOrTarget.TARGET)
c_tgt = unreal.IKRigController.get_controller(ik_tgt)
tgt_chains = [ch.chain_name for ch in c_tgt.get_retarget_chains()]
src_chains = [ch.chain_name for ch in c_lol.get_retarget_chains()]

mapped = 0
for tc in tgt_chains:
    if tc in src_chains:
        c_rtg.set_source_chain(tc, tc)
        mapped += 1
        unreal.log(f"  映射链: {tc} -> {tc}")

unreal.log(f"自动映射骨骼链完成: {mapped} 条")

# (4) 添加默认 Ops 栈（若为空）
if c_rtg.get_num_retarget_ops() == 0:
    try:
        # 添加标准 Op 栈
        c_rtg.add_retarget_op(unreal.IKRetargetOpType.PELVIS_MOTION if hasattr(unreal, "IKRetargetOpType") else 0)
    except Exception as ex:
        unreal.log(f"add_retarget_op note: {ex}")

rtg.modify()
eal.save_asset(RTG_PATH, only_if_is_dirty=False)
unreal.log("RTG_LOL_To_Darius 修复并落盘保存成功！")
