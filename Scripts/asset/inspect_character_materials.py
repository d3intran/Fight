# -*- coding: utf-8 -*-
import unreal

mesh = unreal.load_object(None, "/Game/Character/Darius/SK_Darius_GodKing")
unreal.log(f"=== {mesh.get_name()} 材质槽清单 ===")
for i, m in enumerate(mesh.materials):
    mat_interface = m.material_interface
    slot_name = m.material_slot_name
    unreal.log(f"Slot {i}: [{slot_name}] -> {mat_interface.get_name() if mat_interface else 'None'}")
