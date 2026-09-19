# -*- coding: utf-8 -*-
"""用编辑器视口相机 + HighResShot 渲染战斧特写（该路径在本项目已验证可用）"""
import unreal, os, time

def L(s=""):
    unreal.log(str(s))

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()

if les.is_in_play_in_editor():
    les.editor_request_end_play()
    L("!! PIE 未结束，稍后重跑")
    raise SystemExit

for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith(("TempAudit_", "AxeView_", "CameraActor_AxeView", "AxeProxy_")):
        actor_sub.destroy_actor(a)

out = "E:/UE/Fight/Saved/Shots/AxeAudit"
os.makedirs(out, exist_ok=True)

for cmd in ["t.IdleWhenNotForeground 0", "showflag.Billboard 0", "showflag.Selection 0"]:
    unreal.SystemLibrary.execute_console_command(ew, cmd)

sm = unreal.load_asset("/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")
mi_axe = unreal.load_asset("/Game/Character/Darius/Materials/MI_Darius_Axe")
default_mat = unreal.load_asset("/Engine/BasicShapes/BasicShapeMaterial")

proxy = actor_sub.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 130), unreal.Rotator(0, 0, 0))
proxy.set_actor_label("AxeProxy")
comp = proxy.static_mesh_component
comp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
comp.set_editor_property("static_mesh", sm)
actor_sub.set_selected_level_actors([])
L("proxy: %s  mesh=%s" % (proxy.get_name(), sm.get_name()))

def shoot(name, cam_loc, cam_rot):
    for k in les.get_viewport_config_keys():
        try:
            les.set_level_viewport_camera_info(unreal.Vector(*cam_loc), unreal.Rotator(*cam_rot), k)
            les.editor_set_game_view(True, k)
            les.editor_set_viewport_realtime(True, k)
        except Exception:
            pass
    les.editor_invalidate_viewports()
    time.sleep(0.6)
    p = "%s/%s.png" % (out, name)
    if os.path.exists(p):
        os.remove(p)
    unreal.SystemLibrary.execute_console_command(ew, 'HighResShot 1200x1200 filename="%s"' % p)
    time.sleep(2.2)
    L("shot -> %s  exists=%s size=%s" % (p, os.path.exists(p), os.path.getsize(p) if os.path.exists(p) else -1))

# 相机在 -X 侧看向 +X；斧头沿 Y 横放
shoot("R1_axeMI_side",   (-620.0, 0.0, 130.0),  (0.0, 0.0, 0.0))
shoot("R2_axeDefault_side", (-620.0, 0.0, 130.0), (0.0, 0.0, 0.0))
L("(R2 需换材质后重拍)")
L("=== DONE ===")
