import unreal

FBX = "E:/UE/Fight/Saved/Retarget/A_Darius_LOL_Run_TP.fbx"
DEST = "/Game/Character/Darius/Anims"
NAME = "A_Darius_LOL_Run_TP"

skel = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")
print("skeleton:", skel)
if skel:
    print("  bones:", skel.get_editor_property("skeleton") if hasattr(skel, "get_editor_property") else "")

ui = unreal.FbxImportUI()
ui.set_editor_property("import_mesh", False)
ui.set_editor_property("import_animations", True)
ui.set_editor_property("import_as_skeletal", True)
ui.set_editor_property("import_materials", False)
ui.set_editor_property("import_textures", False)
ui.set_editor_property("automated_import_should_detect_type", False)
try:
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
except Exception as e:
    print("mesh_type err:", e)
if skel:
    try:
        ui.set_editor_property("skeleton", skel)
    except Exception as e:
        print("skeleton set err:", e)

try:
    aid = ui.get_editor_property("anim_sequence_import_data")
    aid.set_editor_property("import_uniform_scale", 1.0)
    aid.set_editor_property("convert_scene", True)
    aid.set_editor_property("use_default_sample_rate", False)
    aid.set_editor_property("custom_sample_rate", 30.0)
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

for p in ["/Game/Character/Darius/Anims/A_Darius_LOL_Run_TP"]:
    a = unreal.EditorAssetLibrary.load_asset(p)
    print(p, "->", a)
    if a and isinstance(a, unreal.AnimSequence):
        print("   length:", a.get_editor_property("sequence_length"))
        print("   skeleton:", a.get_editor_property("skeleton"))
        print("   num frames:", a.get_editor_property("number_of_sampled_frames"))
print("=== DONE ===")
