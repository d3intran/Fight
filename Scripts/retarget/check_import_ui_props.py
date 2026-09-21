# -*- coding: utf-8 -*-
import unreal

ui = unreal.FbxImportUI()
smd = ui.get_editor_property("skeletal_mesh_import_data")
unreal.log("=== SkeletalMeshImportData ===")
for p in dir(smd):
    if not p.startswith("_"):
        unreal.log(f"  {p}")
