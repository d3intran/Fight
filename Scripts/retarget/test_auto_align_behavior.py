# -*- coding: utf-8 -*-
"""test_auto_align_behavior —— 测试并测量 auto_align_all_bones 导致的骨骼旋转"""
import unreal

rtg = unreal.load_object(None, "/Game/Character/Darius/IK/RTG_LOL_To_Darius")
c = unreal.IKRetargeterController.get_controller(rtg)

unreal.log("=== 执行 auto_align_all_bones(TARGET) ===")
c.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)

LEGS = ["thigh_l", "calf_l", "foot_l", "thigh_r", "calf_r", "foot_r"]
unreal.log("对齐后腿部骨骼旋转偏移:")
for b in LEGS:
    q = c.get_rotation_offset_for_retarget_pose_bone(unreal.Name(b), unreal.RetargetSourceOrTarget.TARGET)
    e = q.rotator()
    unreal.log(f"  {b:<10}: pitch={e.pitch:7.2f}, yaw={e.yaw:7.2f}, roll={e.roll:7.2f}")
