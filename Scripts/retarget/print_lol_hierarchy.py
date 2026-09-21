# -*- coding: utf-8 -*-
import unreal

mesh = unreal.load_object(None, "/Game/Character/Darius/LOL_Source/SK_LOL_Darius")
sub = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem) if hasattr(unreal, "SkeletalMeshEditorSubsystem") else None

unreal.log("=== SK_LOL_Darius Bones ===")
# Use AnimationLibrary with an anim sequence
anim = unreal.load_object(None, "/Game/Character/Darius/LOL_Source/A_LOL_Darius_idle1")
bone_names = unreal.AnimationLibrary.get_bone_names(anim)
unreal.log(f"Total bones: {len(bone_names)}")
for b in bone_names:
    p = unreal.AnimationLibrary.find_bone_path_to_skeleton_root(anim, b)
    parent = p[1] if len(p) > 1 else "None"
    unreal.log(f"  {str(b):<25} parent: {str(parent)}")
