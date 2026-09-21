# -*- coding: utf-8 -*-
import unreal

ik = unreal.load_object(None, "/Game/Character/Darius/IK/IK_LOL_Darius")
c = unreal.IKRigController.get_controller(ik)

unreal.log("=== IK_LOL_Darius Introspection ===")
unreal.log(f"Skeletal Mesh: {c.get_skeletal_mesh().get_path_name()}")
unreal.log(f"Retarget Root: {c.get_retarget_root()}")

# Check all methods on c
for m in dir(c):
    if "pose" in m.lower():
        unreal.log(f"  pose method: {m}")
