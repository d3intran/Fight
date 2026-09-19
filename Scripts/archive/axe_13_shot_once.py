# -*- coding: utf-8 -*-
"""单次拍摄：读取 shot_request.txt（name,locX,locY,locZ,pitch,yaw,fov）拍一张
编辑器每次只认最后一条 HighResShot，因此一次运行只拍一张。"""
import unreal, os, time

def L(s=""):
    unreal.log(str(s))

REQ = "E:/UE/Fight/Saved/Shots/AxeAudit/shot_request.txt"
out = "E:/UE/Fight/Saved/Shots/AxeAudit"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if les.is_in_play_in_editor():
    les.editor_request_end_play()
    L("!! PIE 未结束")
    raise SystemExit

with open(REQ, "r", encoding="utf-8") as f:
    parts = [x.strip() for x in f.read().strip().split(",")]
name = parts[0]
loc = unreal.Vector(float(parts[1]), float(parts[2]), float(parts[3]))
pitch, yaw, fov = float(parts[4]), float(parts[5]), float(parts[6])
cam_rot = unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)
L("REQUEST %s loc=(%.0f,%.0f,%.0f) pitch=%.1f yaw=%.1f fov=%.1f" % (name, loc.x, loc.y, loc.z, pitch, yaw, fov))

# 清理旧相机
for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith("CameraActor_ONESHOT"):
        actor_sub.destroy_actor(a)

cam_class = unreal.load_class(None, "/Script/Engine.CameraActor")
cam = actor_sub.spawn_actor_from_class(cam_class, loc, cam_rot)
cam.set_actor_label("CameraActor_ONESHOT")
try:
    cam.camera_component.set_editor_property("field_of_view", fov)
except Exception as e:
    L("fov err %s" % e)
actor_sub.set_selected_level_actors([])
for cmd in ["showflag.Billboard 0", "showflag.Selection 0", "t.IdleWhenNotForeground 0"]:
    unreal.SystemLibrary.execute_console_command(None, cmd)

p = "%s/%s.png" % (out, name)
if os.path.exists(p):
    os.remove(p)
unreal.AutomationLibrary.take_high_res_screenshot(1440, 900, p, cam, False)
L("take_high_res_screenshot -> %s" % p)
L("=== DONE (文件会延迟 1~3 分钟落地) ===")
