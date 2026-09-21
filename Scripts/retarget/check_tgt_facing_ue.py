# -*- coding: utf-8 -*-
import unreal

mesh = unreal.load_object(None, "/Game/Character/Darius/SK_Darius_GodKing")
c = unreal.IKRigController.get_controller(unreal.load_object(None, "/Game/Character/Darius/IK/IK_Darius"))

# Check head and pelvis transforms
t_pelvis = c.get_ref_pose_transform_of_bone(unreal.Name("pelvis"))
t_head = c.get_ref_pose_transform_of_bone(unreal.Name("head"))
t_foot_l = c.get_ref_pose_transform_of_bone(unreal.Name("foot_l"))
t_ball_l = c.get_ref_pose_transform_of_bone(unreal.Name("ball_l"))

unreal.log("=== Target IK_Darius Bone Positions in UE ===")
unreal.log(f"pelvis: {t_pelvis.translation}")
unreal.log(f"head:   {t_head.translation}")
unreal.log(f"foot_l: {t_foot_l.translation}")
unreal.log(f"ball_l: {t_ball_l.translation}")
v_foot = t_ball_l.translation - t_foot_l.translation
unreal.log(f"foot_l -> ball_l vector: ({v_foot.x:.2f}, {v_foot.y:.2f}, {v_foot.z:.2f})")
