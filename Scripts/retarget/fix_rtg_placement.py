# -*- coding: utf-8 -*-
"""fix_rtg_placement —— 修复 RTG_LOL_To_Darius 中两模型的位置对齐与落地"""
import unreal

rtg_path = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, rtg_path)
if not rtg:
    raise RuntimeError(f"Cannot load {rtg_path}")

c = unreal.IKRetargeterController.get_controller(rtg)
eal = unreal.EditorAssetLibrary

unreal.log("=== 修复前状态 ===")
unreal.log(f"Target Root Offset: {c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.TARGET)}")
unreal.log(f"Target Mesh Offset: {rtg.get_editor_property('target_mesh_offset')}")

# 1. 将 Target Root Offset 归零（让 Darius 从 206cm 的高空落回地面）
c.set_root_offset_in_retarget_pose(unreal.Vector(0.0, 0.0, 0.0), unreal.RetargetSourceOrTarget.TARGET)

# 2. 将 Target Mesh 沿横向偏移 150cm（并排放在旁边）
# 注：在视口中通常沿 X 或 Y 轴并排放置
rtg.set_editor_property("target_mesh_offset", unreal.Vector(150.0, 0.0, 0.0))

# 3. 标记脏并落盘保存
rtg.modify()
ok = eal.save_asset(rtg_path, only_if_is_dirty=False)

unreal.log("=== 修复后状态 ===")
unreal.log(f"Target Root Offset: {c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.TARGET)}")
unreal.log(f"Target Mesh Offset: {rtg.get_editor_property('target_mesh_offset')}")
unreal.log(f"资产存盘结果: {'成功' if ok else '失败'}")
