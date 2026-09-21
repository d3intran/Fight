# -*- coding: utf-8 -*-
import unreal

skel = unreal.load_object(None, "/Game/Character/Darius/LOL_Source/SK_LOL_Darius_Skeleton")
unreal.log(f"Skeleton: {skel}")
unreal.log(f"Skeleton is valid: {skel is not None}")

# Check referencers of SK_LOL_Darius_Skeleton
eal = unreal.EditorAssetLibrary
refs = eal.find_package_referencers_for_asset("/Game/Character/Darius/LOL_Source/SK_LOL_Darius_Skeleton")
unreal.log(f"Referencers of Skeleton ({len(refs)}):")
for r in refs:
    unreal.log(f"  {r}")
