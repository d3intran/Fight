# -*- coding: utf-8 -*-
import unreal

rtg_path = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, rtg_path)
c = unreal.IKRetargeterController.get_controller(rtg)

try:
    unreal.log(f"target_mesh_offset = {rtg.get_editor_property('target_mesh_offset')}")
except Exception as ex:
    unreal.log(f"target_mesh_offset ex: {ex}")

# Retarget Poses
poses = c.get_retarget_poses(unreal.RetargetSourceOrTarget.TARGET)
unreal.log(f"Target Retarget Poses: {[p for p in poses]}")
curr_pose = c.get_current_retarget_pose_name(unreal.RetargetSourceOrTarget.TARGET)
unreal.log(f"Current Target Pose Name: {curr_pose}")

tgt_off = c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.TARGET)
src_off = c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.SOURCE)
unreal.log(f"Target Root Offset: {tgt_off}")
unreal.log(f"Source Root Offset: {src_off}")

ik_src = c.get_ik_rig(unreal.RetargetSourceOrTarget.SOURCE)
ik_tgt = c.get_ik_rig(unreal.RetargetSourceOrTarget.TARGET)
c_src = unreal.IKRigController.get_controller(ik_src)
c_tgt = unreal.IKRigController.get_controller(ik_tgt)
unreal.log(f"IK_LOL_Darius Root Bone: {c_src.get_retarget_root()}")
unreal.log(f"IK_Darius Root Bone: {c_tgt.get_retarget_root()}")
