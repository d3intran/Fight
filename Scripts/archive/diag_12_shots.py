import unreal, os, time

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()

actors = [a for a in actor_sub.get_all_level_actors() if "BP_DariusCharacter" in a.get_name()]
print("darius actors:", [a.get_name() for a in actors])
actor = actors[-1]
actor.set_actor_location(unreal.Vector(0, 0, 125), False, False)
actor.set_actor_rotation(unreal.Rotator(0, 0, 180), False)
weapon = None
for c in actor.get_components_by_class(unreal.StaticMeshComponent):
    if "Weapon" in c.get_name() or "Axe" in c.get_name():
        weapon = c
print("weapon worldScale:", weapon.get_world_scale() if weapon else None)

actor_sub.set_selected_level_actors([])
out_dir = r"E:/UE/Fight/Saved/Shots"
os.makedirs(out_dir, exist_ok=True)
unreal.SystemLibrary.execute_console_command(ew, "t.IdleWhenNotForeground 0")

def shoot(name, cam_loc, cam_rot):
    for k in les.get_viewport_config_keys():
        les.set_level_viewport_camera_info(unreal.Vector(*cam_loc), unreal.Rotator(*cam_rot), k)
        try:
            les.editor_set_game_view(True, k)
            les.editor_set_viewport_realtime(True, k)
        except Exception:
            pass
    les.editor_invalidate_viewports()
    time.sleep(0.5)
    p = f"{out_dir}/{name}.png"
    if os.path.exists(p):
        os.remove(p)
    unreal.AutomationLibrary.take_high_res_screenshot(1600, 900, p, False)
    time.sleep(2.5)
    print("shot ->", p, "exists:", os.path.exists(p))

shoot("BEFORE_front", (-430.0, -300.0, 175.0), (-8.0, 35.0, 0.0))
shoot("BEFORE_wide",  (-760.0, -560.0, 330.0), (-15.0, 36.0, 0.0))
print("DONE")
