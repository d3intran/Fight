# -*- coding: utf-8 -*-
import unreal

SRC_FBX = "E:/UE/Fight/Saved/Retarget/Clean/SK_LOL_Darius_Clean.fbx"
DEST = "/Game/Character/Darius/Test_Import"
DEST_NAME = "SK_Test_Darius"

eal = unreal.EditorAssetLibrary
if eal.does_directory_exist(DEST):
    eal.delete_directory(DEST)

at = unreal.AssetToolsHelpers.get_asset_tools()
ui = unreal.FbxImportUI()
ui.set_editor_property("import_mesh", True)
ui.set_editor_property("import_animations", False)
ui.set_editor_property("import_as_skeletal", True)
ui.set_editor_property("import_materials", False)
ui.set_editor_property("import_textures", False)
ui.set_editor_property("automated_import_should_detect_type", False)
ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)

t = unreal.AssetImportTask()
t.set_editor_property("filename", SRC_FBX)
t.set_editor_property("destination_path", DEST)
t.set_editor_property("destination_name", DEST_NAME)
t.set_editor_property("automated", True)
t.set_editor_property("replace_existing", True)
t.set_editor_property("save", True)
t.set_editor_property("options", ui)

at.import_asset_tasks([t])

mesh = unreal.load_object(None, f"{DEST}/{DEST_NAME}")
if mesh:
    # Create temp IK Rig to read ref pose
    ik_factory = unreal.IKRigDefinitionFactory()
    ik_asset = at.create_asset("IK_Test", DEST, unreal.IKRigDefinition, ik_factory)
    c = unreal.IKRigController.get_controller(ik_asset)
    c.set_skeletal_mesh(mesh)
    
    unreal.log("=== Ref Pose of SK_Test_Darius (Imported without animations) ===")
    for b in ["Pelvis", "L_Hip", "R_Hip", "L_Shoulder", "R_Shoulder", "L_Foot", "R_Foot"]:
        tr = c.get_ref_pose_transform_of_bone(unreal.Name(b))
        unreal.log(f"  {b:<12} loc=({tr.translation.x:.2f}, {tr.translation.y:.2f}, {tr.translation.z:.2f})")
    
    # cleanup test
    eal.delete_directory(DEST)
