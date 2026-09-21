# -*- coding: utf-8 -*-
"""把 Blender 侧传递出来的攻击动画 FBX 导入 UE，挂到 Darius 骨架上。

⚠️ 只导入动画，不导入网格（FBX 里带着 7 个网格对象，不关掉会生成重复 SkeletalMesh）。
⚠️ UE 5.8 走 Interchange：目标包名已存在时**静默跳过整个动画工厂**，所以先清同名资产。
"""
import unreal

SRC = "E:/UE/Fight/Saved/Attack/A_Darius_Attack1_LOL_UB.fbx"
DEST = "/Game/Character/Darius/Anims"
NAME = "A_Darius_Attack1_LOL_UB"
SKEL = "/Game/Character/Darius/SK_Darius_GodKing_Skeleton"
FULL = DEST + "/" + NAME

eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
L = unreal.log

sk = eal.load_asset(SKEL)
L("骨架 = %s  (%s)" % (sk, type(sk).__name__))

if eal.does_asset_exist(FULL):
    L("!! 目标已存在，先删：%s" % FULL)
    L("   delete -> %s" % eal.delete_asset(FULL))
else:
    L("目标不存在，直接导入：%s" % FULL)

ui = unreal.FbxImportUI()
ui.set_editor_property("import_mesh", False)
ui.set_editor_property("import_animations", True)
ui.set_editor_property("import_materials", False)
ui.set_editor_property("import_textures", False)
ui.set_editor_property("skeleton", sk)
ui.set_editor_property("create_physics_asset", False)
# 只保留动画（不要多建 PhysicsAsset / 材质）
ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)

task = unreal.AssetImportTask()
task.set_editor_property("filename", SRC)
task.set_editor_property("destination_path", DEST)
task.set_editor_property("destination_name", NAME)
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", True)
task.set_editor_property("save", True)
task.set_editor_property("options", ui)

at.import_asset_tasks([task])

L("=== 导入结果 ===")
if eal.does_asset_exist(FULL):
    a = eal.load_asset(FULL)
    L("OK  %s  类型=%s" % (FULL, type(a).__name__))
    try:
        L("   骨架 = %s" % a.get_editor_property("skeleton"))
        L("   帧数 = %d  时长 = %.4f s" % (
            unreal.AnimationLibrary.get_num_frames(a),
            unreal.AnimationLibrary.get_play_length(a)))
    except Exception as ex:
        L("   读属性失败: %s" % ex)
    L("   导入来源 = %s" % a.get_editor_property("asset_import_data").get_first_filename())
else:
    L("!! 没找到 %s" % FULL)
    L("   同目录下现有:")
    for x in eal.list_assets(DEST, recursive=False, include_folder=False):
        L("     - %s" % x)
