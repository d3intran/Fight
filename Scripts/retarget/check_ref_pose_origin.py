# -*- coding: utf-8 -*-
import unreal

anim = unreal.load_object(None, "/Game/Character/Darius/LOL_Source/A_LOL_Darius_attack1")
track_names = [str(n) for n in unreal.AnimationLibrary.get_animation_track_names(anim)] if hasattr(unreal.AnimationLibrary, "get_animation_track_names") else []
unreal.log(f"Track names: {len(track_names)}")

# Compare bone pose
# In UE, let's see what the ref pose of SK_LOL_Darius is
mesh = unreal.load_object(None, "/Game/Character/Darius/LOL_Source/SK_LOL_Darius")
skel = mesh.get_editor_property("skeleton")

# Check if there is an alternative pose or if the rest pose in FBX was overridden
unreal.log(f"Skeleton: {skel.get_path_name()}")
