# -*- coding: utf-8 -*-
"""把 UE 的 SM 导出为 OBJ，用几何数据硬判 local +Y / -Y 哪端是大刃"""
import unreal, os

def L(s=""):
    unreal.log(str(s))

sm = unreal.load_asset("/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")
out = "E:/UE/Fight/Saved/Shots/AxeAudit"
os.makedirs(out, exist_ok=True)
obj = out + "/sm_axe.obj"
if os.path.exists(obj):
    os.remove(obj)

task = unreal.AssetExportTask()
task.set_editor_property("object", sm)
task.set_editor_property("filename", obj)
task.set_editor_property("automated", True)
task.set_editor_property("replace_identical", True)
task.set_editor_property("prompt", False)
ok = False
for exp_name in ("StaticMeshExporterOBJ", "StaticMeshExporterOBJ2"):
    cls = getattr(unreal, exp_name, None)
    if cls is None:
        L("no exporter class %s" % exp_name)
        continue
    try:
        task.set_editor_property("exporter", cls())
        L("using %s" % exp_name)
    except Exception as e:
        L("set exporter err %s" % e)
try:
    ok = unreal.ExporterTaskHelper.run_asset_export_task(task) if hasattr(unreal, "ExporterTaskHelper") else None
except Exception as e:
    L("helper err %s" % e)
if ok is None:
    try:
        ok = unreal.AssetToolsHelpers.get_asset_tools().export_asset_tasks([task])
    except Exception as e:
        L("export err %s" % e)
L("export ok=%s exists=%s" % (ok, os.path.exists(obj)))
L("=== DONE ===")
