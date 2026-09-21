# -*- coding: utf-8 -*-
import unreal

mesh_path = "/Game/Character/Darius/LOL_Source/SK_LOL_Darius"
mesh = unreal.load_object(None, mesh_path)
unreal.log(f"Loaded mesh: {mesh}")

# Force reimport
reimport_task = unreal.AssetImportTask()
reimport_task.set_editor_property("filename", "E:/UE/Fight/Saved/Retarget/Clean/SK_LOL_Darius_Clean.fbx")
reimport_task.set_editor_property("destination_path", "/Game/Character/Darius/LOL_Source")
reimport_task.set_editor_property("destination_name", "SK_LOL_Darius")
reimport_task.set_editor_property("automated", True)
reimport_task.set_editor_property("replace_existing", True)
reimport_task.set_editor_property("save", True)

# Or use FbxMeshUtils / Reimport
sub = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem) if hasattr(unreal, "SkeletalMeshEditorSubsystem") else None
unreal.log(f"Subsystem: {sub}")

# Let's check reimport method on mesh
at = unreal.AssetToolsHelpers.get_asset_tools()
unreal.log("Attempting reimport...")
at.import_asset_tasks([reimport_task])
unreal.log(f"Imported paths: {reimport_task.get_editor_property('imported_object_paths')}")
