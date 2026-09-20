# -*- coding: utf-8 -*-
"""
ik_01_import_source.py —— 把净化后的 LOL 源骨架（59 骨 + 46 动画）导入 UE

输出：/Game/Character/Darius/LOL_Source/
        SK_LOL_Darius_Skeleton   (Skeleton)
        SK_LOL_Darius            (SkeletalMesh，仅为骨架载体)
        <46 个 AnimSequence>

--------------------------------------------------------------------
⚠️ 本脚本**刻意不做资产重命名**。原因（两条都是实测）：
  1. `EditorAssetLibrary.list_assets()` 返回的是 "package.object" 形式
     （`/Game/X/A.A`），而 `rename_asset()` 需要纯 package 路径（`/Game/X/A`）。
     把带 `.object` 的串拼进路径交给 rename ⇒ UE 抛
     EXCEPTION_ACCESS_VIOLATION，**整个编辑器崩溃**。
  2. 即便传对路径，rename 的效果在未 save 前会随编辑器状态重载而回退
     （实测 rename 返回 True，但后续 list_assets 仍是旧名）。

  ⇒ 源资产保持长名（`SK_LOL_Dariusskinned_mesh_darius_skin15_*`），
    输出名的美化交给 batch retarget 的 search/replace 参数
    （见 ik_11_batch_retarget.py）。
--------------------------------------------------------------------
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

SRC_FBX = "E:/UE/Fight/Saved/Retarget/Clean/Darius_SrcClean.fbx"
DEST = "/Game/Character/Darius/LOL_Source"
DEST_NAME = "SK_LOL_Darius"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if les.is_in_play_in_editor():
    LW("!! PIE 运行中，先退出 PIE")
    raise SystemExit

# ---------------------------------------------------------------- 前置门禁（必读）
# UE 5.8 用 Interchange 导入 FBX。**目标包名已存在时会静默跳过动画工厂**
# （只重建 SkeletalMesh，不报错）。实测三组对照：
#     包名已存在 -> 1 资产 / 0 动画 ｜ 同目录换新名 -> 48/46 ｜ 全新目录 -> 48/46
# ⇒ 导入前目标必须是空目录。先跑清理脚本，或改用全新的 destination_name。
_existing = eal.list_assets(DEST, recursive=False, include_folder=False)
if _existing:
    LW("!! 目标 %s 非空（%d 个资产），Interchange 会静默丢掉全部动画。" % (DEST, len(_existing)))
    LW("!! 请先执行清理脚本，或换 DEST_NAME。已中止。")
    for _a in sorted(_existing)[:6]:
        LW("      %s" % str(_a).split(".")[0])
    raise SystemExit

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
    ui.set_editor_property("skeleton", None)
except Exception:
    pass

try:
    aid = ui.get_editor_property("anim_sequence_import_data")
    aid.set_editor_property("use_default_sample_rate", False)
    aid.set_editor_property("custom_sample_rate", 30.0)
    aid.set_editor_property("import_uniform_scale", 1.0)
    for p in ("snap_to_closest_frame_boundary", "b_snap_to_closest_frame_boundary"):
        try:
            aid.set_editor_property(p, True)
            L("已开启 %s" % p)
            break
        except Exception:
            pass
    ui.set_editor_property("anim_sequence_import_data", aid)
except Exception as ex:
    L("anim_sequence_import_data: %s" % ex)

t = unreal.AssetImportTask()
t.set_editor_property("filename", SRC_FBX)
t.set_editor_property("destination_path", DEST)
t.set_editor_property("destination_name", DEST_NAME)
t.set_editor_property("automated", True)
t.set_editor_property("replace_existing", True)
t.set_editor_property("save", True)
t.set_editor_property("options", ui)

L("=== 导入 %s ===" % SRC_FBX)
at.import_asset_tasks([t])
paths = [str(p) for p in t.get_editor_property("imported_object_paths")]
L("产出资产 = %d 个" % len(paths))

# 逐个显式 save（import task 的 save 标志实测不足以保证 46 个动画全部落盘）
saved = 0
failed = []
for p in paths:
    pkg = p.split(".")[0]
    try:
        if eal.save_asset(pkg):
            saved += 1
    except Exception as ex:
        failed.append((pkg, str(ex)[:60]))
L("显式 save 成功 = %d / %d" % (saved, len(paths)))
for pkg, err in failed[:5]:
    LW("   save 失败 %s : %s" % (pkg.split("/")[-1], err))

# ---------------------------------------------------------------- 清点
L("")
L("=== 清点 %s ===" % DEST)
kinds = {}
anims = []
for a in eal.list_assets(DEST, recursive=False, include_folder=False):
    pkg = a.split(".")[0]
    o = unreal.load_asset(pkg)
    if o is None:
        continue
    cn = o.get_class().get_name()
    kinds[cn] = kinds.get(cn, 0) + 1
    if cn == "AnimSequence":
        anims.append(pkg)
for k, v in sorted(kinds.items(), key=lambda x: -x[1]):
    L("   %-22s %d" % (k, v))

L("")
L("动画前 5 个：")
for p in sorted(anims)[:5]:
    L("   %s" % p.split("/")[-1])

L("")
L("磁盘落盘检查（关键：动画必须真的写到 .uasset）：")
import os
disk = os.listdir("E:/UE/Fight/Content/Character/Darius/LOL_Source")
n_disk = len([f for f in disk if f.endswith(".uasset")])
L("   目录下 .uasset 数 = %d" % n_disk)

# ---------------------------------------------------------------- 后置门禁
if len(anims) != 46:
    LW("!! 期望 46 个 AnimSequence，实际 %d 个 —— 导入链路丢动画了。" % len(anims))
    LW("!! 先查目标目录是否非空（Interchange 重导入路径会静默跳过动画工厂）。")
    raise SystemExit(1)
if n_disk < 48:
    LW("!! 磁盘上应至少 48 个 .uasset，实际 %d 个 —— 资产没落盘。" % n_disk)
    raise SystemExit(1)
L("门禁通过：46 个动画 + 骨架/网格全部落盘。")

L("=== DONE ===")
