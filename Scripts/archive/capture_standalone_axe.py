import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

# Look at (0, 0, 150) from (200, 200, 200)
# delta: (-200, -200, -50)
# yaw = atan2(-200, -200) = -135 degrees
# pitch = atan2(-50, 282) = -10 degrees
cam_loc = unreal.Vector(250.0, 250.0, 200.0)
cam_rot = unreal.Rotator(pitch=-12.0, yaw=-135.0, roll=0.0)
ues.set_level_viewport_camera_info(cam_loc, cam_rot)

unreal.SystemLibrary.execute_console_command(None, "HighResShot 1920x1080")
unreal.log("HighResShot executed towards StaticMeshActor_0")
