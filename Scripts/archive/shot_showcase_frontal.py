import unreal
import time
import os

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

# 取消所有 Actor 选中
actor_sub.set_selected_level_actors([])

# 相机机位：英雄正前方偏右 45 度全身像
# 神王在 (0, 0, 125)，面朝 -X 方向，右手持斧位于 +Y 侧
# 相机放于 (-450.0, 160.0, 160.0)，朝向神王胸膛与战斧中心 (0.0, 40.0, 120.0)
cam_loc = unreal.Vector(-450.0, 160.0, 160.0)
cam_rot = unreal.Rotator(pitch=-5.0, yaw=-15.0, roll=0.0)

for k in les.get_viewport_config_keys():
    les.set_level_viewport_camera_info(cam_loc, cam_rot, k)
    try:
        les.editor_set_game_view(True, k)
        les.editor_set_viewport_realtime(True, k)
    except:
        pass

les.editor_invalidate_viewports()

# 清理隐藏标记
unreal.SystemLibrary.execute_console_command(None, "showflag.Billboard 0")
unreal.SystemLibrary.execute_console_command(None, "showflag.Selection 0")

screenshot_path = "E:/UE/Fight/Saved/Screenshots/Darius_Hero_Frontal_Axe.png"
if os.path.exists(screenshot_path):
    try:
        os.remove(screenshot_path)
    except:
        pass

# 启动短暂模拟以激活渲染管线与光影
unreal.log("Starting simulate for full frame rendering...")
les.editor_play_simulate()
time.sleep(1.0)

unreal.SystemLibrary.execute_console_command(None, f"HighResShot 1920x1080 filename=\"{screenshot_path}\"")
unreal.log(f"HighResShot command sent -> {screenshot_path}")
time.sleep(1.5)

les.editor_request_end_play()
unreal.log("Simulate ended.")
