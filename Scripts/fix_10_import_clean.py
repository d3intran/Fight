import unreal

FBX = "E:/UE/Fight/Saved/Retarget/SK_Darius_GodKing_NoAxe.fbx"
DEST = "/Game/Character/Darius"
NAME = "SK_Darius_GodKing_NoAxe"

skel = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")
ui = unreal.FbxImportUI()
ui.set_editor_property("import_mesh", True)
ui.set_editor_property("import_animations", False)
ui.set_editor_property("import_as_skeletal", True)
ui.set_editor_property("import_materials", True)
ui.set_editor_property("import_textures", False)
ui.set_editor_property("automated_import_should_detect_type", False)
ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
ui.set_editor_property("skeleton", skel)
try:
    smid = ui.get_editor_property("skeletal_mesh_import_data")
    smid.set_editor_property("import_uniform_scale", 1.0)
    smid.set_editor_property("convert_scene", True)
    smid.set_editor_property("use_full_precision_uvs", True)
    ui.set_editor_property("skeletal_mesh_import_data", smid)
except Exception as e:
    print("smid err:", e)

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

sk = unreal.load_asset(f"{DEST}/{NAME}")
print()
print("=== 新网格 ===", sk)
if sk:
    print("  bone count:", sk.get_editor_property("skeleton") and "n/a")
    print("  materials:")
    for i, m in enumerate(sk.get_editor_property("materials")):
        mi = m.get_editor_property("material_interface")
        print(f"     Slot[{i}] {m.get_editor_property('material_slot_name')} -> {mi.get_path_name() if mi else None}")
    print("  sockets:", [s.get_editor_property("socket_name") for s in sk.get_editor_property("sockets")])

print()
print("=== 对比原网格 ===")
orig = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
print("  orig materials:")
for i, m in enumerate(orig.get_editor_property("materials")):
    mi = m.get_editor_property("material_interface")
    print(f"     Slot[{i}] {m.get_editor_property('material_slot_name')} -> {mi.get_path_name() if mi else None}")
print("  orig sockets:", [s.get_editor_property("socket_name") for s in orig.get_editor_property("sockets")])
print("=== DONE ===")
