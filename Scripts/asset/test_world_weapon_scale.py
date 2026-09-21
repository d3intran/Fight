# -*- coding: utf-8 -*-
"""test_world_weapon_scale —— 验证在实际场景中武器与插槽的世界空间真实尺寸"""
import math
import unreal

bp_path = "/Game/Character/Darius/Blueprints/BP_DariusCharacter"
bp_class = unreal.EditorAssetLibrary.load_blueprint_class(bp_path)

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = ues.get_editor_world()

# 临时生成一个 actor 进行几何测量
actor = eas.spawn_actor_from_class(bp_class, unreal.Vector(0, 0, 100), unreal.Rotator(0, 0, 0))
actor.set_actor_label("TMP_Scale_Probe")

try:
    axe = None
    for c in actor.get_components_by_class(unreal.StaticMeshComponent):
        if "Weapon" in c.get_name():
            axe = c
            break
    
    unreal.log("=== 武器与插槽世界空间度量衡审计 ===")
    if axe:
        ws = axe.get_world_scale()
        unreal.log(f"武器组件世界缩放 (WorldScale): ({ws.x:.4f}, {ws.y:.4f}, {ws.z:.4f})")
        
        loc_main = axe.get_socket_location("Grip_Main")
        loc_tip = axe.get_socket_location("Blade_Tip")
        loc_edge = axe.get_socket_location("Blade_Edge")
        loc_pommel = axe.get_socket_location("Pommel")
        
        unreal.log(f"  Grip_Main 世界坐标: ({loc_main.x:.1f}, {loc_main.y:.1f}, {loc_main.z:.1f})")
        unreal.log(f"  Blade_Tip 世界坐标: ({loc_tip.x:.1f}, {loc_tip.y:.1f}, {loc_tip.z:.1f})")
        unreal.log(f"  Pommel    世界坐标: ({loc_pommel.x:.1f}, {loc_pommel.y:.1f}, {loc_pommel.z:.1f})")
        
        dist_tip_pommel = math.sqrt(
            (loc_tip.x - loc_pommel.x)**2 +
            (loc_tip.y - loc_pommel.y)**2 +
            (loc_tip.z - loc_pommel.z)**2
        )
        unreal.log(f"★ 斧柄底端 (Pommel) 到 刀尖 (Blade_Tip) 的世界欧式距离: {dist_tip_pommel:.2f} cm")
        
        if 130.0 <= dist_tip_pommel <= 180.0:
            unreal.log("   [PASS] 武器世界空间尺度 100% 正常（1.5米~1.7米双手重战斧真实尺度）！")
        else:
            unreal.log_warning(f"   [FAIL] 尺度异常: {dist_tip_pommel:.2f} cm")
    else:
        unreal.log_warning("未找到武器组件")
finally:
    eas.destroy_actor(actor)
    unreal.log("清理临时探测 Actor 完成。")
