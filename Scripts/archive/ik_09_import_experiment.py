# -*- coding: utf-8 -*-
"""对照实验：找出「多 take FBX 导入后动画被丢」的原因。

只写内存不落盘（save=False），产出到 /Game/Temp/ImportExp 下，不动正式资产。

变量：
  A = 完全复刻当前导入设置（options = FbxImportUI，含 import_animations=True）
  B = 完全不传 options（走 Interchange 默认 pipeline 栈）
  C = 传 options 但目标路径全新（与 A 同设置、不同 dest，用于分离「目标已存在」因素）
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

SRC_FBX = "E:/UE/Fight/Saved/Retarget/Clean/Darius_SrcClean.fbx"
BASE = "/Game/Temp/ImportExp"


def pkg_of(p):
    return str(p).split(".")[0]


def make_options():
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
        ui.set_editor_property("anim_sequence_import_data", aid)
    except Exception as ex:
        LW("anim_sequence_import_data: %s" % ex)
    return ui


def run(tag, dest, name, with_options):
    if not eal.does_directory_exist(dest):
        eal.make_directory(dest)
    at = unreal.AssetToolsHelpers.get_asset_tools()
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", SRC_FBX)
    t.set_editor_property("destination_path", dest)
    t.set_editor_property("destination_name", name)
    t.set_editor_property("automated", True)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("save", False)
    if with_options:
        t.set_editor_property("options", make_options())

    L("")
    L("########## %s  dest=%s name=%s options=%s" % (tag, dest, name, with_options))
    try:
        at.import_asset_tasks([t])
    except Exception as ex:
        LW("   import_asset_tasks 抛异常: %s" % str(ex)[:200])
    paths = [pkg_of(p) for p in t.get_editor_property("imported_object_paths")]
    kinds = {}
    for p in paths:
        o = unreal.load_asset(p)
        cn = o.get_class().get_name() if o else "?"
        kinds[cn] = kinds.get(cn, 0) + 1
    L("[%s] 产出资产 = %d   分类 = %s" % (tag, len(paths), kinds))
    anims = [p for p in paths if unreal.load_asset(p) and
             unreal.load_asset(p).get_class().get_name() == "AnimSequence"]
    L("[%s] AnimSequence = %d" % (tag, len(anims)))
    for p in sorted(anims)[:3]:
        L("      %s" % p.split("/")[-1])
    return len(paths), len(anims)


L("=== 对照实验开始 ===")
resA = run("A", BASE + "/A", "SK_ImpExpA", True)
resC = run("C", BASE + "/C", "SK_ImpExpC", True)
resB = run("B", BASE + "/B", "SK_ImpExpB", False)

L("")
L("=== 汇总 ===")
L("A 复刻当前设置        : 总 %d / 动画 %d" % resA)
L("C 同设置·全新目标     : 总 %d / 动画 %d" % resC)
L("B 不传 options        : 总 %d / 动画 %d" % resB)
L("=== DONE ===")
