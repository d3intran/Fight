# -*- coding: utf-8 -*-
"""战斧单独渲染 + 换材质对照：定位是几何问题还是材质问题"""
import unreal, os, time

def L(s=""):
    unreal.log(str(s))

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

L("in PIE: %s" % les.is_in_play_in_editor())
if les.is_in_play_in_editor():
    les.editor_request_end_play()
    L("!! 已请求结束 PIE，请稍后重跑")
    raise SystemExit

for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith(("TempAudit_", "AxeView_", "CameraActor_AxeView", "AxeProxy_")):
        actor_sub.destroy_actor(a)

out = "E:/UE/Fight/Saved/Shots/AxeAudit"
os.makedirs(out, exist_ok=True)

sm = unreal.load_asset("/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")
b = sm.get_bounds()
L("SM bounds extent=(%.1f,%.1f,%.1f) origin=%s" % (b.box_extent.x * 2, b.box_extent.y * 2, b.box_extent.z * 2, b.origin))
L("num_sections(0) = %d" % sm.get_num_sections(0))
try:
    L("num_lods = %d" % sm.get_editor_property("num_lods"))
except Exception:
    pass
try:
    L("materials = %s" % [e.get_editor_property("material_interface").get_path_name() for e in sm.get_editor_property("static_materials")])
except Exception as e:
    L("mat err %s" % e)
# 顶点数（通过 bounds 无法拿到，尝试 LOD0 的 render data 不可用，改走 StaticMeshEditorSubsystem）
try:
    ses = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    L("tri count(lod0) = %s" % ses.get_num_triangles(sm, 0))
    L("vert count(lod0) = %s" % ses.get_num_vertices(sm, 0))
except Exception as e:
    L("tri/vert err %s" % e)

# 材质对照
default_mat = unreal.load_asset("/Engine/BasicShapes/BasicShapeMaterial")
mi_axe = unreal.load_asset("/Game/Character/Darius/Materials/MI_Darius_Axe")
L("default_mat=%s  mi_axe=%s" % (default_mat, mi_axe))

cam_class = unreal.load_class(None, "/Script/Engine.CameraActor")

def shot(tag, mat, loc, rot, fov=42.0, res=(1100, 1100)):
    a = actor_sub.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 120), unreal.Rotator(0, 0, 0))
    a.set_actor_label("AxeView_" + tag)
    c = a.static_mesh_component
    c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    c.set_editor_property("static_mesh", sm)
    if mat is not None:
        c.set_material(0, mat)
    for fn in ("get_bounds", "get_local_bounds"):
        try:
            wb = getattr(c, fn)()
            L("[%s] comp %s extent=(%.1f,%.1f,%.1f) origin=%s" % (
                tag, fn, wb.box_extent.x * 2, wb.box_extent.y * 2, wb.box_extent.z * 2, wb.origin))
        except Exception as e:
            L("[%s] %s err %s" % (tag, fn, e))
    cam = actor_sub.spawn_actor_from_class(cam_class, unreal.Vector(*loc), rot)
    cam.set_actor_label("CameraActor_AxeView_" + tag)
    try:
        cam.camera_component.set_editor_property("field_of_view", fov)
    except Exception:
        pass
    p = "%s/%s.png" % (out, tag)
    if os.path.exists(p):
        os.remove(p)
    unreal.AutomationLibrary.take_high_res_screenshot(res[0], res[1], p, cam, False)
    L("requested %s" % p)
    time.sleep(1.5)
    actor_sub.destroy_actor(cam)
    return a

# 相机沿 -X（侧视），看向原点
kept = []
kept.append(shot("A_axeMI_side", mi_axe, (-700.0, 0.0, 120.0), unreal.Rotator(0.0, 0.0, -90.0)))
kept.append(shot("B_axeDefault_side", default_mat, (-700.0, 0.0, 120.0), unreal.Rotator(0.0, 0.0, -90.0)))
kept.append(shot("C_axeDefault_34", default_mat, (-500.0, -500.0, 380.0), unreal.Rotator(-22.0, 0.0, -45.0)))

for a in kept + [x for x in actor_sub.get_all_level_actors() if x.get_name().startswith("CameraActor_AxeView")]:
    actor_sub.destroy_actor(a)
L("cleaned temp")
L("=== DONE ===")
