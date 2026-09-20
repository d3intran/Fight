import math
import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
if not gw:
    unreal.log("不在 PIE")
    raise SystemExit(0)

unreal.log("############ 1. 地面顶面高度 & 角色是否陷进地板")
floor_top = None
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.StaticMeshActor):
    lbl = a.get_actor_label()
    if "Floor" not in lbl:
        continue
    try:
        o, e = a.get_actor_bounds(False)
        floor_top = o.z + e.z
        unreal.log("   %-28s center_z=%.1f  extent_z=%.1f  ⇒ 顶面 z=%.1f" % (lbl, o.z, e.z, floor_top))
    except Exception as ex:
        unreal.log("   %s bounds ERR %s" % (lbl, str(ex)[:50]))

ch = None
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if a.get_class().get_name().startswith("BP_DariusCharacter"):
        ch = a
        break
if not ch:
    unreal.log("没角色")
    raise SystemExit(0)

caps = ch.get_components_by_class(unreal.CapsuleComponent)[0]
hh = caps.get_editor_property("capsule_half_height") * caps.get_editor_property("relative_scale3d").z
r = caps.get_editor_property("capsule_radius") * caps.get_editor_property("relative_scale3d").x
az = ch.get_actor_location().z
unreal.log("   角色 actor z=%.1f   胶囊 半径=%.1f 半高=%.1f  ⇒ 胶囊底 z=%.1f" % (az, r, hh, az - hh))
if floor_top is not None:
    unreal.log("   ⇒ 胶囊底 - 地面顶面 = %+.1f cm（≈0 才对）" % ((az - hh) - floor_top))

mc = ch.get_components_by_class(unreal.SkeletalMeshComponent)[0]
rl = mc.get_editor_property("relative_location")
unreal.log("   网格 relative_location z = %.1f" % rl.z)
lo = None
for b in ("ball_l", "ball_r", "toe_l", "toe_r", "foot_l", "foot_r"):
    try:
        z = mc.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_WORLD).translation.z
        unreal.log("      %-8s world z = %6.1f" % (b, z))
        lo = z if lo is None else min(lo, z)
    except Exception:
        pass
if lo is not None and floor_top is not None:
    sole = lo - 4.5          # 鞋底比 ball 骨低约 4.5cm（bind pose 实测）
    unreal.log("   ⇒ 鞋底 z ≈ %.1f ；地面顶面 %.1f ⇒ 脚陷入地面 %+.1f cm" % (
        sole, floor_top, floor_top - sole))

unreal.log("############ 2. IA_Jump 的触发方式")
ia = unreal.load_object(None, "/Game/Input/Actions/IA_Jump")
if ia:
    for p in ("value_type", "triggers", "modifiers", "b_consume_input", "b_trigger_when_paused"):
        try:
            v = ia.get_editor_property(p)
            if p in ("triggers", "modifiers"):
                v = [(x.get_class().get_name(), str(x.get_editor_property("trigger_type"))
                      if p == "triggers" else "") for x in v]
            unreal.log("   %-22s = %s" % (p, v))
        except Exception as ex:
            unreal.log("   %-22s ERR %s" % (p, str(ex)[:45]))
imc = unreal.load_object(None, "/Game/Input/IMC_Default")
if imc:
    try:
        for m in imc.get_editor_property("mappings"):
            a = m.get_editor_property("action")
            k = m.get_editor_property("key")
            unreal.log("   IMC: %-16s <- %s" % (a.get_name() if a else None, k))
    except Exception as ex:
        unreal.log("   IMC ERR %s" % str(ex)[:60])
unreal.log("############ DONE")
