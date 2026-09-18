import unreal

FBX = "E:/UE/Fight/Saved/Retarget/A_Darius_LOL_Run_TP.fbx"
DEST = "/Game/Character/Darius/Anims"
NAME = "A_Darius_LOL_Run_TP"

# 1. 清理上一次失败导入产生的冗余资产
for p in ["/Game/Character/Darius/Anims/A_Darius_LOL_Run_TP_Skeleton",
          "/Game/Character/Darius/Anims/LOL_Source"]:
    if unreal.EditorAssetLibrary.does_asset_exist(p):
        print("deleting", p, "->", unreal.EditorAssetLibrary.delete_asset(p))
    elif unreal.EditorAssetLibrary.does_directory_exist(p):
        print("deleting dir", p, "->", unreal.EditorAssetLibrary.delete_directory(p))

skel = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")
print("target skeleton:", skel)

ui = unreal.FbxImportUI()
ui.set_editor_property("import_mesh", False)
ui.set_editor_property("import_animations", True)
ui.set_editor_property("import_as_skeletal", True)
ui.set_editor_property("import_materials", False)
ui.set_editor_property("import_textures", False)
ui.set_editor_property("automated_import_should_detect_type", False)
ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
ui.set_editor_property("skeleton", skel)
try:
    aid = ui.get_editor_property("anim_sequence_import_data")
    aid.set_editor_property("import_uniform_scale", 1.0)
    aid.set_editor_property("convert_scene", True)
    aid.set_editor_property("use_default_sample_rate", False)
    aid.set_editor_property("custom_sample_rate", 30.0)
    aid.set_editor_property("delete_existing_custom_attribute_tracks", False)
    ui.set_editor_property("anim_sequence_import_data", aid)
except Exception as e:
    print("animdata err:", e)

task = unreal.AssetImportTask()
task.set_editor_property("filename", FBX)
task.set_editor_property("destination_path", DEST)
task.set_editor_property("destination_name", NAME)
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", True)
task.set_editor_property("save", True)
task.set_editor_property("options", ui)

at = unreal.AssetToolsHelpers.get_asset_tools()
print("importing...")
try:
    at.import_asset_tasks([task])
    print("imported:", [str(p) for p in task.get_editor_property("imported_object_paths")])
except Exception as e:
    print("IMPORT ERR:", e)

print()
print("=== Anims 目录 ===")
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for a in ar.get_assets_by_path(DEST, recursive=True):
    print("  ", a.package_name, "|", a.asset_class_path.asset_name)

for p in [f"{DEST}/{NAME}", f"{DEST}/A_Darius_LOL_Run_TP_Anim"]:
    a = unreal.load_asset(p)
    print(p, "->", a)
    if a and a.get_class().get_name() == "AnimSequence":
        print("   length:", a.get_editor_property("sequence_length"))
        print("   skeleton:", a.get_editor_property("skeleton"))
        print("   frames:", a.get_editor_property("number_of_sampled_frames"))
print("=== DONE ===")
