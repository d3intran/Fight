# -*- coding: utf-8 -*-
import unreal

mesh = unreal.load_object(None, "/Game/Character/Darius/LOL_Source/SK_LOL_Darius")
skel = unreal.load_object(None, "/Game/Character/Darius/LOL_Source/SK_LOL_Darius_Skeleton")

unreal.log("=== Inspecting SK_LOL_Darius in UE ===")
# Check import data
import_data = mesh.get_editor_property("asset_import_data")
unreal.log(f"Import data: {import_data}")

# Check Retarget Poses on Skeleton
c_skel = unreal.IKRigController.get_controller(unreal.load_object(None, "/Game/Character/Darius/IK/IK_LOL_Darius"))
unreal.log(f"IK_LOL_Darius retarget root: {c_skel.get_retarget_root()}")

# Check bone transform directly from reference skeleton if possible
# Or check bone positions from AnimSequence frame 0 vs SkeletalMesh ref pose
for b in ["Pelvis", "L_Hip", "R_Hip", "L_Shoulder", "R_Shoulder"]:
    t = c_skel.get_ref_pose_transform_of_bone(unreal.Name(b))
    unreal.log(f"  {b}: pos=({t.translation.x:.2f}, {t.translation.y:.2f}, {t.translation.z:.2f}) rot=({t.rotation.rotator()})")
