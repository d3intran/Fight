# -*- coding: utf-8 -*-
"""终极对照：无角色遮挡，同一 SM 的两种变换并排渲染"""
import unreal, os, time

def L(s=""):
    unreal.log(str(s))

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()

if les.is_in_play_in_editor():
    les.editor_request_end_play(); L("!! PIE"); raise SystemExit

killed = []
for a in actor_sub.get_all_level_actors():
    n = a.get_name()
    if n.startswith(("BP_DariusCharacter", "AXE_", "CameraActor_", "AxeProxy", "AxeCap_",
                     "SceneCapture2D_", "ABTest_", "XYZ_", "StaticMeshActor_0",
                     "StaticMeshActor_5", "StaticMeshActor_6", "TempAudit_", "DariusShowcase")):
        killed.append(n); actor_sub.destroy_actor(a)
L("清理: %s" % killed)

sm = unreal.load_asset("/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")

# --- A: 用手部世界变换（复现手上那把）---
HAND_LOC = unreal.Vector(7.549233, -70.905591, 118.293288)
HAND_ROT = unreal.Rotator(pitch=6.668431, yaw=165.058254, roll=-137.516973)
aA = actor_sub.spawn_actor_from_class(unreal.StaticMeshActor, HAND_LOC, HAND_ROT)
aA.set_actor_label("XYZ_hand")
aA.static_mesh_component.set_editor_property("static_mesh", sm)
aA.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
L("A hand-transform: loc=%s rot=%s" % (aA.get_actor_location(), aA.get_actor_rotation()))

# --- B: 原点无旋转（复现 CAP_side 里完整那把）---
aB = actor_sub.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0.0, 320.0, 60.0),
                                      unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
aB.set_actor_label("XYZ_origin")
aB.static_mesh_component.set_editor_property("static_mesh", sm)
aB.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
L("B origin: loc=%s rot=%s" % (aB.get_actor_location(), aB.get_actor_rotation()))

for c in (aA, aB):
    comp = c.static_mesh_component
    L("%s: world_scale=%s num_mat=%d mat0=%s" % (
        c.get_actor_label(), comp.get_world_scale(), comp.get_num_materials(),
        comp.get_material(0).get_path_name() if comp.get_material(0) else None))
    try:
        bb = comp.get_local_bounds()
        L("   local_bounds=%s" % (bb,))
    except Exception as e:
        L("   lb err %s" % e)

if not unreal.EditorAssetLibrary.does_directory_exist("/Game/Temp"):
    unreal.EditorAssetLibrary.make_directory("/Game/Temp")
rt = unreal.load_asset("/Game/Temp/RT_AxeCap")
if rt is None:
    rt = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "RT_AxeCap", "/Game/Temp", unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew())
rt.set_editor_property("size_x", 1400); rt.set_editor_property("size_y", 900)

out = "E:/UE/Fight/Saved/Shots/AxeAudit"
os.makedirs(out, exist_ok=True)
sc_class = unreal.load_class(None, "/Script/Engine.SceneCapture2D")
ca = actor_sub.spawn_actor_from_class(sc_class, unreal.Vector(-900.0, 130.0, 200.0),
                                      unreal.Rotator(pitch=-6.0, yaw=0.0, roll=0.0))
ca.set_actor_label("SceneCapture2D_xyz")
cap = ca.capture_component2d
cap.set_editor_property("texture_target", rt)
cap.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cap.set_editor_property("fov_angle", 50.0)
cap.set_editor_property("capture_every_frame", False)

def snap(tag, loc, pitch, yaw):
    ca.set_actor_location(unreal.Vector(*loc), False, False)
    ca.set_actor_rotation(unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0), False)
    time.sleep(0.4)
    cap.capture_scene(); time.sleep(0.9)
    unreal.RenderingLibrary.export_render_target(ew, rt, out, "XYZ_" + tag)
    L("snap XYZ_%s" % tag)

snap("wide", (-900.0, 130.0, 200.0), -6.0, 0.0)
snap("hand_only", (-620.0, -20.0, 140.0), -2.0, 4.0)
snap("origin_only", (-620.0, 330.0, 100.0), -2.0, 0.0)
L("=== DONE ===")
