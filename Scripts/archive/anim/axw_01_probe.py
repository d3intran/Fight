import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

PATHS = [
    "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Mixamo",
    "/Game/Character/Darius/Anims/A_Darius_Walk_Layered",
    "/Game/Character/Darius/Anims/A_Darius_Walk_InPlace",
    "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Mixamo",
]

for p in PATHS:
    a = eal.load_asset(p)
    unreal.log("================ %s" % p)
    if not a:
        unreal.log_error("  load FAILED")
        continue
    unreal.log("  class = %s" % a.get_class().get_name())
    try:
        unreal.log("  length = %.4f" % a.get_play_length())
    except Exception as e:
        unreal.log("  length err %s" % e)
    for prop in ("number_of_frames", "sampling_frame_rate", "enable_root_motion",
                 "root_motion_root_lock", "force_root_lock", "sequence_length",
                 "rate_scale", "skeleton"):
        try:
            unreal.log("  %s = %s" % (prop, a.get_editor_property(prop)))
        except Exception as e:
            unreal.log("  %s -> ERR %s" % (prop, e))
    try:
        dm = a.get_data_model()
        names = list(dm.get_bone_track_names())
        unreal.log("  data_model OK, bone tracks = %d" % len(names))
        unreal.log("  track names sample = %s" % names[:8])
    except Exception as e:
        unreal.log("  data_model ERR %s" % e)
    try:
        c = a.get_controller()
        unreal.log("  controller = %s" % c)
    except Exception as e:
        unreal.log("  controller ERR %s" % e)

unreal.log("#################### AnimationDataController dir")
try:
    unreal.log("%s" % [m for m in dir(unreal.AnimationDataController) if not m.startswith("_")])
except Exception as e:
    unreal.log("ERR %s" % e)
unreal.log("#################### AnimationDataModel dir")
try:
    unreal.log("%s" % [m for m in dir(unreal.AnimationDataModel) if not m.startswith("_")])
except Exception as e:
    unreal.log("ERR %s" % e)
unreal.log("#################### AnimSequence dir (filtered)")
try:
    ms = [m for m in dir(unreal.AnimSequence) if "track" in m or "controller" in m or "data_model" in m or "bone" in m]
    unreal.log("%s" % ms)
except Exception as e:
    unreal.log("ERR %s" % e)
unreal.log("#################### AnimationLibrary dir")
try:
    unreal.log("%s" % [m for m in dir(unreal.AnimationLibrary) if not m.startswith("_")])
except Exception as e:
    unreal.log("ERR %s" % e)
