# -*- coding: utf-8 -*-
import unreal

for name in ["/Game/Character/Darius/IK/IK_LOL_Darius", "/Game/Character/Darius/IK/IK_Darius"]:
    ik = unreal.load_object(None, name)
    c = unreal.IKRigController.get_controller(ik)
    unreal.log(f"=== {ik.get_name()} Solver 0 ===")
    sc = c.get_solver_controller(0)
    unreal.log(f"Solver class: {sc.get_class().get_name()}")
    s = sc.get_solver()
    unreal.log(f"Solver type: {s.get_class().get_name()}")
    root = s.get_editor_property("root_bone")
    unreal.log(f"Root bone: {root.bone_name if hasattr(root, 'bone_name') else root}")
