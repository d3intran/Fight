# -*- coding: utf-8 -*-
import unreal

anim = unreal.load_object(None, "/Game/Character/Darius/LOL_Source/A_LOL_Darius_00_BindPose")
unreal.log(f"Anim: {anim.get_path_name()}")
num_frames = anim.get_editor_property("number_of_sampled_keys")
unreal.log(f"Num frames: {num_frames}")

# Check bone pose for frame 0
for b in ["Pelvis", "L_Hip", "R_Hip", "L_Shoulder", "R_Shoulder", "L_Foot", "R_Foot"]:
    t = unreal.AnimationLibrary.get_bone_pose_for_frame(anim, unreal.Name(b), 0, False)
    unreal.log(f"  {b:<12} frame 0 pos: {t.translation}")
