# -*- coding: utf-8 -*-
"""用已标定的求解器渲染两个候选握持姿态"""
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
    if a.get_name().startswith(("BP_DariusCharacter", "FIX_", "SceneCapture2D_",
                                "StaticMeshActor_0", "StaticMeshActor_5", "StaticMeshActor_6",
                                "XYZ_", "ABTest_")):
        actor_sub.destroy_actor(a)

bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
sk = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
sock = sk.find_socket(unreal.Name("hand_rSocket"))

if not unreal.EditorAssetLibrary.does_directory_exist("/Game/Temp"):
    unreal.EditorAssetLibrary.make_directory("/Game/Temp")
rt = unreal.load_asset("/Game/Temp/RT_AxeCap")
if rt is None:
    rt = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "RT_AxeCap", "/Game/Temp", unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew())
rt.set_editor_property("size_x", 1200); rt.set_editor_property("size_y", 900)
out = "E:/UE/Fight/Saved/Shots/AxeAudit"
os.makedirs(out, exist_ok=True)
sc_class = unreal.load_class(None, "/Script/Engine.SceneCapture2D")
ca = actor_sub.spawn_actor_from_class(sc_class, unreal.Vector(-560.0, -110.0, 150.0), R(0.0, 0.0, 0.0))
ca.set_actor_label("SceneCapture2D_v")
cap = ca.capture_component2d
cap.set_editor_property("texture_target", rt)
cap.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cap.set_editor_property("fov_angle", 52.0)
cap.set_editor_property("capture_every_frame", False)

VAR = {
 "V_A_up":   (R(-106.3340, -70.9820, 9.3420), unreal.Vector(0.18965, 0.10080, 0.00982)),
 "V_B_down": (R(-73.6660, 108.9160, 9.4440), unreal.Vector(-0.18966, -0.10078, -0.00992)),
 "V_C_orig": (R(90.0, 0.0, 0.0),              unreal.Vector(0.0, 0.0, 0.0)),
}
ORDER = ["V_A_up", "V_B_down"]

for tag in ORDER:
    rrot, rloc = VAR[tag]
    sock.set_editor_property("relative_rotation", rrot)
    sock.set_editor_property("relative_location", rloc)
    sock.set_editor_property("relative_scale", unreal.Vector(0.01, 0.01, 0.01))
    for a in actor_sub.get_all_level_actors():
        if a.get_name().startswith(("FIX_show", "FIX_probe")):
            actor_sub.destroy_actor(a)
    act = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125), R(0.0, 180.0, 0.0))
    act.set_actor_label("FIX_show")
    L("=== %s ===" % tag)
    for nm, loc, pitch, yaw in [("side", (-560.0, -110.0, 150.0), 0.0, 0.0),
                                ("front", (0.0, -620.0, 160.0), -3.0, 90.0)]:
        ca.set_actor_location(unreal.Vector(*loc), False, False)
        ca.set_actor_rotation(R(pitch, yaw, 0.0), False)
        time.sleep(0.4)
        cap.capture_scene(); time.sleep(0.8)
        unreal.RenderingLibrary.export_render_target(ew, rt, out, "%s_%s" % (tag, nm))
        L("  拍 %s_%s" % (tag, nm))
L("=== DONE ===")
