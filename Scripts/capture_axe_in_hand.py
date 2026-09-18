import unreal
import os

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

# 获取神王 Actor
actors = [a for a in actor_sub.get_all_level_actors() if "BP_DariusCharacter" in a.get_name()]
if not actors:
    unreal.log_error("No BP_DariusCharacter actor found!")
else:
    actor = actors[0]
    
    # 取消选中以隐藏橙色描边与坐标轴，获得纯净美观的渲染
    actor_sub.set_selected_level_actors([])

    # 查明右手 hand_rSocket 的精确世界坐标
    mesh = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    hand_loc = mesh.get_socket_location(unreal.Name("hand_rSocket"))
    unreal.log(f"Target hand_rSocket: {hand_loc}")

    # 将摄像机放置在右手前方偏外侧（英雄特写机位）:
    # 距离右手约 180cm，高度稍高于右手，以微俯视+侧面展现战斧全貌、利刃和握把
    # hand_loc 约在 (-7.5, +70.9, 118.3)
    cam_loc = unreal.Vector(hand_loc.x - 180.0, hand_loc.y + 110.0, hand_loc.z + 25.0)
    
    # 目标为战斧中央偏上 (hand_loc.x, hand_loc.y, hand_loc.z + 20.0)
    target = unreal.Vector(hand_loc.x, hand_loc.y, hand_loc.z + 10.0)
    delta = target - cam_loc
    
    # 计算 look_at 角度
    # delta: (+180.0, -110.0, -15.0)
    # yaw = atan2(-110, 180) = -31.4 度
    # pitch = atan2(-15, 210) = -4.1 度
    cam_rot = unreal.Rotator(pitch=-4.1, yaw=-31.4, roll=0.0)

    for k in les.get_viewport_config_keys():
        les.set_level_viewport_camera_info(cam_loc, cam_rot, k)
        les.editor_set_viewport_realtime(True, k)

    les.editor_invalidate_viewports()

    screenshot_path = "E:/UE/Fight/Saved/Screenshots/Darius_Weapon_Holding.png"
    unreal.SystemLibrary.execute_console_command(None, f"HighResShot 1920x1080 filename=\"{screenshot_path}\"")
    unreal.log(f"HighResShot triggered -> {screenshot_path}")
