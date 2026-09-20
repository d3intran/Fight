import math
import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
cdo = unreal.get_default_object(bp)

unreal.log("############ 1. ACharacter 跳跃相关")
for p in ("jump_max_hold_time", "jump_max_count", "jump_current_count", "b_is_crouched",
          "jump_key_hold_time", "can_jump", "b_pressed_jump"):
    try:
        unreal.log("   %-26s = %s" % (p, cdo.get_editor_property(p)))
    except Exception as ex:
        unreal.log("   %-26s ERR %s" % (p, str(ex)[:40]))
unreal.log("   签名 jump_max_hold_time: %s" % (
    cdo.get_editor_property.__doc__ or "")[:0])
for m in ("get_jump_max_hold_time", "get_jump_max_count", "can_jump_internal"):
    f = getattr(cdo, m, None)
    if f:
        try:
            unreal.log("   %s() = %s" % (m, f()))
        except Exception as ex:
            unreal.log("   %s() ERR %s" % (m, str(ex)[:40]))

unreal.log("############ 2. CharacterMovement 跳跃相关（补充）")
for c in cdo.get_components_by_class(unreal.CharacterMovementComponent):
    for p in ("jump_z_velocity", "jump_off_jump_z_factor", "gravity_scale",
              "max_fly_speed", "b_can_walk_off_ledges", "b_use_separate_braking_friction",
              "velocity", "physics_volume_changed_delegate"):
        try:
            unreal.log("   %-32s = %s" % (p, c.get_editor_property(p)))
        except Exception as ex:
            unreal.log("   %-32s ERR %s" % (p, str(ex)[:35]))
    for m in ("is_falling", "is_flying", "is_moving_on_ground"):
        f = getattr(c, m, None)
        if f:
            try:
                unreal.log("   %s() = %s" % (m, f()))
            except Exception as ex:
                unreal.log("   %s() ERR %s" % (m, str(ex)[:35]))

unreal.log("############ 3. 网格 / 动画是否带 root motion")
for c in cdo.get_components_by_class(unreal.SkeletalMeshComponent):
    for p in ("enable_root_motion", "root_motion_mode", "relative_location", "relative_rotation"):
        try:
            unreal.log("   %-24s = %s" % (p, c.get_editor_property(p)))
        except Exception as ex:
            unreal.log("   %-24s ERR %s" % (p, str(ex)[:35]))
for p, tag in (("/Game/Characters/Mannequins/Animations/MM_Jump", "MM_Jump"),
               ("/Game/Characters/Mannequins/Animations/MM_Fall_Loop", "MM_Fall_Loop"),
               ("/Game/Characters/Mannequins/Animations/MM_Land", "MM_Land")):
    a = unreal.load_object(None, p)
    if a:
        try:
            unreal.log("   %-14s root_motion=%s length=%.3f" % (
                tag, a.get_editor_property("enable_root_motion"), a.get_play_length()))
        except Exception as ex:
            unreal.log("   %-14s ERR %s" % (tag, str(ex)[:40]))

unreal.log("############ 4. PIE 里斧头 vs 手")
gw = ues.get_game_world()
if gw:
    ch = None
    for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
        if a.get_class().get_name().startswith("BP_DariusCharacter"):
            ch = a
            break
    if ch:
        cmc = ch.get_components_by_class(unreal.CharacterMovementComponent)[0]
        unreal.log("   角色 z=%.1f  velocity=%s  falling=%s" % (
            ch.get_actor_location().z,
            [round(v, 1) for v in (ch.get_velocity().x, ch.get_velocity().y, ch.get_velocity().z)],
            cmc.is_falling()))
        mc = ch.get_components_by_class(unreal.SkeletalMeshComponent)[0]
        hl = mc.get_socket_transform("hand_r", unreal.RelativeTransformSpace.RTS_WORLD).translation
        sl = mc.get_socket_transform("hand_rSocket", unreal.RelativeTransformSpace.RTS_WORLD).translation
        unreal.log("   hand_r       world = %s" % [round(v, 1) for v in (hl.x, hl.y, hl.z)])
        unreal.log("   hand_rSocket world = %s" % [round(v, 1) for v in (sl.x, sl.y, sl.z)])
        for c in ch.get_components_by_class(unreal.StaticMeshComponent):
            if c.get_name() != "WeaponAxe":
                continue
            try:
                b = c.get_editor_property("bounds")
                unreal.log("   斧头世界 AABB center=%s extent=%s" % (
                    [round(v, 1) for v in (b.origin.x, b.origin.y, b.origin.z)],
                    [round(v, 1) for v in (b.box_extent.x, b.box_extent.y, b.box_extent.z)]))
                unreal.log("   手到斧头中心距离 = %.1f cm" % math.dist(
                    (b.origin.x, b.origin.y, b.origin.z), (sl.x, sl.y, sl.z)))
            except Exception as ex:
                unreal.log("   bounds ERR %s" % str(ex)[:50])
            for p in ("relative_location", "relative_rotation", "relative_scale3d"):
                try:
                    unreal.log("   %-20s = %s" % (p, c.get_editor_property(p)))
                except Exception as ex:
                    unreal.log("   %-20s ERR %s" % (p, str(ex)[:35]))
unreal.log("############ DONE")
