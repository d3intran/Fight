# -*- coding: utf-8 -*-
import unreal

RTG_PATH = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, RTG_PATH)
c = unreal.IKRetargeterController.get_controller(rtg)

unreal.log("=== All Retarget Poses in RTG ===")
for side in [unreal.RetargetSourceOrTarget.SOURCE, unreal.RetargetSourceOrTarget.TARGET]:
    s_str = "SOURCE" if side == unreal.RetargetSourceOrTarget.SOURCE else "TARGET"
    poses = c.get_retarget_poses(side)
    unreal.log(f"{s_str} Poses: {[p for p in poses]}")
    curr = c.get_current_retarget_pose_name(side)
    unreal.log(f"{s_str} Current Pose: {curr}")

# Check solvers
for s in [c.get_ik_rig(unreal.RetargetSourceOrTarget.SOURCE), c.get_ik_rig(unreal.RetargetSourceOrTarget.TARGET)]:
    c_ik = unreal.IKRigController.get_controller(s)
    unreal.log(f"IK Rig: {s.get_name()}")
    for attr in dir(c_ik):
        if "solver" in attr.lower() or "goal" in attr.lower():
            unreal.log(f"   {attr}")
