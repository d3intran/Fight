# -*- coding: utf-8 -*-
"""第二轮对照：把「目标已存在」这个变量单独钉死。

R1 = 再导入一次到刚才已存在的同一条目标（包已在内存里）
R2 = 导入到全新目标（对照组，预期 48）
R3 = 导入到 LOL_Source 目录下但用全新名字（区分「目录」还是「包名」）
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

SRC_FBX = "E:/UE/Fight/Saved/Retarget/Clean/Darius_SrcClean.fbx"


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
    return ui


def run(tag, dest, name):
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
    t.set_editor_property("options", make_options())
    L("")
    L("########## %s  dest=%s  name=%s" % (tag, dest, name))
    try:
        at.import_asset_tasks([t])
    except Exception as ex:
        LW("   抛异常: %s" % str(ex)[:200])
    paths = [str(p).split(".")[0] for p in t.get_editor_property("imported_object_paths")]
    kinds = {}
    for p in paths:
        o = unreal.load_asset(p)
        cn = o.get_class().get_name() if o else "?"
        kinds[cn] = kinds.get(cn, 0) + 1
    L("[%s] 产出 = %d  %s" % (tag, len(paths), kinds))
    return len(paths), kinds.get("AnimSequence", 0)


L("=== 第二轮对照 ===")
r1 = run("R1 已存在的同一条目标", "/Game/Temp/ImportExp/A", "SK_ImpExpA")
r3 = run("R3 LOL_Source 下全新名字", "/Game/Character/Darius/LOL_Source", "SK_LOL_DariusProbe")
r2 = run("R2 全新目标（对照）", "/Game/Temp/ImportExp/D", "SK_ImpExpD")

L("")
L("=== 汇总 ===")
L("R1 目标已存在（同包名） : 总 %d / 动画 %d" % r1)
L("R3 同目录·换个包名      : 总 %d / 动画 %d" % r3)
L("R2 全新目录（对照）     : 总 %d / 动画 %d" % r2)
L("=== DONE ===")
