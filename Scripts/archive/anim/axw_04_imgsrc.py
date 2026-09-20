import unreal

eal = unreal.EditorAssetLibrary

PATHS = [
    "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Mixamo",
    "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Mixamo",
    "/Game/Character/Darius/Anims/A_Darius_Walk_Layered",
    "/Game/Character/Darius/Anims/A_Darius_Walk_InPlace",
]

for p in PATHS:
    a = eal.load_asset(p)
    unreal.log("======== %s" % p)
    if not a:
        unreal.log_error("   load FAILED")
        continue
    try:
        aid = a.get_editor_property("asset_import_data")
        unreal.log("   import_data class = %s" % aid.get_class().get_name())
        for m in ("get_first_filename", "get_source_file", "extract_filenames"):
            f = getattr(aid, m, None)
            if f is None:
                continue
            try:
                unreal.log("   %s -> %s" % (m, f()))
            except Exception as e:
                unreal.log("   %s ERR %s" % (m, e))
    except Exception as e:
        unreal.log("   import_data ERR %s" % e)
    try:
        unreal.log("   asset_import_data(str) = %s" % a.get_editor_property("asset_import_data"))
    except Exception:
        pass
