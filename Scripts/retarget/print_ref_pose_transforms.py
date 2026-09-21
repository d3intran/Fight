# -*- coding: utf-8 -*-
import unreal

IK_TGT_PATH = "/Game/Character/Darius/IK/IK_Darius"
IK_SRC_PATH = "/Game/Character/Darius/IK/IK_LOL_Darius"

c_tgt = unreal.IKRigController.get_controller(unreal.load_object(None, IK_TGT_PATH))
c_src = unreal.IKRigController.get_controller(unreal.load_object(None, IK_SRC_PATH))

unreal.log("=== Target IK_Darius Ref Pose Transforms ===")
for b in ["pelvis", "thigh_l", "calf_l", "foot_l", "thigh_r", "calf_r", "foot_r", "upperarm_l", "hand_l", "upperarm_r", "hand_r"]:
    try:
        t = c_tgt.get_ref_pose_transform_of_bone(unreal.Name(b))
        unreal.log(f"  {b:<12} loc=({t.translation.x:.1f}, {t.translation.y:.1f}, {t.translation.z:.1f})")
    except Exception as ex:
        unreal.log(f"  {b:<12} error {ex}")

unreal.log("\n=== Source IK_LOL_Darius Ref Pose Transforms ===")
for b in ["Pelvis", "L_Hip", "L_KneeLower", "L_Foot", "R_Hip", "R_KneeLower", "R_Foot", "L_Shoulder", "L_Hand", "R_Shoulder", "R_Hand", "Weapon"]:
    try:
        t = c_src.get_ref_pose_transform_of_bone(unreal.Name(b))
        unreal.log(f"  {b:<12} loc=({t.translation.x:.1f}, {t.translation.y:.1f}, {t.translation.z:.1f})")
    except Exception as ex:
        unreal.log(f"  {b:<12} error {ex}")
