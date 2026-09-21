# -*- coding: utf-8 -*-
"""import_clean_lol_source —— 把净化后的 LOL 源资产与 46 个动画全套导入 UE

导入目标：/Game/Character/Darius/LOL_Source/
    SK_LOL_Darius            (SkeletalMesh，包含纯净神王身体、披风与战斧，无狼无王座，无悬浮肩甲)
    SK_LOL_Darius_Skeleton   (Skeleton，65 根骨骼)
    <46 个标准尺寸的 AnimSequence>
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

SRC_FBX = "E:/UE/Fight/Saved/Retarget/Clean/SK_LOL_Darius_Clean.fbx"
DEST = "/Game/Character/Darius/LOL_Source"
DEST_NAME = "SK_LOL_Darius"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if les.is_in_play_in_editor():
    LW("!! PIE 运行中，先退出 PIE")
    raise SystemExit(1)

# 前置清理目标目录以确保 Interchange 触发动画工厂
if eal.does_directory_exist(DEST):
    eal.delete_directory(DEST)
    L(f"已清理目录: {DEST}")

at = unreal.AssetToolsHelpers.get_asset_tools()
ui = unreal.FbxImportUI()
ui.set_editor_property("import_mesh", True)
ui.set_editor_property("import_animations", True)
ui.set_editor_property("import_as_skeletal", True)
ui.set_editor_property("import_materials", False)
ui.set_editor_property("import_textures", False)
ui.set_editor_property("automated_import_should_detect_type", False)
ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)

try:
    smd = ui.get_editor_property("skeletal_mesh_import_data")
    smd.set_editor_property("import_rotation", unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0))
    ui.set_editor_property("skeletal_mesh_import_data", smd)
    L("SkeletalMeshImportData import_rotation 设为 Yaw=180.0°")
except Exception as ex:
    LW(f"skeletal_mesh_import_data config note: {ex}")

try:
    aid = ui.get_editor_property("anim_sequence_import_data")
    aid.set_editor_property("use_default_sample_rate", False)
    aid.set_editor_property("custom_sample_rate", 30.0)
    aid.set_editor_property("import_uniform_scale", 1.0)
    aid.set_editor_property("import_rotation", unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0))
    for p in ("snap_to_closest_frame_boundary", "b_snap_to_closest_frame_boundary"):
        try:
            aid.set_editor_property(p, True)
            break
        except Exception:
            pass
    ui.set_editor_property("anim_sequence_import_data", aid)
    L("AnimSequenceImportData import_rotation 设为 Yaw=180.0°")
except Exception as ex:
    L(f"anim_sequence_import_data config note: {ex}")

t = unreal.AssetImportTask()
t.set_editor_property("filename", SRC_FBX)
t.set_editor_property("destination_path", DEST)
t.set_editor_property("destination_name", DEST_NAME)
t.set_editor_property("automated", True)
t.set_editor_property("replace_existing", True)
t.set_editor_property("save", True)
t.set_editor_property("options", ui)

L(f"=== 开始导入纯净源资产: {SRC_FBX} ===")
at.import_asset_tasks([t])
paths = [str(p) for p in t.get_editor_property("imported_object_paths")]
L(f"导入产物资产总数 = {len(paths)} 个")

# 批量规范化重命名动画序列，彻底根治 SK_LOL_DariusSK_LOL_Darius_ 前缀重复 Bug
renamed_count = 0
for p in paths:
    pkg = p.split(".")[0]
    asset_name = pkg.split("/")[-1]
    # 如果是动画序列（不是 Mesh，不是 Skeleton）
    if asset_name not in ["SK_LOL_Darius", "SK_LOL_Darius_Skeleton", "SK_LOL_Darius_Mesh"]:
        clean_name = asset_name
        for prefix in ["SK_LOL_Darius", "SK_LOL_Darius_", "skinned_mesh_", "darius_skin15_", "darius_"]:
            clean_name = clean_name.replace(prefix, "")
        clean_name = clean_name.strip("_")
        new_asset_name = f"A_LOL_Darius_{clean_name}"
        new_pkg = f"{DEST}/{new_asset_name}"
        if new_pkg != pkg:
            ok = eal.rename_asset(pkg, new_pkg)
            if ok:
                eal.save_asset(new_pkg)
                renamed_count += 1

L(f"动画规范化重命名完成: {renamed_count} 个")

# 落盘保存全部资产
all_assets = eal.list_assets(DEST, recursive=False, include_folder=False)
saved = 0
for a in all_assets:
    pkg = str(a).split(".")[0]
    if eal.save_asset(pkg, only_if_is_dirty=False):
        saved += 1
L(f"落盘保存 = {saved}/{len(all_assets)} 个资产")

# 检查网格包围盒
mesh = unreal.load_object(None, f"{DEST}/{DEST_NAME}")
if mesh:
    b = mesh.get_bounds()
    L(f"=== SK_LOL_Darius 包围盒校验 ===")
    L(f"   box_extent: {b.box_extent}")
    L(f"   sphere_radius: {b.sphere_radius:.2f} cm")
    L(f"   Approx Size: {b.box_extent.x*2:.1f} x {b.box_extent.y*2:.1f} x {b.box_extent.z*2:.1f} cm")
    if b.sphere_radius < 260.0:
        L("   [PASS] 包围盒尺寸正常（2米左右正常人体英雄尺度）！")
    else:
        LW(f"   [WARN] 包围盒偏大: {b.sphere_radius:.2f} cm")
else:
    L("!! 未找到 SK_LOL_Darius")
