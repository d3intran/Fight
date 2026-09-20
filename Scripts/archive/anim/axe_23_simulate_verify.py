# -*- coding: utf-8 -*-
"""终验：Simulate 模式下（角色播放动画）拍修复后的持斧画面"""
import unreal, os, time

def L(s=""):
    unreal.log(str(s))

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()

if les.is_in_play_in_editor():
    les.editor_request_end_play(); L("!! PIE"); raise SystemExit

def R(p, y, r):
    return unreal.Rotator(pitch=p, yaw=y, roll=r)

for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith(("BP_DariusCharacter", "FIX_", "SceneCapture2D_", "AXE_", "SIM_")):
        actor_sub.destroy_actor(a)

bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
act = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125), R(0.0, 180.0, 0.0))
act.set_actor_label("SIM_Darius")
mesh = act.get_component_by_class(unreal.SkeletalMeshComponent)
try:
    L("anim_class = %s" % mesh.get_editor_property("anim_class"))
except Exception as e:
    L("anim_class err %s" % e)
try:
    L("anim_mode  = %s" % mesh.get_editor_property("animation_mode"))
except Exception:
    pass
actor_sub.set_selected_level_actors([])

if not unreal.EditorAssetLibrary.does_directory_exist("/Game/Temp"):
    unreal.EditorAssetLibrary.make_directory("/Game/Temp")
rt = unreal.load_asset("/Game/Temp/RT_AxeCap")
if rt is None:
    rt = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "RT_AxeCap", "/Game/Temp", unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew())
rt.set_editor_property("size_x", 1200); rt.set_editor_property("size_y", 900)

sc_class = unreal.load_class(None, "/Script/Engine.SceneCapture2D")
ca = actor_sub.spawn_actor_from_class(sc_class, unreal.Vector(-560.0, -170.0, 150.0), R(0.0, 0.0, 0.0))
ca.set_actor_label("SceneCapture2D_sim")
cap = ca.capture_component2d
cap.set_editor_property("texture_target", rt)
cap.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cap.set_editor_property("fov_angle", 52.0)
cap.set_editor_property("capture_every_frame", False)

out = "E:/UE/Fight/Saved/Shots/AxeAudit"
os.makedirs(out, exist_ok=True)

VIEWS = [("sim_side", (-560.0, -170.0, 150.0), 0.0, 0.0),
         ("sim_q34", (-430.0, -430.0, 210.0), -8.0, 47.0)]

for nm, loc, pitch, yaw in VIEWS:
    ca.set_actor_location(unreal.Vector(*loc), False, False)
    ca.set_actor_rotation(R(pitch, yaw, 0.0), False)
    time.sleep(0.4)
    cap.capture_scene(); time.sleep(0.8)
    unreal.RenderingLibrary.export_render_target(ew, rt, out, "SIM_pre_%s" % nm)
    L("sim 前拍 SIM_pre_%s" % nm)

les.editor_play_simulate()
time.sleep(1.0)
L("simulate started")

for nm, loc, pitch, yaw in VIEWS:
    ca.set_actor_location(unreal.Vector(*loc), False, False)
    ca.set_actor_rotation(R(pitch, yaw, 0.0), False)
    time.sleep(0.6)
    cap.capture_scene(); time.sleep(1.0)
    unreal.RenderingLibrary.export_render_target(ew, rt, out, "SIM_%s" % nm)
    L("拍 SIM_%s" % nm)

les.editor_request_end_play()
L("simulate ended")

for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith(("SIM_", "SceneCapture2D_")):
        actor_sub.destroy_actor(a)
L("清理完成，剩余: %s" % [a.get_name() for a in actor_sub.get_all_level_actors()])
L("=== DONE ===")
