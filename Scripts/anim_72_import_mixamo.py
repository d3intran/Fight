# -*- coding: utf-8 -*-
"""把转换后的 Mixamo 动作导入 UE，并**显式挂到 Darius 骨架**。

## 与 LOL 那条路线的关键区别
骨名已改成 Mannequin 命名 ⇒ 导入时指定 `skeleton = SK_Darius_GodKing_Skeleton`，
动画**直接**落在目标骨架上，**不需要 IK Retargeter / Retarget Pose 标定**。

⚠️ 两个已知坑（都踩过）：
1. **目标包名已存在 ⇒ Interchange 静默跳过动画工厂**（46→0 个）⇒ 导入前目标目录必须为空
2. **纯骨架 FBX 导入产出 0 资产** ⇒ 先用 `FBXIT_ANIMATION` + 显式 skeleton 试；
   若产出 0，再退回「给 FBX 加一个网格载体」

用法（经网关跑；docstring 里别写自己的文件名）：
    uv run --no-project python Scripts/ue_remote.py Scripts/<本脚本>
"""
import os
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

DEST = "/Game/Character/Darius/Anims_Mixamo2"
SKELETON = "/Game/Character/Darius/SK_Darius_GodKing_Skeleton"
JOBS = [
    ("A_Mixamo_WalkFwd", "E:/UE/Fight/Saved/Retarget/Mixamo/WalkFwd.fbx"),
    ("A_Mixamo_WalkBwd", "E:/UE/Fight/Saved/Retarget/Mixamo/WalkBwd.fbx"),
]

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if les.is_in_play_in_editor():
    LW("!! PIE 运行中，先退出 PIE")
    raise SystemExit

# ---------------------------------------------------------------- 前置门禁：目标必须空
existing = eal.list_assets(DEST, recursive=False, include_folder=False)
if existing:
    LW("!! %s 非空（%d 个）⇒ Interchange 会静默丢掉动画。已中止。" % (DEST, len(existing)))
    for a in sorted(existing)[:8]:
        LW("      %s" % str(a).split(".")[0])
    raise SystemExit

skel = unreal.load_asset(SKELETON)
L("目标骨架 = %s -> %s" % (SKELETON, "OK" if skel else "!! 加载失败"))
if skel is None:
    raise SystemExit

at = unreal.AssetToolsHelpers.get_asset_tools()
total = 0
for name, fbx in JOBS:
    if not os.path.isfile(fbx):
        LW("!! 缺文件 %s" % fbx)
        continue
    ui = unreal.FbxImportUI()
    # ⚠️ 必须走 SkeletalMesh 路径：纯骨架 FBX 导入产出 0 资产（已实测）。
    #    转换器已挂了一个 1cm 立方体当载体；骨架仍显式指定为 Darius 骨架。
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_animations", True)
    ui.set_editor_property("import_as_skeletal", True)
    ui.set_editor_property("automated_import_should_detect_type", False)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    ui.set_editor_property("skeleton", skel)
    try:
        aid = ui.get_editor_property("anim_sequence_import_data")
        aid.set_editor_property("use_default_sample_rate", False)
        aid.set_editor_property("custom_sample_rate", 30.0)
        aid.set_editor_property("import_uniform_scale", 1.0)
        ui.set_editor_property("anim_sequence_import_data", aid)
    except Exception as ex:
        L("   anim import data: %s" % ex)

    t = unreal.AssetImportTask()
    t.set_editor_property("filename", fbx)
    t.set_editor_property("destination_path", DEST)
    t.set_editor_property("destination_name", name)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", True)
    t.set_editor_property("options", ui)
    L("=== 导入 %s ===" % os.path.basename(fbx))
    at.import_asset_tasks([t])
    paths = [str(p) for p in t.get_editor_property("imported_object_paths")]
    L("   产出 = %d 个：%s" % (len(paths), [p.split(".")[0].split("/")[-1] for p in paths][:4]))
    for p in paths:
        pkg = p.split(".")[0]
        try:
            eal.save_asset(pkg)
        except Exception as ex:
            LW("   save 失败 %s: %s" % (pkg, str(ex)[:60]))
    total += len(paths)

# ---------------------------------------------------------------- 清点 + 门禁
L("")
L("=== 清点 %s ===" % DEST)
anims = []
for a in eal.list_assets(DEST, recursive=False, include_folder=False):
    pkg = a.split(".")[0]
    o = unreal.load_asset(pkg)
    if o is None:
        continue
    cn = o.get_class().get_name()
    L("   %-40s %s" % (pkg.split("/")[-1], cn))
    if cn == "AnimSequence":
        anims.append((pkg, o))

L("")
if not anims:
    LW("!! 0 个动画 —— 纯骨架 FBX 走 ANIMATION 类型也可能产出 0。")
    LW("!! 下一步：在 Blender 里给骨架挂一个立方体网格当载体再导出。")
    raise SystemExit(1)

for pkg, o in anims:
    n = unreal.AnimationLibrary.get_num_frames(o)
    sk = o.get_editor_property("skeleton")
    L("   %-24s 帧=%d 骨架=%s" % (pkg.split("/")[-1], n,
                                  sk.get_name() if sk else "<无>"))
L("=== DONE (%d 个动画) ===" % len(anims))
