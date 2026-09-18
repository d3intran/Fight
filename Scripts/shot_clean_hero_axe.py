import unreal
import time
import os

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

# 1. 退出任何相机试点并清理测试相机
les.eject_pilot_level_actor()
for a in actor_sub.get_all_level_actors():
    if "TestCamera" in a.get_name():
        actor_sub.destroy_actor(a)

# 2. 取消所有选中
actor_sub.set_selected_level_actors([])

# 3. 英雄正面机位设置
# 神王在 (0, 0, 125)，正面朝向 +X 方向！
# 我们将相机置于神王正前方稍偏右侧 (X=+350.0, Y=-100.0, Z=150.0)，视线朝向神王胸膛与右手战斧
# delta: target (0, -30, 120) - cam (350, -100, 150) = (-350.0, +70.0, -30.0)
# yaw = atan2(70, -350) = 168.69 度
# pitch = atan2(-30, 357) = -4.8 度
cam_loc = unreal.Vector(350.0, -100.0, 150.0)
cam_rot = unreal.Rotator(pitch=-4.8, yaw=168.69, roll=0.0)

for k in les.get_viewport_config_keys():
    les.set_level_viewport_camera_info(cam_loc, cam_rot, k)
    try:
        les.editor_set_game_view(True, k)
        les.editor_set_viewport_realtime(True, k)
    except:
        pass

les.editor_invalidate_viewports()

# 4. 执行截图
screenshot_path = "E:/UE/Fight/Saved/Screenshots/Darius_GodKing_Axe_Deliverable.png"
if os.path.exists(screenshot_path):
    try:
        os.remove(screenshot_path)
    except:
        pass

unreal.log("Starting simulate for live frame capture...")
les.editor_play_simulate()
time.sleep(1.0)

unreal.SystemLibrary.execute_console_command(None, f"HighResShot 1920x1080 filename=\"{screenshot_path}\"")
unreal.log(f"HighResShot requested -> {screenshot_path}")
time.sleep(1.5)

les.editor_request_end_play()
unreal.log("Simulate finished.")
