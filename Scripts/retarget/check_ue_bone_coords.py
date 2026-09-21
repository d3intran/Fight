# -*- coding: utf-8 -*-
import unreal

def get_bone_locs(skel_mesh_path, bone_names):
    mesh = unreal.load_object(None, skel_mesh_path)
    skel = mesh.get_editor_property("skeleton")
    ref_skel = mesh.get_editor_property("skeletal_mesh_component") # wait, let's read ref pose
    # Use SkeletalMesh or AnimationLibrary / Skeleton
    unreal.log(f"=== {skel_mesh_path} ===")
    for b in bone_names:
        # In UE python, we can get ref pose transform from Skeleton or SkeletalMesh
        # Let's inspect how to get ref pose
        pass

# Let's test using unreal.AnimationLibrary or unreal.SkeletalMesh
mesh_lol = unreal.load_object(None, "/Game/Character/Darius/LOL_Source/SK_LOL_Darius")
mesh_tgt = unreal.load_object(None, "/Game/Character/Darius/SK_Darius_GodKing")

unreal.log("Checking LOL bones in UE:")
skel_lol = mesh_lol.get_editor_property("skeleton")
for b in ["Pelvis", "L_Hip", "R_Hip", "L_Shoulder", "R_Shoulder", "L_Hand", "R_Hand", "Weapon"]:
    loc = unreal.AnimationLibrary.get_bone_pose_for_frame(None, b, 0, False) if False else None

