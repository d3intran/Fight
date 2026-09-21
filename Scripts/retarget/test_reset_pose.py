# -*- coding: utf-8 -*-
import unreal

rtg_path = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, rtg_path)
c = unreal.IKRetargeterController.get_controller(rtg)

unreal.log("=== 测试 Reset Retarget Pose ===")
unreal.log(f"Before Reset: {c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.TARGET)}")

c.reset_retarget_pose(unreal.Name("Default Pose"), [], unreal.RetargetSourceOrTarget.TARGET)
unreal.log(f"After Reset: {c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.TARGET)}")

pose_obj = c.get_current_retarget_pose(unreal.RetargetSourceOrTarget.TARGET)
unreal.log(f"Pose obj: {pose_obj}")
for attr in dir(pose_obj):
    if not attr.startswith("_"):
        unreal.log(f"   pose.{attr}")
