# -*- coding: utf-8 -*-
"""PIE 内截图：角色 + 战斧"""
import unreal, os, time

def L(s=""):
    unreal.log(str(s))

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
gw = ues.get_game_world()
L("game world: %s   in PIE=%s" % (gw, les.is_in_play_in_editor()))

ew = ues.get_editor_world()
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# PIE 世界的 actor 子系统
gaw = unreal.GameplayStatics

out = "E:/UE/Fight/Saved/Shots/AxeAudit"
os.makedirs(out, exist_ok=True)

pawn = None
for a in gaw.get_all_actors_of_class(gw, unreal.Actor):
    n = a.get_name()
    if "Darius" in n and "Character" in n:
        pawn = a
        L("pawn: %s at %s" % (n, a.get_actor_location()))
L("pawn=%s" % (pawn.get_name() if pawn else None))

# 找一个能看到角色右手的机位（角色面朝 -Y 或 +Y，逐机位试）
pc = gaw.get_player_controller(gw, 0)
L("pc=%s" % pc)

def shot(tag, cam_loc, cam_rot, fov=45.0):
    cam_class = unreal.load_class(None, "/Script/Engine.CameraActor")
    cam = gaw.begin_spawn_actor_from_class(gw, cam_class, unreal.Vector(*cam_loc), cam_rot)
    try:
        cam.camera_component.set_editor_property("field_of_view", fov)
    except Exception as e:
        L("  fov err %s" % e)
    p = "%s/%s.png" % (out, tag)
    if os.path.exists(p):
        os.remove(p)
    unreal.AutomationLibrary.take_high_res_screenshot(1440, 900, p, cam, False)
    L("shot %s -> %s" % (tag, p))
    return cam

cams = []
cams.append(shot("P1_right34", (-330.0, -300.0, 175.0), unreal.Rotator(-8.0, 42.0, 0.0)))
cams.append(shot("P2_right_side", (-30.0, -400.0, 160.0), unreal.Rotator(-5.0, 86.0, 0.0)))
cams.append(shot("P3_left_side", (-30.0, 400.0, 160.0), unreal.Rotator(-5.0, -86.0, 0.0)))
cams.append(shot("P4_front", (-420.0, -100.0, 165.0), unreal.Rotator(-7.0, 13.0, 0.0)))
L("cams spawned: %d" % len(cams))
L("=== DONE ===")
