import unreal, os, time

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ew = ues.get_editor_world()

for a in actor_sub.get_all_level_actors():
    n = a.get_name()
    if n.startswith("CameraActor_") or n.startswith("BP_DariusCharacter") or n.startswith("ShotCam") or n.startswith("TestCamera"):
        actor_sub.destroy_actor(a)

print("剩余 Actor:")
for a in actor_sub.get_all_level_actors():
    print("   ", a.get_name(), "|", a.get_class().get_name())

# 展示用角色 + 相机
bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
actor = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125), unreal.Rotator(0, 0, 180))
actor.set_actor_label("DariusShowcase")
actor_sub.set_selected_level_actors([])

cam_class = unreal.load_class(None, "/Script/Engine.CameraActor")
out = "E:/UE/Fight/Saved/Shots"
os.makedirs(out, exist_ok=True)
for name, loc, rot, fov in [
    ("SHOW_full", (-430.0, -300.0, 175.0), unreal.Rotator(-7.0, 34.0, 0.0), 42.0),
    ("SHOW_feet", (-300.0, -200.0, 95.0), unreal.Rotator(-14.0, 33.0, 0.0), 48.0)]:
    cam = actor_sub.spawn_actor_from_class(cam_class, unreal.Vector(*loc), rot)
    cam.set_actor_label("CameraActor_Show_" + name)
    try:
        cam.camera_component.set_editor_property("field_of_view", fov)
    except Exception:
        pass
    p = f"{out}/{name}.png"
    if os.path.exists(p):
        os.remove(p)
    unreal.AutomationLibrary.take_high_res_screenshot(1500, 950, p, cam, False)
    print("requested", p)
    time.sleep(1.2)
print("=== DONE ===")
