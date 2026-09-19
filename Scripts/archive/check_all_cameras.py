import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
unreal.log(f"UES Viewport Size: {ues.get_level_viewport_size()}")
loc, rot = ues.get_level_viewport_camera_info()
unreal.log(f"UES Viewport Camera: Loc={loc}, Rot={rot}")

# Check if there is a CineCameraActor or CameraActor in the level
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in actor_sub.get_all_level_actors():
    if "Camera" in a.get_class().get_name():
        unreal.log(f"Camera Actor in Level: {a.get_name()} ({a.get_class().get_name()}) at {a.get_actor_location()}, rot={a.get_actor_rotation()}")
