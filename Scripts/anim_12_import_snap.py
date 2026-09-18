import unreal, os, glob

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if les.is_in_play_in_editor():
    print("!! PIE 运行中"); raise SystemExit

DEST = "/Game/Character/Darius/Anims"
skel = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")

# 先探测属性名
probe = unreal.FbxImportUI()
ad = probe.get_editor_property("anim_sequence_import_data")
print("FbxAnimSequenceImportData 可用属性（含 frame/snap）:")
for p in dir(ad):
    if "snap" in p.lower() or "frame" in p.lower() or "rate" in p.lower():
        try:
            print("   ", p, "=", ad.get_editor_property(p))
        except Exception as e:
            print("   ", p, "<err>")
print()

files = ["A_Darius_Attack1_TP.fbx", "A_Darius_RunFast_TP.fbx", "A_Darius_TurnL_TP.fbx", "A_Darius_TurnR_TP.fbx"]
at = unreal.AssetToolsHelpers.get_asset_tools()
for fn in files:
    f = "E:/UE/Fight/Saved/Retarget/Batch/" + fn
    name = os.path.splitext(fn)[0]
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", False)
    ui.set_editor_property("import_animations", True)
    ui.set_editor_property("import_as_skeletal", True)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("automated_import_should_detect_type", False)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    ui.set_editor_property("skeleton", skel)
    aid = ui.get_editor_property("anim_sequence_import_data")
    aid.set_editor_property("import_uniform_scale", 1.0)
    aid.set_editor_property("convert_scene", True)
    aid.set_editor_property("use_default_sample_rate", False)
    aid.set_editor_property("custom_sample_rate", 30.0)
    for p in ["snap_to_closest_frame_boundary", "b_snap_to_closest_frame_boundary"]:
        try:
            aid.set_editor_property(p, True)
            print("  已开启", p)
            break
        except Exception:
            pass
    ui.set_editor_property("anim_sequence_import_data", aid)
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", f)
    t.set_editor_property("destination_path", DEST)
    t.set_editor_property("destination_name", name)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", True)
    t.set_editor_property("options", ui)
    try:
        at.import_asset_tasks([t])
        print("  OK", fn, "->", [str(p) for p in t.get_editor_property("imported_object_paths")])
    except Exception as e:
        print("  ERR", fn, e)
print("=== DONE ===")
