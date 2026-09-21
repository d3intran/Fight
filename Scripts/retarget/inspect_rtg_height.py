# -*- coding: utf-8 -*-
"""inspect_rtg_height —— 检查两个模型在 RTG 里的世界高度与脚底位置"""
import unreal

rtg_path = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, rtg_path)
c = unreal.IKRetargeterController.get_controller(rtg)

src_mesh = c.get_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE)
tgt_mesh = c.get_preview_mesh(unreal.RetargetSourceOrTarget.TARGET)

unreal.log(f"Source Mesh: {src_mesh.get_name()}")
b_src = src_mesh.get_bounds()
unreal.log(f"  Bounds Box: extent={b_src.box_extent}, origin={b_src.origin}")
unreal.log(f"  Z range: [{b_src.origin.z - b_src.box_extent.z:.1f} .. {b_src.origin.z + b_src.box_extent.z:.1f}]")

unreal.log(f"Target Mesh: {tgt_mesh.get_name()}")
b_tgt = tgt_mesh.get_bounds()
unreal.log(f"  Bounds Box: extent={b_tgt.box_extent}, origin={b_tgt.origin}")
unreal.log(f"  Z range: [{b_tgt.origin.z - b_tgt.box_extent.z:.1f} .. {b_tgt.origin.z + b_tgt.box_extent.z:.1f}]")

# 检查控制器中的 Retarget Pose
curr_pose = c.get_current_retarget_pose_name(unreal.RetargetSourceOrTarget.TARGET)
unreal.log(f"Target Current Pose: {curr_pose}")
off = c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.TARGET)
unreal.log(f"Target Root Offset in pose: {off}")

# 检查 Op Stack (Pelvis Motion 等)
ops_count = c.get_num_retarget_ops()
unreal.log(f"Ops count: {ops_count}")
for i in range(ops_count):
    unreal.log(f"  Op {i}: enabled={c.get_retarget_op_enabled(i)}")
