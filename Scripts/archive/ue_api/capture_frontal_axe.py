import unreal
import os

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

# 神王在 (0, 0, 125)，面朝 +X 方向 (yaw=0 / 180 depending on actor rot)
# 站在神王正前方稍偏右侧 (即面向他的右手和战斧)：
# 相机位置: X = +260.0, Y = -110.0, Z = 145.0
# 目标: X = 0.0, Y = -40.0, Z = 125.0
# delta = (-260.0, +70.0, -20.0)
# yaw = atan2(70, -260) = 180 - 15.0 = 165.0 度
# pitch = atan2(-20, 270) = -4.2 度
cam_loc = unreal.Vector(260.0, -110.0, 145.0)
cam_rot = unreal.Rotator(pitch=-4.2, yaw=165.0, roll=0.0)
ues.set_level_viewport_camera_info(cam_loc, cam_rot)

# 刷新视口
unreal.EditorLevelLibrary.editor_invalidate_viewports()

screenshot_path = "E:/UE/Fight/Saved/Screenshots/Darius_Frontal_Axe.png"
if os.path.exists(screenshot_path):
    try:
        os.remove(screenshot_path)
    except:
        pass

unreal.SystemLibrary.execute_console_command(None, f"HighResShot 1920x1080 filename=\"{screenshot_path}\"")
unreal.log(f"HighResShot triggered -> {screenshot_path}")
