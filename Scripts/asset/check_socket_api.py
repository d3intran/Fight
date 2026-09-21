# -*- coding: utf-8 -*-
import unreal

mesh = unreal.load_object(None, "/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")
unreal.log("=== StaticMesh Socket API Check ===")
for attr in dir(mesh):
    if "socket" in attr.lower():
        unreal.log(f"mesh.{attr}")

for s in [unreal.StaticMeshEditorSubsystem, unreal.EditorStaticMeshLibrary]:
    if s:
        unreal.log(f"Subsystem {s}:")
        for attr in dir(s):
            if "socket" in attr.lower():
                unreal.log(f"   {attr}")
