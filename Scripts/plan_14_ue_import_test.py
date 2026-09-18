# -*- coding: utf-8 -*-
"""
plan_14_ue_import_test.py —— M1-① 最终消费者验证：净化后的 FBX 能否在 UE 侧正确导入

导入到临时目录 /Game/Temp_SrcClean，检查：
  1. 是否成功建出 Skeleton（纯骨架、无 mesh 的 FBX 是否被接受）
  2. 生成了多少 AnimSequence、帧数是否与源一致
  3. Skeleton 的 reference pose 里 Root 的位置是否为 (0,0,127.37) 量级
     （若 bind pose 被当前 pose 污染，这里会明显偏移）
跑完请执行 plan_99_clean_temp.py 清理临时资产。

用法：uv run --no-project python Scripts/ue_remote.py Scripts/plan_14_ue_import_test.py
"""
import unreal

TMP = "/Game/Temp_SrcClean"
FBX = "E:/UE/Fight/Saved/Retarget/Clean/Darius_SrcClean.fbx"
L = unreal.log
LW = unreal.log_warning

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if les.is_in_play_in_editor():
    L("!! PIE 运行中，先退出 PIE 再导入")
    raise SystemExit

eal = unreal.EditorAssetLibrary
if eal.does_directory_exist(TMP):
    L("清理旧目录 %s -> %s" % (TMP, eal.delete_directory(TMP)))

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
except Exception as e:
    L("set skeleton=None 失败: %s" % e)

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
except Exception as e:
    L("anim_sequence_import_data 配置失败: %s" % e)

t = unreal.AssetImportTask()
t.set_editor_property("filename", FBX)
t.set_editor_property("destination_path", TMP)
t.set_editor_property("destination_name", "SrcClean")
t.set_editor_property("automated", True)
t.set_editor_property("replace_existing", True)
t.set_editor_property("save", True)
t.set_editor_property("options", ui)

L("=== 开始导入 %s ===" % FBX)
try:
    at.import_asset_tasks([t])
    paths = [str(p) for p in t.get_editor_property("imported_object_paths")]
    L("imported_object_paths = %d 个" % len(paths))
    for p in paths[:8]:
        L("   %s" % p)
except Exception as e:
    LW("导入异常: %s" % e)

L("")
L("=== 目录清单 ===")
assets = eal.list_assets(TMP, recursive=True, include_folder=False)
L("资产总数 = %d" % len(assets))
kinds = {}
anims = []
for a in assets:
    o = unreal.load_asset(a)
    if o is None:
        L("   <load failed> %s" % a)
        continue
    cn = o.get_class().get_name()
    kinds[cn] = kinds.get(cn, 0) + 1
    if cn == "AnimSequence":
        anims.append((a, o))
for k, v in sorted(kinds.items(), key=lambda x: -x[1]):
    L("   %-28s %d" % (k, v))

L("")
L("=== 抽查 AnimSequence 帧数 ===")
L("  %-58s %8s" % ("asset", "frames"))
sampled = 0
for a, o in sorted(anims, key=lambda x: x[0]):
    try:
        nf = o.get_editor_property("number_of_frames")
    except Exception:
        try:
            nf = o.get_editor_property("sequence_length")
        except Exception:
            nf = "?"
    if sampled < 12 or "run" in a or "turn" in a or "spell4_5" in a or "idle1" in a:
        L("  %-58s %8s" % (a.split("/")[-1], nf))
    sampled += 1

L("")
L("=== Skeleton reference pose 检查 ===")
skel = eal.load_asset(TMP + "/SrcClean_Skeleton")
if skel is None:
    LW("找不到 SrcClean_Skeleton —— 目录里可能有别的骨架名")
else:
    L("skeleton = %s" % skel.get_name())
    try:
        rp = skel.get_editor_property("reference_skeleton")
        L("reference_skeleton = %s" % rp)
    except Exception as e:
        L("reference_skeleton 读取失败: %s" % e)
    skm = eal.load_asset(TMP + "/SrcClean")
    if skm:
        try:
            L("skeletalmesh = %s  bones = %d" % (
                skm.get_name(), skm.get_editor_property("skeleton").get_editor_property("bone_tree").__len__()))
        except Exception:
            pass

L("")
L("=== 提示：跑完请执行 Scripts/plan_99_clean_temp.py 清理 %s ===" % TMP)
L("=== DONE ===")
