import unreal

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if les.is_in_play_in_editor():
    les.editor_request_end_play()
    print("!! PIE 仍在运行，已请求结束，请重跑本脚本")
    raise SystemExit

# 清理中间产物
if unreal.EditorAssetLibrary.does_asset_exist("/Game/Character/Darius/SK_Darius_GodKing_NoAxe"):
    print("删除中间资产:", unreal.EditorAssetLibrary.delete_asset("/Game/Character/Darius/SK_Darius_GodKing_NoAxe"))

FBX = "E:/UE/Fight/Saved/Retarget/SK_Darius_GodKing_Clean.fbx"
skel = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")

ui = unreal.FbxImportUI()
ui.set_editor_property("import_mesh", True)
ui.set_editor_property("import_animations", False)
ui.set_editor_property("import_as_skeletal", True)
ui.set_editor_property("import_materials", False)   # 保留资产上已有的材质覆盖
ui.set_editor_property("import_textures", False)
ui.set_editor_property("automated_import_should_detect_type", False)
ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
ui.set_editor_property("skeleton", skel)
try:
    smid = ui.get_editor_property("skeletal_mesh_import_data")
    smid.set_editor_property("import_uniform_scale", 1.0)
    smid.set_editor_property("convert_scene", True)
    ui.set_editor_property("skeletal_mesh_import_data", smid)
except Exception as e:
    print("smid err:", e)

task = unreal.AssetImportTask()
task.set_editor_property("filename", FBX)
task.set_editor_property("destination_path", "/Game/Character/Darius")
task.set_editor_property("destination_name", "SK_Darius_GodKing")
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", True)
task.set_editor_property("save", True)
task.set_editor_property("options", ui)

at = unreal.AssetToolsHelperr.get_asset_tools() if hasattr(unreal, "AssetToolsHelperr") else unreal.AssetToolsHelpers.get_asset_tools()
print("re-importing over SK_Darius_GodKing ...")
try:
    at.import_asset_tasks([task])
    print("imported:", [str(p) for p in task.get_editor_property("imported_object_paths")])
except Exception as e:
    print("IMPORT ERR:", e)

sk = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
print()
print("=== 替换后 ===", sk)
if sk:
    mats = sk.get_editor_property("materials")
    print("  槽位数量:", len(mats))
    for i, m in enumerate(mats):
        mi = m.get_editor_property("material_interface")
        print(f"     Slot[{i}] {m.get_editor_property('material_slot_name')} -> {mi.get_path_name() if mi else None}")
    b = sk.get_bounds()
    print("  bounds:", b)
    # 重建 hand_rSocket
    s = sk.find_socket(unreal.Name("hand_rSocket"))
    if s is None:
        new_sock = unreal.SkeletalMeshSocket()
        new_sock.set_editor_property("socket_name", "hand_rSocket")
        new_sock.set_editor_property("bone_name", "hand_r")
        new_sock.set_editor_property("relative_location", unreal.Vector(0, 0, 0))
        new_sock.set_editor_property("relative_rotation", unreal.Rotator(90, 0, 0))
        new_sock.set_editor_property("relative_scale", unreal.Vector(0.01, 0.01, 0.01))
        sk.add_socket(new_sock, True)
        print("  已重建 hand_rSocket")
    s = sk.find_socket(unreal.Name("hand_rSocket"))
    print("  hand_rSocket:", s)
    if s:
        print("     bone:", s.get_editor_property("bone_name"),
              "relRot:", s.get_editor_property("relative_rotation"),
              "relScale:", s.get_editor_property("relative_scale"))
    print("  保存:", unreal.EditorAssetLibrary.save_loaded_asset(sk))
print("=== DONE ===")
