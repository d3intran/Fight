# -*- coding: utf-8 -*-
"""角色手持战斧实拍（修正 Rotator 参数顺序：必须用关键字）"""
import unreal, os, time

def L(s=""):
    unreal.log(str(s))

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if les.is_in_play_in_editor():
    les.editor_request_end_play()
    L("!! PIE 未结束，稍后重跑")
    raise SystemExit

# 彻底清场
killed = []
for a in actor_sub.get_all_level_actors():
    n = a.get_name()
    if n.startswith(("BP_DariusCharacter", "AXE_", "CameraActor_", "AxeProxy", "AxeCap_",
                     "StaticMeshActor_0", "StaticMeshActor_5", "StaticMeshActor_6",
                     "TempAudit_", "DariusShowcase", "SceneCapture2D_0")):
        killed.append(n)
        actor_sub.destroy_actor(a)
L("清理: %s" % killed)

bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
actor = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125), unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0))
actor.set_actor_label("AXE_Showcase")
actor_sub.set_selected_level_actors([])

for cmd in ["showflag.Billboard 0", "showflag.Selection 0", "t.IdleWhenNotForeground 0"]:
    unreal.SystemLibrary.execute_console_command(None, cmd)

out = "E:/UE/Fight/Saved/Shots/AxeAudit"
os.makedirs(out, exist_ok=True)

cam_class = unreal.load_class(None, "/Script/Engine.CameraActor")
# 角色在 (0,0,125) 面朝 -Y；右手/斧头在 -Y 侧
SHOTS = [
    ("W1_front",     (-20.0, -470.0, 150.0),  -4.0, 90.0),
    ("W2_right",     (-480.0, -120.0, 150.0), -4.0, 0.0),
    ("W3_q34",       (-350.0, -400.0, 170.0), -6.0, 45.0),
    ("W4_topdown",   (0.0, -70.0, 620.0),     -80.0, 90.0),
    ("W5_hand_area", (-140.0, -430.0, 130.0), -4.0, 72.0),
]
cams = []
for nm, loc, pitch, yaw in SHOTS:
    cam = actor_sub.spawn_actor_from_class(cam_class, unreal.Vector(*loc),
                                           unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0))
    cam.set_actor_label("CameraActor_" + nm)
    try:
        cam.camera_component.set_editor_property("field_of_view", 46.0)
    except Exception:
        pass
    cams.append((nm, cam))
    L("cam %s @ (%.0f,%.0f,%.0f) pitch=%.0f yaw=%.0f" % (nm, loc[0], loc[1], loc[2], pitch, yaw))

# 用 Simulate 激活完整渲染管线（项目里已验证可行）
les.editor_play_simulate()
time.sleep(1.5)
L("simulate started")

for nm, cam in cams:
    p = "%s/%s.png" % (out, nm)
    if os.path.exists(p):
        os.remove(p)
    unreal.SystemLibrary.execute_console_command(None, 'HighResShot 1440x900 filename="%s"' % p)
    L("HighResShot %s" % p)
    time.sleep(1.0)

les.editor_request_end_play()
L("simulate ended")
L("=== DONE ===")
