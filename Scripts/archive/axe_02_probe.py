# -*- coding: utf-8 -*-
"""战斧显示缺失 - 第二轮：SM 材质 / 蓝图组件实况 / SCS 节点"""
import unreal

def L(s=""):
    unreal.log(str(s))

def mat_name(mi):
    return mi.get_path_name() if mi else "None"

L("=== [1] SM_Darius_GodKing_Axe 材质与 section ===")
sm = unreal.load_asset("/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")
L("asset: %s" % sm)
if sm:
    try:
        sml = sm.get_editor_property("static_materials")
        L("static_materials: %d" % len(sml))
        for i, e in enumerate(sml):
            L("   Slot[%d] name=%s -> %s" % (i, e.get_editor_property("material_slot_name"),
                                             mat_name(e.get_editor_property("material_interface"))))
    except Exception as e:
        L("static_materials err: %s" % e)
    try:
        L("has_nanite: %s" % sm.get_editor_property("nanite_settings"))
    except Exception:
        pass
    try:
        for s in sm.get_editor_property("sockets"):
            L("   socket %s loc=%s" % (s.get_editor_property("socket_name"), s.get_editor_property("relative_location")))
    except Exception as e:
        L("sockets err: %s" % e)

L("")
L("=== [2] MI_Darius_Axe 材质实况 ===")
mi = unreal.load_asset("/Game/Character/Darius/Materials/MI_Darius_Axe")
L("MI: %s" % mi)
if mi:
    parent = None
    try:
        parent = mi.get_editor_property("parent")
    except Exception as e:
        L("parent err %s" % e)
    L("parent: %s" % parent)
    for p in ("blend_mode", "two_sided", "opacity_mask_clip_value"):
        try:
            L("  %s = %s" % (p, mi.get_editor_property(p)))
        except Exception:
            pass
    try:
        base = mi.get_editor_property("base_property_overrides")
        L("  base_property_overrides: %s" % base)
    except Exception as e:
        L("  overrides err: %s" % e)

L("")
L("=== [3] ABP / 角色网格材质覆盖 ===")
sk = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
mats = sk.get_editor_property("materials")
L("SK slot count = %d" % len(mats))
slot_names = [str(m.get_editor_property("material_slot_name")) for m in mats]
L("slot names: %s" % slot_names)

L("")
L("=== [4] 蓝图组件实况（临时 spawn） ===")
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
created = []
candidates = []
for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith(("BP_DariusCharacter", "TempAudit_")):
        candidates.append(a)

bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
temp = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125), unreal.Rotator(0, 0, 180))
temp.set_actor_label("TempAudit_Darius")
created.append(temp)
L("spawned: %s" % temp.get_name())

for c in temp.get_components_by_class(unreal.ActorComponent):
    cn = c.get_name()
    L("--- Comp %s (%s)" % (cn, c.get_class().get_name()))
    for p in ("relative_location", "relative_rotation", "relative_scale3d", "visible",
              "cast_shadow", "hidden_in_game", "mobility", "attach_socket_name",
              "absolute_scale", "static_mesh", "skeletal_mesh_asset"):
        try:
            L("      %s = %s" % (p, c.get_editor_property(p)))
        except Exception:
            pass
    try:
        L("      world_loc=%s world_scale=%s" % (c.get_world_location(), c.get_world_scale()))
    except Exception:
        pass
    try:
        n = c.get_num_materials()
        for i in range(n):
            L("      Slot[%d] -> %s" % (i, mat_name(c.get_material(i))))
    except Exception:
        pass
    try:
        bb = c.get_local_bounds()
        L("      local_bounds origin=%s extent=%s" % (bb.origin, bb.box_extent))
    except Exception:
        pass
    try:
        ob = c.get_bounds()
        L("      world_bounds origin=%s extent=%s" % (ob.origin, ob.box_extent))
    except Exception:
        pass

mesh = temp.get_component_by_class(unreal.SkeletalMeshComponent)
L("")
L("=== [5] 骨骼与手部插槽 ===")
L("NumBones: %d" % mesh.get_num_bones())
for bn in ("root", "hand_r", "hand_rSocket", "weapon_jnt"):
    try:
        cs = mesh.get_socket_transform(unreal.Name(bn), unreal.RelativeTransformSpace.RTS_COMPONENT)
        ws = mesh.get_socket_transform(unreal.Name(bn), unreal.RelativeTransformSpace.RTS_WORLD)
        L("  %s  compSpace loc=%s scale=%s | world loc=%s scale=%s" % (bn, cs.translation, cs.scale3d, ws.translation, ws.scale3d))
    except Exception as e:
        L("  %s err %s" % (bn, e))

L("")
L("=== [6] 清理临时 Actor ===")
for a in created:
    actor_sub.destroy_actor(a)
L("cleaned")
L("=== DONE ===")
