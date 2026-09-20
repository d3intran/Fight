import os
import unreal

eal = unreal.EditorAssetLibrary
OUT = "E:/UE/Fight/Saved/Preview/AxwExport"
os.makedirs(OUT, exist_ok=True)

CASES = [
    ("AxeWalk_Mixamo", "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Mixamo"),
    ("Walk_Layered", "/Game/Character/Darius/Anims/A_Darius_Walk_Layered"),
]

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
    ok = False
    try:
        ok = unreal.Exporter.run_asset_export_task(task)
    except Exception as ex:
        unreal.log_error("export ERR %s" % ex)
    unreal.log("%s ok=%s size=%s" % (name, ok, os.path.getsize(fn) if os.path.exists(fn) else -1))
unreal.log("### DONE")
