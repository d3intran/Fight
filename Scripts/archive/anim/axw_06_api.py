import unreal

C = unreal.AnimationDataController
for m in ("set_bone_track_keys", "add_bone_track", "remove_bone_track", "insert_bone_track",
          "open_bracket", "close_bracket", "resize_number_of_frames", "set_number_of_frames",
          "set_frame_rate", "get_model_interface", "set_play_length", "remove_all_bone_tracks"):
    f = getattr(C, m, None)
    unreal.log("### %s" % m)
    unreal.log("%s" % (f.__doc__ if f else "MISSING"))

unreal.log("### AnimSequence props")
for p in ("controller", "data_model", "data_model_interface"):
    try:
        unreal.log("   %s = %s" % (p, getattr(unreal.AnimSequence, p)))
    except Exception as e:
        unreal.log("   %s ERR %s" % (p, e))

unreal.log("### AnimationLibrary signature samples")
for m in ("get_bone_pose_for_frame", "get_bone_poses_for_frame", "get_num_frames", "get_raw_track_data"):
    f = getattr(unreal.AnimationLibrary, m, None)
    unreal.log("### %s" % m)
    unreal.log("%s" % (f.__doc__ if f else "MISSING"))

a = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/Anims/A_Darius_Walk_Layered")
c = a.controller
unreal.log("controller obj = %s" % c)
mi = c.get_model_interface()
unreal.log("model interface = %s" % mi)
unreal.log("mi doc: %s" % mi.__doc__)
for m in ("get_num_keys", "get_bone_track_names", "get_bone_track_by_name", "get_number_of_frames"):
    f = getattr(mi, m, None)
    unreal.log("   mi.%s :: %s" % (m, f.__doc__ if f else "MISSING"))
