"""
=============================================================================
 德莱厄斯战斧握持与地面旧网格隐藏验证脚本 (verify_weapon_render.py)
 -----------------------------------------------------------------------------
 作用：
 1. 在关卡中心 (0, 0, 125) 生成 BP_DariusCharacter。
 2. 检查 Mesh 与 WeaponAxe 的挂接状态与 Socket 矩阵。
 3. 将视口相机推至英雄近景（涵盖战斧刀刃、手部握把与角色下盘），验证地面旧斧隐蔽性。
 4. 触发高分辨率截图并保存至指定路径。
=============================================================================
"""

import unreal
import os
import time

def verify():
    bp_class = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
    if not bp_class:
        unreal.log_error("Could not load BP_DariusCharacter_C!")
        return

    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    level_editor_sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

    # 清理之前残留的 Darius 测试 Actor
    for a in actor_sub.get_all_level_actors():
        if "BP_DariusCharacter" in a.get_name():
            actor_sub.destroy_actor(a)

    # 生成角色 - 旋转为 0 度，与之前 180 度翻转，确保正面对准视口
    spawn_loc = unreal.Vector(0.0, 0.0, 125.0)
    spawn_rot = unreal.Rotator(0.0, 0.0, 0.0)
    actor = actor_sub.spawn_actor_from_class(bp_class, spawn_loc, spawn_rot)
    if not actor:
        unreal.log_error("Failed to spawn BP_DariusCharacter!")
        return

    unreal.log(f"Spawned test actor: {actor.get_name()}")

    # 检查武器组件
    mesh_comp = None
    weapon_comp = None
    for c in actor.get_components_by_class(unreal.SceneComponent):
        c_name = c.get_name()
        if "CharacterMesh0" in c_name:
            mesh_comp = c
        elif "WeaponAxe" in c_name:
            weapon_comp = c

    if mesh_comp and weapon_comp:
        parent = weapon_comp.get_attach_parent()
        socket_name = weapon_comp.get_attach_socket_name()
        unreal.log(f"Weapon Component: {weapon_comp.get_name()}")
        unreal.log(f"  Parent: {parent.get_name() if parent else 'None'}")
        unreal.log(f"  Socket: {socket_name}")
        unreal.log(f"  Relative Location: {weapon_comp.get_editor_property('relative_location')}")
        unreal.log(f"  Relative Rotation: {weapon_comp.get_editor_property('relative_rotation')}")
        unreal.log(f"  Relative Scale: {weapon_comp.get_editor_property('relative_scale3d')}")
        unreal.log(f"  World Location: {weapon_comp.get_world_location()}")
        unreal.log(f"  StaticMesh: {weapon_comp.get_editor_property('static_mesh')}")
    else:
        unreal.log_warning("Mesh or Weapon component missing!")

    # 取消选中以彻底消除视口橙色描边/碰撞胶囊体线条
    actor_sub.set_selected_level_actors([])

    # 调整视口相机视角至英雄全景中远距离 (距离约 390cm，完整展现神王体格与霸气战斧全貌)
    # 神王在 (0, 0, 125)，右手位于 Y = +70.91 侧
    # 相机放在 (-380.0, 120.0, 160.0)，朝向神王与战斧中心 (0.0, 40.0, 130.0)
    # delta: target - cam = (+380.0, -80.0, -30.0)
    # yaw = atan2(-80, 380) = -11.89 度
    # pitch = atan2(-30, 388) = -4.42 度
    cam_loc = unreal.Vector(-380.0, 120.0, 160.0)
    cam_rot = unreal.Rotator(pitch=-4.42, yaw=-11.89, roll=0.0)
    
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    for k in les.get_viewport_config_keys():
        les.set_level_viewport_camera_info(cam_loc, cam_rot, k)
        try:
            les.editor_set_game_view(True, k)
        except:
            pass

    # 刷新视口
    les.editor_invalidate_viewports()

    # 执行 HighResShot
    screenshot_dir = "E:/UE/Fight/Saved/Screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = os.path.join(screenshot_dir, "Darius_Weapon_Holding.png").replace("\\", "/")
    
    unreal.SystemLibrary.execute_console_command(None, f"HighResShot 1920x1080 filename=\"{screenshot_path}\"")
    unreal.log(f"Triggered HighResShot -> {screenshot_path}")

if __name__ == "__main__":
    verify()
