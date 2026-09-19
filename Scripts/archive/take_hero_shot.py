import unreal
import os

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

# 神王在 (0, 0, 125)，面朝 -X 方向 (yaw=180)
# 右手 hand_r 在 (7.55, -70.91, 118.29)
# 我们将相机放在神王右前侧:
# 相机位置: (-180.0, -160.0, 140.0)
# 视线目标: (0.0, -50.0, 120.0)
# delta: target - cam = (180.0, 110.0, -20.0)
# yaw = atan2(110, 180) = ~31.4 度
# pitch = atan2(-20, 210) = -5.4 度
cam_loc = unreal.Vector(-180.0, -160.0, 140.0)
cam_rot = unreal.Rotator(pitch=-5.4, yaw=31.4, roll=0.0)
ues.set_level_viewport_camera_info(cam_loc, cam_rot)

# 强制刷新视口
unreal.EditorLevelLibrary.editor_invalidate_viewports()

screenshot_path = "E:/UE/Fight/Saved/Screenshots/Darius_Hero_Axe_Shot.png"
if os.path.exists(screenshot_path):
    os.remove(screenshot_path)

unreal.SystemLibrary.execute_console_command(None, f"HighResShot 1920x1080 filename=\"{screenshot_path}\"")
unreal.log(f"Executed HighResShot -> {screenshot_path}")
