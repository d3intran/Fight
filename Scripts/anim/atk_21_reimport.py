# -*- coding: utf-8 -*-
"""诊断 + 重导：上次误建了 SkeletalMesh，这次显式指定「只导动画」。
先用别的名字落地，避免和已有资产同名冲突。"""
import unreal

SRC = "E:/UE/Fight/Saved/Attack/A_Darius_Attack1_LOL_UB.fbx"
DEST = "/Game/Character/Darius/Anims"
NAME = "A_Darius_Attack1_UB"
SKEL = "/Game/Character/Darius/SK_Darius_GodKing_Skeleton"
FULL = DEST + "/" + NAME

eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
L = unreal.log

L("=== FBXImportType 可选值 ===")
L("   %s" % [x for x in dir(unreal.FBXImportType) if not x.startswith("_")])

L("=== 目录现状 ===")
for p in eal.list_assets(DEST, recursive=False, include_folder=False):
    try:
        c = eal.find_asset_data(p).asset_class_path.asset_name
    except Exception:
        c = "?"
    L("   %-52s %s" % (p, c))

sk = eal.load_asset(SKEL)
ui = unreal.FbxImportUI()
ui.set_editor_property("import_mesh", False)
ui.set_editor_property("import_animations", True)
ui.set_editor_property("import_materials", False)
ui.set_editor_property("import_textures", False)
ui.set_editor_property("skeleton", sk)
ui.set_editor_property("create_physics_asset", False)
try:
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    L("已设 mesh_type_to_import = FBXIT_ANIMATION")
except Exception as ex:
    L("!! 设 FBXIT_ANIMATION 失败: %s" % ex)

task = unreal.AssetImportTask()
task.set_editor_property("filename", SRC)
task.set_editor_property("destination_path", DEST)
task.set_editor_property("destination_name", NAME)
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", True)
task.set_editor_property("save", True)
task.set_editor_property("options", ui)
at.import_asset_tasks([task])

L("=== 结果 ===")
if eal.does_asset_exist(FULL):
    a = eal.load_asset(FULL)
    L("OK  %s  类型=%s" % (FULL, type(a).__name__))
    if isinstance(a, unreal.AnimSequence):
        L("   骨架 = %s" % a.get_editor_property("skeleton").get_name())
        L("   帧数 = %d  时长 = %.4f s  采样率 = %.2f" % (
            unreal.AnimationLibrary.get_num_frames(a),
            unreal.AnimationLibrary.get_play_length(a),
            a.get_editor_property("sampling_frame_rate")))
        names = [str(n) for n in a.controller.get_model_interface().get_bone_track_names()]
        L("   骨骼轨道数 = %d" % len(names))
        for b in ("pelvis", "spine_01", "spine_03", "hand_l", "hand_r", "weapon_jnt"):
            L("     %-12s %s" % (b, "有轨道" if b in names else "!! 无轨道"))
else:
    L("!! 没找到 %s；目录现状:" % FULL)
    for p in eal.list_assets(DEST, recursive=False, include_folder=False):
        L("   - %s" % p)
