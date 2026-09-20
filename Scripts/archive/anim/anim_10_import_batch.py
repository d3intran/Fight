import unreal, os, glob

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if les.is_in_play_in_editor():
    print("!! PIE 运行中，请先结束"); raise SystemExit

DEST = "/Game/Character/Darius/Anims"
skel = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")
files = sorted(glob.glob("E:/UE/Fight/Saved/Retarget/Batch/*.fbx"))
print("待导入:", [os.path.basename(f) for f in files])

at = unreal.AssetToolsHelpers.get_asset_tools()
tasks = []
for f in files:
    name = os.path.splitext(os.path.basename(f))[0]
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
        ui.set_editor_property("anim_sequence_import_data", aid)
    except Exception as e:
        print("  animdata err:", e)
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", f)
    t.set_editor_property("destination_path", DEST)
    t.set_editor_property("destination_name", name)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", True)
    t.set_editor_property("options", ui)
    tasks.append(t)

print("开始导入", len(tasks), "个...")
for t in tasks:
    try:
        at.import_asset_tasks([t])
        print("  OK", os.path.basename(t.get_editor_property("filename")),
              "->", [str(p) for p in t.get_editor_property("imported_object_paths")])
    except Exception as e:
        print("  ERR", os.path.basename(t.get_editor_property("filename")), e)

print()
print("=== Anims 目录最终清单 ===")
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for a in ar.get_assets_by_path(DEST, recursive=True):
    if "AnimSequence" in str(a.asset_class_path.asset_name):
        seq = unreal.load_asset(str(a.package_name))
        ln = round(seq.get_editor_property("sequence_length"), 3) if seq else "?"
        print(f"   {a.asset_name:28s} {ln}s")
print("=== DONE ===")
