# -*- coding: utf-8 -*-
import unreal

rtg_path = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, rtg_path)
c = unreal.IKRetargeterController.get_controller(rtg)

unreal.log("=== RTG_LOL_To_Darius 最终状态审计 ===")
unreal.log(f"Target Mesh Offset: {rtg.get_editor_property('target_mesh_offset')}")
unreal.log(f"Target Root Offset: {c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.TARGET)}")
unreal.log(f"Source Root Offset: {c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.SOURCE)}")
unreal.log(f"Total Ops: {c.get_num_retarget_ops()}")
for i in range(c.get_num_retarget_ops()):
    unreal.log(f"  Op [{i}] {c.get_op_name(i)}: enabled={c.get_retarget_op_enabled(i)}")

chains = ["Spine", "Head", "LeftArm", "RightArm", "LeftLeg", "RightLeg"]
unreal.log("=== 核心链映射检查 ===")
for ch in chains:
    unreal.log(f"  {ch:<12} -> {c.get_source_chain(unreal.Name(ch))}")
