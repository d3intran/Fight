# -*- coding: utf-8 -*-
import unreal

# Search all unreal classes/subsystems for ref pose update methods
for cls in [unreal.AnimationLibrary, unreal.SkeletalMeshEditorSubsystem, unreal.Skeleton, unreal.SkeletalMesh]:
    unreal.log(f"=== {cls.__name__} ===")
    for m in dir(cls):
        if "ref" in m.lower() or "pose" in m.lower():
            unreal.log(f"  {m}")
