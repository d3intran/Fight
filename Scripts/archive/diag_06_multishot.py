import unreal, os, math, time

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
out_dir = r"E:/UE/Fight/Saved/Shots"
os.makedirs(out_dir, exist_ok=True)

for cmd in ["t.IdleWhenNotForeground 0", "r.Editor.Viewport.Throttle 0", "Editor.bThrottleWhenHidden 0",
            "showflag.Billboard 0", "showflag.Selection 0"]:
    unreal.SystemLibrary.execute_console_command(gw, cmd)

darius = None
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "BP_DariusCharacter" in a.get_name():
        darius = a
        break

loc = darius.get_actor_location()
rot = darius.get_actor_rotation()
print("Darius loc:", loc, "rot:", rot)

# 清掉旧相机
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.CameraActor):
    a.destroy_actor()
time.sleep(0.2)

cam_class = unreal.load_class(None, "/Script/Engine.CameraActor")

def shoot(name, offset, target_offset, fov=50.0):
    cam = unreal.GameplayStatics.begin_spawn_actor_from_class(gw, cam_class, loc, unreal.Rotator(0, 0, 0))
    cam.set_actor_label("ShotCam_" + name)
    # 让相机沿角色朝向旋转偏移
    yaw_rad = math.radians(rot.yaw)
    ox = offset[0] * math.cos(yaw_rad) - offset[1] * math.sin(yaw_rad)
    oy = offset[0] * math.sin(yaw_rad) + offset[1] * math.cos(yaw_rad)
    cam_loc = unreal.Vector(loc.x + ox, loc.y + oy, loc.z + offset[2])
    tx = target_offset[0] * math.cos(yaw_rad) - target_offset[1] * math.sin(yaw_rad)
    ty = target_offset[0] * math.sin(yaw_rad) + target_offset[1] * math.cos(yaw_rad)
    tgt = unreal.Vector(loc.x + tx, loc.y + ty, loc.z + target_offset[2])
    cam.set_actor_location(cam_loc, False, False)
    cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam_loc, tgt), False)
    try:
        cam.camera_component.set_editor_property("field_of_view", fov)
    except Exception as e:
        print("fov err", e)
    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    pc.set_view_target(cam)
    time.sleep(0.4)
    p = f"{out_dir}/{name}.png"
    if os.path.exists(p):
        os.remove(p)
    unreal.SystemLibrary.execute_console_command(gw, f'HighResShot 1600x900 filename="{p}"')
    time.sleep(1.6)
    print("shot:", name, "camLoc:", cam_loc, "->", tgt)
    return cam

# offset 是角色本地空间 (X=前, Y=右, Z=上)
shoot("A_front_full",   (520.0, -330.0, 150.0), (0.0, 0.0, 110.0), 45.0)
shoot("B_hand_closeup", (110.0, -95.0, 175.0),  (40.0, 30.0, 125.0), 50.0)
shoot("C_feet_ground",  (330.0, -230.0, 35.0),  (0.0, 0.0, 20.0), 55.0)
shoot("D_back_full",    (-470.0, 0.0, 160.0),   (0.0, 0.0, 110.0), 45.0)
print("ALL DONE")
