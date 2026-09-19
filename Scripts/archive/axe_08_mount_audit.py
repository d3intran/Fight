# -*- coding: utf-8 -*-
"""装配数值审计：斧刃在世界空间到底落在哪"""
import unreal

def L(s=""):
    unreal.log(str(s))

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if les.is_in_play_in_editor():
    les.editor_request_end_play()
    L("!! PIE 未结束，稍后重跑")
    raise SystemExit

for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith(("TempAudit_", "AxeProxy", "AxeCap_")):
        actor_sub.destroy_actor(a)

bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
L("bp class: %s" % bp)
actor = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125), unreal.Rotator(0, 0, 180))
if actor is None:
    L("!! spawn 失败")
    raise SystemExit
actor.set_actor_label("TempAudit_Darius")
L("spawned: %s" % actor.get_name())
actor_sub.set_selected_level_actors([])

L("")
L("=== 全部组件 ===")
for c in actor.get_components_by_class(unreal.ActorComponent):
    extra = ""
    if c.get_class().get_name() == "StaticMeshComponent":
        try:
            smv = c.get_editor_property("static_mesh")
            extra = " static_mesh=%s" % (smv.get_path_name() if smv else None)
        except Exception:
            pass
    L("  %-24s %-26s%s" % (c.get_name(), c.get_class().get_name(), extra))

mesh = actor.get_component_by_class(unreal.SkeletalMeshComponent)
weapon = None
for c in actor.get_components_by_class(unreal.StaticMeshComponent):
    if "Weapon" in c.get_name() or "Axe" in c.get_name():
        weapon = c
L("")
L("mesh comp : %s" % (mesh.get_name() if mesh else None))
L("weapon comp: %s" % (weapon.get_name() if weapon else None))

def aabb_of_local_bounds(comp, lmin=None, lmax=None, label=""):
    """用组件世界变换把 SM 局部包围盒角点转到世界"""
    sm = comp.get_editor_property("static_mesh")
    b = sm.get_bounds()
    lo = b.origin - b.box_extent
    hi = b.origin + b.box_extent
    t = comp.get_world_transform()
    xs, ys, zs = [], [], []
    for i in (0, 1):
        for j in (0, 1):
            for k in (0, 1):
                p = unreal.Vector(lo.x if i == 0 else hi.x,
                                  lo.y if j == 0 else hi.y,
                                  lo.z if k == 0 else hi.z)
                w = t.transform_location(p)
                xs.append(w.x); ys.append(w.y); zs.append(w.z)
    L("  [%s] 世界 AABB  X %.1f~%.1f  Y %.1f~%.1f  Z %.1f~%.1f" % (
        label, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))

if weapon:
    L("")
    L("=== 武器组件 ===")
    for p in ("relative_location", "relative_rotation", "relative_scale3d", "absolute_scale",
              "visible", "cast_shadow", "hidden_in_game", "mobility", "attach_socket_name",
              "collision_enabled", "collision_profile_name"):
        try:
            L("  %-24s = %s" % (p, weapon.get_editor_property(p)))
        except Exception as e:
            L("  %-24s <err %s>" % (p, e))
    try:
        L("  attach parent         = %s" % weapon.get_attach_parent().get_name())
    except Exception as e:
        L("  attach parent err %s" % e)
    try:
        L("  world_loc   = %s" % weapon.get_world_location())
        L("  world_rot   = %s" % weapon.get_world_rotation())
        L("  world_scale = %s" % weapon.get_world_scale())
    except Exception as e:
        L("  world xform err %s" % e)
    L("  num_materials = %d" % weapon.get_num_materials())
    for i in range(weapon.get_num_materials()):
        mi = weapon.get_material(i)
        L("     Slot[%d] -> %s" % (i, mi.get_path_name() if mi else None))
    L("  SM 局部包围盒: origin=%s extent=%s" % (weapon.get_editor_property("static_mesh").get_bounds().origin,
                                              weapon.get_editor_property("static_mesh").get_bounds().box_extent))
    L("  局部包围盒 → 世界 AABB:")
    box = aabb_of_local_bounds(weapon, label="axe whole")

if mesh:
    L("")
    L("=== 角色网格 ===")
    for p in ("visible", "cast_shadow", "hidden_in_game"):
        try:
            L("  %s = %s" % (p, mesh.get_editor_property(p)))
        except Exception:
            pass
    st = mesh.get_socket_transform(unreal.Name("hand_rSocket"), unreal.RelativeTransformSpace.RTS_WORLD)
    L("  hand_rSocket world loc=%s rot=%s scale=%s" % (st.translation, st.rotation, st.scale3d))
    for bn in ("root", "hand_r", "weapon_jnt", "weapon_jnt_r"):
        try:
            s = mesh.get_socket_transform(unreal.Name(bn), unreal.RelativeTransformSpace.RTS_WORLD)
            L("  %-14s world loc=%s scale=%s" % (bn, s.translation, s.scale3d))
        except Exception as e:
            L("  %s err %s" % (bn, e))
    # 角色 AABB
    sk = mesh.get_editor_property("skeletal_mesh_asset")
    b = sk.get_bounds()
    t = mesh.get_world_transform()
    lo = b.origin - b.box_extent; hi = b.origin + b.box_extent
    xs, ys, zs = [], [], []
    for i in (0, 1):
        for j in (0, 1):
            for k in (0, 1):
                w = t.transform_location(unreal.Vector(lo.x if i == 0 else hi.x,
                                                       lo.y if j == 0 else hi.y,
                                                       lo.z if k == 0 else hi.z))
                xs.append(w.x); ys.append(w.y); zs.append(w.z)
    L("  角色世界 AABB  X %.1f~%.1f  Y %.1f~%.1f  Z %.1f~%.1f" % (
        min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

L("")
L("=== 清理 ===")
actor_sub.destroy_actor(actor)
L("destroyed")
L("=== DONE ===")
