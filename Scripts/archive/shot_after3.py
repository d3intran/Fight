import unreal, os, time

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()
print("world:", ew.get_name() if ew else None)

for a in actor_sub.get_all_level_actors():
    if "ShotCam" in a.get_name():
        actor_sub.destroy_actor(a)

actors = [a for a in actor_sub.get_all_level_actors() if "BP_DariusCharacter" in a.get_name()]
print("darius actors:", [(a.get_name(), a.get_actor_location()) for a in actors])
for a in actors[1:]:
    actor_sub.destroy_actor(a)
actor = actors[0]
actor.set_actor_location(unreal.Vector(0, 0, 125), False, False)
actor.set_actor_rotation(unreal.Rotator(0, 0, 180), False)
for c in actor.get_components_by_class(unreal.StaticMeshComponent):
    if "Weapon" in c.get_name():
        print("WeaponAxe worldScale:", c.get_world_scale(), "loc:", c.get_world_location())

actor_sub.set_selected_level_actors([])
unreal.SystemLibrary.execute_console_command(ew, "t.IdleWhenNotForeground 0")
out = "E:/UE/Fight/Saved/Shots"
cam_class = unreal.load_class(None, "/Script/Engine.CameraActor")

specs = [
    ("AFTER_front", (-380.0, -260.0, 170.0), unreal.Rotator(-7.0, 34.0, 0.0), 40.0),
    ("AFTER_hand",  (-130.0, -110.0, 140.0), unreal.Rotator(-10.0, 52.0, 0.0), 50.0),
    ("AFTER_feet",  (-230.0, -140.0, 50.0),  unreal.Rotator(0.0, 34.0, 0.0), 55.0),
]
paths = []
for name, loc, rot, fov in specs:
    cam = actor_sub.spawn_actor_from_class(cam_class, unreal.Vector(*loc), rot)
    cam.set_actor_label("ShotCam_" + name)
    try:
        cam.camera_component.set_editor_property("field_of_view", fov)
    except Exception as e:
        print("fov err", e)
    p = f"{out}/{name}.png"
    if os.path.exists(p):
        os.remove(p)
    unreal.AutomationLibrary.take_high_res_screenshot(1600, 900, p, cam, False)
    paths.append(p)
    print("requested", p)
    time.sleep(1.0)

# 轮询等待落盘
deadline = time.time() + 45
while time.time() < deadline:
    if all(os.path.exists(p) for p in paths):
        break
    time.sleep(1.0)
for p in paths:
    print(p, "->", os.path.exists(p), os.path.getsize(p) if os.path.exists(p) else 0)
print("=== DONE ===")
