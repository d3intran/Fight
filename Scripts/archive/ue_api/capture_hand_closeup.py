import unreal
import os

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

# hand_r is at (7.55, -70.91, 118.29)
# Let's place camera at (60, -180, 130), looking at (7.55, -70.91, 118.29)
# delta = (-52.45, 109.09, -11.71)
# yaw = atan2(109.09, -52.45) = ~115 degrees
cam_loc = unreal.Vector(80.0, -200.0, 140.0)
cam_rot = unreal.Rotator(pitch=-10.0, yaw=120.0, roll=0.0)

ues.set_level_viewport_camera_info(cam_loc, cam_rot)

screenshot_path = "E:/UE/Fight/Saved/Screenshots/Darius_Hand_CloseUp.png"
unreal.SystemLibrary.execute_console_command(None, f"HighResShot 1920x1080 filename=\"{screenshot_path}\"")
unreal.log(f"Close-up screenshot triggered -> {screenshot_path}")
