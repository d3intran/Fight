# -*- coding: utf-8 -*-
"""复位视口 + 重试编辑器截图（带长等待与多次重试）"""
import unreal, os, time

def L(s=""):
    unreal.log(str(s))

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()

L("viewport config keys: %s" % list(les.get_viewport_config_keys()))
L("in PIE: %s" % les.is_in_play_in_editor())

# ---- 复位视口（回透视、关游戏视图、开实时、归位相机）----
for k in les.get_viewport_config_keys():
    try:
        les.editor_set_game_view(False, k)
    except Exception as e:
        L("  game view off err %s" % e)
    try:
        les.editor_set_viewport_realtime(True, k)
    except Exception as e:
        L("  realtime err %s" % e)
    try:
        les.set_level_viewport_camera_info(unreal.Vector(-1200, -1200, 900), unreal.Rotator(-30, 45, 0), k)
    except Exception as e:
        L("  cam err %s" % e)
for cmd in ["t.IdleWhenNotForeground 0", "Editor.bThrottleWhenHidden 0", "r.Editor.Viewport.Throttle 0"]:
    unreal.SystemLibrary.execute_console_command(ew, cmd)
les.editor_invalidate_viewports()
time.sleep(1.5)
L("viewport reset done")

# ---- 临时角色 + 相机 ----
for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith(("TempAudit_", "AxeProxy", "AxeCap_", "CameraActor_Shot")):
        actor_sub.destroy_actor(a)

bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
actor = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125), unreal.Rotator(0, 0, 180))
actor.set_actor_label("TempAudit_Darius")
actor_sub.set_selected_level_actors([])
L("spawned %s" % actor.get_name())

cam_class = unreal.load_class(None, "/Script/Engine.CameraActor")
out = "E:/UE/Fight/Saved/Shots/AxeAudit"
os.makedirs(out, exist_ok=True)

specs = [
    ("Z1_right34", (-380.0, -330.0, 190.0), unreal.Rotator(-10.0, 41.0, 0.0), 40.0),
    ("Z2_right_side", (-60.0, -430.0, 170.0), unreal.Rotator(-6.0, 82.0, 0.0), 40.0),
    ("Z3_front", (-450.0, -140.0, 175.0), unreal.Rotator(-8.0, 17.0, 0.0), 42.0),
    ("Z4_hand_close", (-140.0, -260.0, 150.0), unreal.Rotator(-8.0, 60.0, 0.0), 45.0),
]
for name, loc, rot, fov in specs:
    cam = actor_sub.spawn_actor_from_class(cam_class, unreal.Vector(*loc), rot)
    cam.set_actor_label("CameraActor_Shot_" + name)
    try:
        cam.camera_component.set_editor_property("field_of_view", fov)
    except Exception:
        pass
    p = "%s/%s.png" % (out, name)
    if os.path.exists(p):
        os.remove(p)
    for attempt in range(3):
        unreal.AutomationLibrary.take_high_res_screenshot(1400, 900, p, cam, False)
        for _ in range(10):
            time.sleep(1.0)
            if os.path.exists(p) and os.path.getsize(p) > 10000:
                break
        if os.path.exists(p) and os.path.getsize(p) > 10000:
            break
        L("  retry %s (%d)" % (name, attempt))
    L("shot %s -> exists=%s size=%s" % (name, os.path.exists(p), os.path.getsize(p) if os.path.exists(p) else -1))
    actor_sub.destroy_actor(cam)
L("=== DONE ===")
