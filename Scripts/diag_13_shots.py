import unreal, os, time

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()

actors = [a for a in actor_sub.get_all_level_actors() if "BP_DariusCharacter" in a.get_name()]
actor = actors[-1]
actor.set_actor_location(unreal.Vector(0, 0, 125), False, False)
actor.set_actor_rotation(unreal.Rotator(0, 0, 180), False)
weapon = None
for c in actor.get_components_by_class(unreal.StaticMeshComponent):
    if "Weapon" in c.get_name() or "Axe" in c.get_name():
        weapon = c
print("weapon worldScale:", weapon.get_world_scale() if weapon else None)

actor_sub.set_selected_level_actors([])
for a in actor_sub.get_all_level_actors():
    if "ShotCam" in a.get_name():
        actor_sub.destroy_actor(a)

cam_class = unreal.load_class(None, "/Script/Engine.CameraActor")
out_dir = r"E:/UE/Fight/Saved/Shots"
os.makedirs(out_dir, exist_ok=True)

def shoot(name, cam_loc, cam_rot):
    cam = actor_sub.spawn_actor_from_class(cam_class, unreal.Vector(*cam_loc), unreal.Rotator(*cam_rot))
    cam.set_actor_label("ShotCam_" + name)
    try:
        cam.camera_component.set_editor_property("field_of_view", 45.0)
    except Exception as e:
        print("fov err", e)
    p = f"{out_dir}/{name}.png"
    if os.path.exists(p):
        os.remove(p)
    unreal.AutomationLibrary.take_high_res_screenshot(1600, 900, p, cam, False)
    time.sleep(2.5)
    print("shot ->", p, "exists:", os.path.exists(p))
    actor_sub.destroy_actor(cam)

shoot("BEFORE_front", (-430.0, -300.0, 175.0), (-8.0, 35.0, 0.0))
shoot("BEFORE_wide",  (-760.0, -560.0, 330.0), (-15.0, 36.0, 0.0))
print("DONE")
