# -*- coding: utf-8 -*-
import unreal

mesh = unreal.load_object(None, "/Game/Character/Darius/LOL_Source/SK_LOL_Darius")
import_data = mesh.get_editor_property("asset_import_data")
unreal.log(f"Import data class: {import_data.get_class().get_name()}")
# Check if it has import_rotation
for p in ["import_rotation", "yaw", "rotation"]:
    try:
        val = import_data.get_editor_property(p)
        unreal.log(f"  {p}: {val}")
    except Exception as ex:
        pass
