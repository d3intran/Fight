import unreal
import os

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

# 我们希望正面偏右，近景特写神王右手握持的战斧
# 神王在 (0, 0, 125)
# 如果神王面朝 -X (spawn_rot yaw=180)，他的正面在 -X 侧！
# 如果神王面朝 +X (spawn_rot yaw=0)，他的正面在 +X 侧！
# 先把相机放到 (-200, -80, 140)，朝向 (0, -40, 125)
# look_at: delta = (+200, +40, -15)
# yaw = atan2(40, 200) = 11.3 度
# pitch = atan2(-15, 204) = -4.2 度
cam_loc = unreal.Vector(-200.0, -80.0, 140.0)
cam_rot = unreal.Rotator(pitch=-4.2, yaw=11.3, roll=0.0)

for k in les.get_viewport_config_keys():
    les.set_level_viewport_camera_info(cam_loc, cam_rot, k)
    info = les.get_level_viewport_camera_info(k)
    unreal.log(f"Set viewport [{k}] -> {info}")

les.editor_invalidate_viewports()
unreal.log("All viewports updated and invalidated!")
