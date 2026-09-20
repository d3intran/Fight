import unreal, os, time
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()

for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith("CameraActor_") or a.get_name().startswith("BP_DariusCharacter"):
        actor_sub.destroy_actor(a)

bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
actor = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125), unreal.Rotator(0, 0, 180))
print("spawned:", actor.get_name())
actor_sub.set_selected_level_actors([])

cam_class = unreal.load_class(None, "/Script/Engine.CameraActor")
out = "E:/UE/Fight/Saved/Shots"
os.makedirs(out, exist_ok=True)
specs = [("FIX_feet", (-330.0, -210.0, 120.0), unreal.Rotator(-22.0, 32.0, 0.0), 45.0),
         ("FIX_full", (-430.0, -290.0, 180.0), unreal.Rotator(-8.0, 34.0, 0.0), 42.0)]
paths = []
for name, loc, rot, fov in specs:
    cam = actor_sub.spawn_actor_from_class(cam_class, unreal.Vector(*loc), rot)
    cam.set_actor_label("CameraActor_Shot_" + name)
    try:
        cam.camera_component.set_editor_property("field_of_view", fov)
    except Exception:
        pass
    p = f"{out}/{name}.png"
    if os.path.exists(p):
        os.remove(p)
    unreal.AutomationLibrary.take_high_res_screenshot(1500, 950, p, cam, False)
    paths.append(p)
    print("requested", p)
    time.sleep(1.0)
print("paths:", paths)
print("=== DONE ===")
