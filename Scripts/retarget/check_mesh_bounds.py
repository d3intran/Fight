# -*- coding: utf-8 -*-
import unreal

def inspect_mesh_orientation(path):
    mesh = unreal.load_object(None, path)
    unreal.log(f"=== {path} ===")
    bounds = mesh.get_bounds()
    unreal.log(f"  Origin: {bounds.origin}")
    unreal.log(f"  Box Extent: {bounds.box_extent}")

inspect_mesh_orientation("/Game/Character/Darius/SK_Darius_GodKing")
inspect_mesh_orientation("/Game/Character/Darius/LOL_Source/SK_LOL_Darius")
