# -*- coding: utf-8 -*-
"""audit_rtg_pose_rotations —— 检查当前 Retarget Pose 中各骨骼被施加的旋转偏移"""
import unreal

RTG_PATH = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, RTG_PATH)
c = unreal.IKRetargeterController.get_controller(rtg)

unreal.log("=== Target 骨骼旋转偏移审计 ===")
curr_pose = c.get_current_retarget_pose_name(unreal.RetargetSourceOrTarget.TARGET)
unreal.log(f"Current Target Pose: {curr_pose}")

BONES = [
    "root", "pelvis", "thigh_l", "calf_l", "foot_l", "ball_l",
    "thigh_r", "calf_r", "foot_r", "ball_r",
    "spine_01", "spine_02", "spine_03", "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l",
    "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r"
]

for b in BONES:
    try:
        q = c.get_rotation_offset_for_retarget_pose_bone(unreal.Name(b), unreal.RetargetSourceOrTarget.TARGET)
        euler = q.rotator()
        if abs(euler.pitch) > 0.01 or abs(euler.yaw) > 0.01 or abs(euler.roll) > 0.01:
            unreal.log(f"  {b:<16} : pitch={euler.pitch:.2f}, yaw={euler.yaw:.2f}, roll={euler.roll:.2f}")
    except Exception as ex:
        unreal.log(f"  {b:<16} : error {ex}")

# 检查 Op 栈中 Run IK Rig 是否开启，以及 Goals
unreal.log("\n=== IK Goals 与 Solver 检查 ===")
ik_tgt = c.get_ik_rig(unreal.RetargetSourceOrTarget.TARGET)
c_tgt = unreal.IKRigController.get_controller(ik_tgt)
unreal.log(f"Target Goals: {[g.goal_name for g in c_tgt.get_goals()]}")

ik_src = c.get_ik_rig(unreal.RetargetSourceOrTarget.SOURCE)
c_src = unreal.IKRigController.get_controller(ik_src)
unreal.log(f"Source Goals: {[g.goal_name for g in c_src.get_goals()]}")
