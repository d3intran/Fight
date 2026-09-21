# -*- coding: utf-8 -*-
import unreal

c = unreal.IKRigController.get_controller(unreal.load_object(None, "/Game/Character/Darius/IK/IK_LOL_Darius"))

t_foot_l = c.get_ref_pose_transform_of_bone(unreal.Name("L_Foot"))
t_toe_l = c.get_ref_pose_transform_of_bone(unreal.Name("L_Toe"))
t_foot_r = c.get_ref_pose_transform_of_bone(unreal.Name("R_Foot"))
t_toe_r = c.get_ref_pose_transform_of_bone(unreal.Name("R_Toe"))

unreal.log("=== Source IK_LOL_Darius Bone Positions in UE ===")
unreal.log(f"L_Foot: {t_foot_l.translation}")
unreal.log(f"L_Toe:  {t_toe_l.translation}")
v_l = t_toe_l.translation - t_foot_l.translation
unreal.log(f"L_Foot -> L_Toe vector: ({v_l.x:.2f}, {v_l.y:.2f}, {v_l.z:.2f})")

unreal.log(f"R_Foot: {t_foot_r.translation}")
unreal.log(f"R_Toe:  {t_toe_r.translation}")
v_r = t_toe_r.translation - t_foot_r.translation
unreal.log(f"R_Foot -> R_Toe vector: ({v_r.x:.2f}, {v_r.y:.2f}, {v_r.z:.2f})")
