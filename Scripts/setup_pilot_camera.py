import unreal

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

# 清除已有的测试相机
for a in actor_sub.get_all_level_actors():
    if "TestCamera" in a.get_name():
        actor_sub.destroy_actor(a)

# 创建一个 CameraActor
cam_class = unreal.load_class(None, "/Script/Engine.CameraActor")
cam = actor_sub.spawn_actor_from_class(cam_class, unreal.Vector(0, 0, 0))
cam.set_actor_label("TestCamera")

# 获取神王
darius = [a for a in actor_sub.get_all_level_actors() if "BP_DariusCharacter" in a.get_name()][0]
darius_loc = darius.get_actor_location()
unreal.log(f"Darius is at: {darius_loc}")

# 找到右手 hand_rSocket 的世界坐标
mesh = darius.get_component_by_class(unreal.SkeletalMeshComponent)
hand_loc = mesh.get_socket_location(unreal.Name("hand_rSocket"))
unreal.log(f"Hand_rSocket is at: {hand_loc}")

# 我们把相机放在右手前方 150cm 处，直接平视右手与战斧！
# 设相机在 (hand_loc.x - 120, hand_loc.y - 120, hand_loc.z + 20)
# 或环绕拍摄
cam_loc = unreal.Vector(hand_loc.x - 120.0, hand_loc.y - 100.0, hand_loc.z + 15.0)
cam.set_actor_location(cam_loc, False, False)

# 计算朝向 hand_loc 的旋转
# look_at: target - cam = (120, 100, -15)
# yaw = atan2(100, 120) = 39.8 度
# pitch = atan2(-15, 156) = -5.5 度
cam_rot = unreal.Rotator(pitch=-5.5, yaw=39.8, roll=0.0)
cam.set_actor_rotation(cam_rot, False)

unreal.log(f"Spawned TestCamera at {cam_loc}, rot {cam_rot}")

# 试点相机
les.pilot_level_actor(cam)
unreal.log("Piloting TestCamera in level editor!")
