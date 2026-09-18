# -*- coding: utf-8 -*-
"""SceneCapture 拍摄角色持斧（离屏，稳定）"""
import unreal, os, time

def L(s=""):
    unreal.log(str(s))

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if les.is_in_play_in_editor():
    les.editor_request_end_play()
    L("!! PIE 未结束")
    raise SystemExit

killed = []
for a in actor_sub.get_all_level_actors():
    n = a.get_name()
    if n.startswith(("BP_DariusCharacter", "AXE_", "CameraActor_", "AxeProxy", "AxeCap_",
                     "SceneCapture2D_", "StaticMeshActor_0", "StaticMeshActor_5", "StaticMeshActor_6",
                     "TempAudit_", "DariusShowcase")):
        killed.append(n)
        actor_sub.destroy_actor(a)
L("清理: %s" % killed)
L("剩余: %s" % [a.get_name() for a in actor_sub.get_all_level_actors()])

bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
actor = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125),
                                         unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0))
actor.set_actor_label("AXE_Showcase")
actor_sub.set_selected_level_actors([])
L("角色: %s" % actor.get_name())

# RT
if not unreal.EditorAssetLibrary.does_directory_exist("/Game/Temp"):
    unreal.EditorAssetLibrary.make_directory("/Game/Temp")
rt = unreal.load_asset("/Game/Temp/RT_AxeCap")
if rt is None:
    rt = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "RT_AxeCap", "/Game/Temp", unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew())
rt.set_editor_property("size_x", 1200)
rt.set_editor_property("size_y", 900)

out = "E:/UE/Fight/Saved/Shots/AxeAudit"
os.makedirs(out, exist_ok=True)

sc_class = unreal.load_class(None, "/Script/Engine.SceneCapture2D")
cap_actor = actor_sub.spawn_actor_from_class(sc_class, unreal.Vector(-520.0, -90.0, 140.0),
                                             unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
cap_actor.set_actor_label("SceneCapture2D_char")
cap = cap_actor.capture_component2d
cap.set_editor_property("texture_target", rt)
cap.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cap.set_editor_property("fov_angle", 46.0)
cap.set_editor_property("capture_every_frame", False)
L("SceneCapture ready: %s" % cap)

VIEWS = [
    ("S1_right",  (-520.0, -90.0, 140.0),  0.0,    0.0),
    ("S2_front",  (0.0, -560.0, 150.0),    -3.0,  90.0),
    ("S3_q34",    (-390.0, -430.0, 185.0), -8.0,  47.0),
    ("S4_top",    (0.0, -80.0, 600.0),    -86.0,  90.0),
    ("S5_close",  (-230.0, -330.0, 135.0), -4.0,  55.0),
]
for nm, loc, pitch, yaw in VIEWS:
    cap_actor.set_actor_location(unreal.Vector(*loc), False, False)
    cap_actor.set_actor_rotation(unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0), False)
    time.sleep(0.4)
    cap.capture_scene()
    time.sleep(0.9)
    try:
        unreal.RenderingLibrary.export_render_target(unreal.UnrealEditorSubsystem.get_editor_world(None), rt, out, nm)
    except Exception as e:
        try:
            ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
            unreal.RenderingLibrary.export_render_target(ues.get_editor_world(), rt, out, nm)
        except Exception as e2:
            L("  export err %s / %s" % (e, e2))
    L("captured %s @ (%.0f,%.0f,%.0f) pitch=%.0f yaw=%.0f" % (nm, loc[0], loc[1], loc[2], pitch, yaw))

L("=== DONE ===")
