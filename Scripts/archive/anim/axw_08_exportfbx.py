import os
import unreal

eal = unreal.EditorAssetLibrary
OUT = "E:/UE/Fight/Saved/Preview/AxwExport"
os.makedirs(OUT, exist_ok=True)

CASES = [
    ("AxeWalk_Mixamo", "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Mixamo"),
    ("Walk_Layered", "/Game/Character/Darius/Anims/A_Darius_Walk_Layered"),
]

unreal.log("Exporter exists = %s" % hasattr(unreal, "Exporter"))
if hasattr(unreal, "Exporter"):
    unreal.log("Exporter dir = %s" % [m for m in dir(unreal.Exporter) if not m.startswith("_")])

for name, path in CASES:
    anim = eal.load_asset(path)
    if not anim:
        unreal.log_error("load fail %s" % path)
        continue
    fn = os.path.join(OUT, "%s.fbx" % name)
    task = unreal.AssetExportTask()
    task.set_editor_property("object", anim)
    task.set_editor_property("filename", fn)
    task.set_editor_property("automated", True)
    task.set_editor_property("prompt", False)
    task.set_editor_property("replace_identical", True)
    task.set_editor_property("exporter", None)
    ok = False
    try:
        ok = unreal.Exporter.run_asset_export_task(task)
    except Exception as e:
        unreal.log_error("run_asset_export_task ERR %s" % e)
    unreal.log("%s -> ok=%s exists=%s size=%s" % (
        name, ok, os.path.exists(fn), os.path.getsize(fn) if os.path.exists(fn) else -1))
unreal.log("OUT = %s" % OUT)
