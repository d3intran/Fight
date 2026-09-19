# -*- coding: utf-8 -*-
"""离屏 SceneCapture 渲染：绕开失效的 HighResShot"""
import unreal, os, time

def L(s=""):
    unreal.log(str(s))

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()

if les.is_in_play_in_editor():
    les.editor_request_end_play()
    L("!! PIE 未结束")
    raise SystemExit

# ---------- 顶点/三角面数硬指标 ----------
sm = unreal.load_asset("/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")
try:
    L("UE mesh verts(lod0)  = %s" % unreal.EditorStaticMeshLibrary.get_number_verts(sm, 0))
    L("UE mesh tris(lod0)   = %s" % unreal.EditorStaticMeshLibrary.get_number_triangles(sm, 0))
    L("UE mesh LOD count    = %s" % unreal.EditorStaticMeshLibrary.get_lod_count(sm))
except Exception as e:
    L("vert/tri err: %s" % e)

# ---------- RenderTarget ----------
out = "E:/UE/Fight/Saved/Shots/AxeAudit"
os.makedirs(out, exist_ok=True)
if not unreal.EditorAssetLibrary.does_directory_exist("/Game/Temp"):
    unreal.EditorAssetLibrary.make_directory("/Game/Temp")
rt_path = "/Game/Temp/RT_AxeCap"
rt = unreal.load_asset(rt_path)
if rt is None:
    fac = unreal.TextureRenderTargetFactoryNew()
    rt = unreal.AssetToolsHelpers.get_asset_tools().create_asset("RT_AxeCap", "/Game/Temp", unreal.TextureRenderTarget2D, fac)
rt.set_editor_property("size_x", 1024)
rt.set_editor_property("size_y", 1024)
unreal.EditorAssetLibrary.save_loaded_asset(rt)
L("RT: %s  %sx%s" % (rt, rt.get_editor_property("size_x"), rt.get_editor_property("size_y")))

# ---------- 清场 + 摆斧头 ----------
for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith(("TempAudit_", "AxeView_", "AxeProxy", "AxeCap_", "CameraActor_AxeView")):
        actor_sub.destroy_actor(a)

proxy = actor_sub.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 130), unreal.Rotator(0, 0, 0))
proxy.set_actor_label("AxeProxy")
comp = proxy.static_mesh_component
comp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
comp.set_editor_property("static_mesh", sm)
actor_sub.set_selected_level_actors([])

# ---------- SceneCapture ----------
sc_class = unreal.load_class(None, "/Script/Engine.SceneCapture2D")
cap_actor = actor_sub.spawn_actor_from_class(sc_class, unreal.Vector(-620.0, 0.0, 130.0), unreal.Rotator(0.0, 0.0, 0.0))
cap_actor.set_actor_label("AxeCap_side")
cap = None
for attr in ("capture_component2d", "capture_component", "scene_capture_component2d"):
    try:
        cap = cap_actor.get_editor_property(attr) if hasattr(cap_actor, "get_editor_property") else None
        if cap is None:
            cap = getattr(cap_actor, attr)
        L("capture component via %s -> %s" % (attr, cap))
        break
    except Exception as e:
        L("  attr %s err %s" % (attr, e))
if cap is None:
    try:
        cap = cap_actor.get_component_by_class(unreal.SceneCaptureComponent2D)
        L("capture component via get_component_by_class -> %s" % cap)
    except Exception as e:
        L("component fallback err %s" % e)

if cap:
    for k, v in [("texture_target", rt),
                 ("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR),
                 ("fov_angle", 45.0),
                 ("post_process_blend_weight", 0.0),
                 ("show_flag_settings", None)]:
        if v is None:
            continue
        try:
            cap.set_editor_property(k, v)
            L("  set %s ok" % k)
        except Exception as e:
            L("  set %s err %s" % (k, e))
    try:
        cap.set_editor_property("capture_every_frame", True)
    except Exception as e:
        L("  capture_every_frame err %s" % e)
    L("cap props: source=%s fov=%s rt=%s" % (
        cap.get_editor_property("capture_source"), cap.get_editor_property("fov_angle"),
        cap.get_editor_property("texture_target")))

def do_capture(name):
    try:
        cap.capture_scene()
    except Exception as e:
        L("  capture_scene err %s" % e)
    time.sleep(1.0)
    try:
        unreal.RenderingLibrary.export_render_target(ew, rt, out, name)
        L("  exported %s/%s.png exists=%s" % (out, name, os.path.exists("%s/%s.png" % (out, name))))
    except Exception as e:
        L("  export err %s" % e)

do_capture("CAP_side")

# 正面
cap_actor.set_actor_rotation(unreal.Rotator(0.0, -90.0, 0.0), False)
cap_actor.set_actor_location(unreal.Vector(0.0, -620.0, 130.0), False, False)
time.sleep(0.6)
do_capture("CAP_front")

L("=== DONE ===")
