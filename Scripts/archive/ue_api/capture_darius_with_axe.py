import unreal
import os
import time

def run():
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

    # 1. 清理多余的测试 Actor，仅保留一个 BP_DariusCharacter
    darius_actors = []
    for a in actor_sub.get_all_level_actors():
        if "StaticMeshActor_0" in a.get_name():
            actor_sub.destroy_actor(a)
        elif "BP_DariusCharacter" in a.get_name():
            darius_actors.append(a)

    for a in darius_actors[1:]:
        actor_sub.destroy_actor(a)

    if not darius_actors:
        bp_class = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
        # 旋转 180 度，使神王面朝 -X 方向 (即正面朝向摄像机)
        actor = actor_sub.spawn_actor_from_class(bp_class, unreal.Vector(0, 0, 125), unreal.Rotator(0, 0, 180))
    else:
        actor = darius_actors[0]
        actor.set_actor_location(unreal.Vector(0, 0, 125), False, False)
        actor.set_actor_rotation(unreal.Rotator(0, 0, 180), False)

    # 2. 检查 WeaponAxe 组件状态
    axe_comp = None
    for c in actor.get_components_by_class(unreal.StaticMeshComponent):
        if "Weapon" in c.get_name():
            axe_comp = c
            break

    if not axe_comp:
        unreal.log_error("No WeaponAxe found on Darius Actor!")
        return

    unreal.log(f"Found WeaponAxe: {axe_comp.get_name()}")
    unreal.log(f"  Parent: {axe_comp.get_attach_parent()}")
    unreal.log(f"  Socket: {axe_comp.get_attach_socket_name()}")
    unreal.log(f"  WorldLoc: {axe_comp.get_world_location()}")
    unreal.log(f"  WorldRot: {axe_comp.get_world_rotation()}")
    unreal.log(f"  StaticMesh: {axe_comp.get_editor_property('static_mesh')}")
    unreal.log(f"  IsVisible: {axe_comp.is_visible()}")

    # 3. 设置摄像机为英雄斜前方 45 度视角，正对右手的霸气神王战斧与胸部狼首铠甲
    # 神王在 (0, 0, 125)，面朝 -X 方向 (胸口朝向 -X)
    # 右手 hand_r 在 (7.55, -70.91, 118.29) (在 -Y 侧)
    # 相机放置在 (-220, -180, 150)，朝向 (0, -40, 130)
    # delta: (+220, +140, -20)
    # yaw = atan2(140, 220) = ~32.5 度
    # pitch = atan2(-20, 260) = -4.4 度
    cam_loc = unreal.Vector(-220.0, -180.0, 150.0)
    cam_rot = unreal.Rotator(pitch=-4.5, yaw=32.5, roll=0.0)
    ues.set_level_viewport_camera_info(cam_loc, cam_rot)
    
    # 选中神王以便高亮视口焦点
    actor_sub.set_selected_level_actors([actor])

    # 4. 截图
    screenshot_path = "E:/UE/Fight/Saved/Screenshots/Darius_Hero_Axe.png"
    if os.path.exists(screenshot_path):
        try:
            os.remove(screenshot_path)
        except:
            pass

    task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, screenshot_path, force_game_view=False)
    unreal.log(f"AutomationLibrary screenshot requested -> {screenshot_path}")

if __name__ == "__main__":
    run()
