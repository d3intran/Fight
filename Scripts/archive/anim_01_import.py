import unreal

SRC = "E:/UE/Assets/Darius_GodKing_LOL_Original/Animations_GLB/standalone/darius_skin15_run.glb"
DEST = "/Game/Character/Darius/Anims/LOL_Source"

at = unreal.AssetToolsHelpers.get_asset_tools()
task = unreal.AssetImportTask()
task.set_editor_property("filename", SRC)
task.set_editor_property("destination_path", DEST)
task.set_editor_property("destination_name", "LOL_Darius_Run")
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", True)
task.set_editor_property("save", True)
try:
    task.set_editor_property("options", "")
except Exception:
    pass

print("importing...")
try:
    at.import_asset_tasks([task])
    print("import_asset_tasks done")
except Exception as e:
    print("import err:", e)

paths = task.get_editor_property("imported_object_paths") if hasattr(task, "get_editor_property") else []
try:
    print("imported:", [str(p) for p in task.get_editor_property("imported_object_paths")])
except Exception as e:
    print("paths err:", e)

ar = unreal.AssetRegistryHelpers.get_asset_registry()
try:
    assets = ar.get_assets_by_path(DEST, recursive=True)
    print("assets under dest:")
    for a in assets:
        print("   ", a.package_name, a.asset_class_path.asset_name)
except Exception as e:
    print("ar err:", e)
print("=== DONE ===")
