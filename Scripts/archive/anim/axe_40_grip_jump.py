import math
import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eal = unreal.EditorAssetLibrary

unreal.log("PIE = %s" % les.is_in_play_in_editor())

unreal.log("############ 1. 角色跳跃参数（BP 模板）")
bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
if bp:
    cdo = unreal.get_default_object(bp)
    for c in cdo.get_components_by_class(unreal.CharacterMovementComponent):
        unreal.log("   %s" % c.get_name())
        for p in ("jump_z_velocity", "gravity_scale", "air_control", "max_walk_speed",
                  "max_acceleration", "braking_deceleration_walking", "ground_friction",
                  "falling_lateral_friction", "mass", "movement_mode", "air_control_boost",
                  "jump_off_jump_z_factor", "walkable_floor_angle", "max_step_height",
                  "max_fly_speed", "default_land_movement_mode"):
            try:
                unreal.log("      %-32s = %s" % (p, c.get_editor_property(p)))
            except Exception as ex:
                unreal.log("      %-32s ERR %s" % (p, str(ex)[:40]))
    for c in cdo.get_components_by_class(unreal.SkeletalMeshComponent):
        try:
            rl = c.get_editor_property("relative_location")
            rr = c.get_editor_property("relative_rotation")
            unreal.log("   %s rel_loc=(%.1f, %.1f, %.1f) rel_rot=(%.1f, %.1f, %.1f)" % (
                c.get_name(), rl.x, rl.y, rl.z, rr.pitch, rr.yaw, rr.roll))
        except Exception as ex:
            unreal.log("   mesh ERR %s" % str(ex)[:50])

unreal.log("############ 2. 输入映射里 Space 绑了什么")
try:
    cdo = unreal.get_default_object(bp)
    imc = None
    for p in ("input_mapping_contexts",):
        try:
            imc = cdo.get_editor_property(p)
        except Exception:
            pass
    unreal.log("   IMC = %s" % imc)
except Exception as ex:
    unreal.log("   ERR %s" % str(ex)[:60])

unreal.log("############ 3. 关卡里角色实际跳跃参数（PIE 中）")
gw = ues.get_game_world()
if gw:
    ch = None
    for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
        if a.get_class().get_name().startswith("BP_DariusCharacter"):
            ch = a
            break
    if ch:
        cmc = ch.get_components_by_class(unreal.CharacterMovementComponent)[0]
        for p in ("jump_z_velocity", "gravity_scale", "max_fly_speed", "movement_mode"):
            try:
                unreal.log("   %-24s = %s" % (p, cmc.get_editor_property(p)))
            except Exception as ex:
                unreal.log("   %-24s ERR %s" % (p, str(ex)[:40]))
        mc = ch.get_components_by_class(unreal.SkeletalMeshComponent)[0]
        for c in ch.get_components_by_class(unreal.StaticMeshComponent):
            if c.get_name() == "WeaponAxe":
                aloc = c.get_component_transform().translation
                st = mc.get_socket_transform("hand_rSocket", unreal.RelativeTransformSpace.RTS_WORLD)
                hloc = mc.get_socket_transform("hand_r", unreal.RelativeTransformSpace.RTS_WORLD).translation
                unreal.log("   WeaponAxe world = %s" % [round(v, 1) for v in (aloc.x, aloc.y, aloc.z)])
                unreal.log("   hand_r   world = %s" % [round(v, 1) for v in (hloc.x, hloc.y, hloc.z)])
                unreal.log("   hand_rSocket world = %s" % [round(v, 1) for v in
                                                           (st.translation.x, st.translation.y, st.translation.z)])
                try:
                    b = c.get_editor_property("bounds")
                    unreal.log("   斧头世界 AABB: center=%s  extent=%s" % (
                        [round(v, 1) for v in (b.origin.x, b.origin.y, b.origin.z)],
                        [round(v, 1) for v in (b.box_extent.x, b.box_extent.y, b.box_extent.z)]))
                except Exception as ex:
                    unreal.log("   bounds ERR %s" % str(ex)[:50])
                try:
                    sm = c.get_editor_property("static_mesh")
                    bb = sm.get_bounds()
                    unreal.log("   斧头网格局部 extent=%s（X/Y/Z）" % [
                        round(v, 1) for v in (bb.box_extent.x, bb.box_extent.y, bb.box_extent.z)])
                except Exception as ex:
                    unreal.log("   mesh bounds ERR %s" % str(ex)[:50])
unreal.log("############ DONE")
