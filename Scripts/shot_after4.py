import unreal, os, time

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
out = "E:/UE/Fight/Saved/Shots"
os.makedirs(out, exist_ok=True)

# 干掉编辑器残留副本
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "BP_DariusCharacter" in a.get_name() and a.get_actor_location().z < -1000:
        print("destroying fallen:", a.get_name())
        a.destroy_actor()

pawn = None
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "BP_DariusCharacter" in a.get_name():
        pawn = a
print("pawn:", pawn.get_name() if pawn else None)

good = unreal.Vector(479.96, 301.90, 130.0)
pc = unreal.GameplayStatics.get_player_controller(gw, 0)
for cmd in ["t.IdleWhenNotForeground 0", "ShowFlag.Selection 0"]:
    unreal.SystemLibrary.execute_console_command(gw, cmd)

shots = [("AFTER_back", unreal.Rotator(0, 0, 0)),
         ("AFTER_front", unreal.Rotator(-8, 180, 0)),
         ("AFTER_side", unreal.Rotator(-8, 95, 0))]
for name, rot in shots:
    if pawn:
        pawn.set_actor_location(good, False, False)
    if pc:
        pc.set_control_rotation(rot)
    time.sleep(1.5)
    if pawn:
        print(name, "pawn z:", pawn.get_actor_location().z)
        for c in pawn.get_components_by_class(unreal.StaticMeshComponent):
            if "Weapon" in c.get_name():
                print("   weapon worldScale:", c.get_world_scale())
    p = f"{out}/{name}.png"
    if os.path.exists(p):
        os.remove(p)
    unreal.SystemLibrary.execute_console_command(gw, f'HighResShot 1600x900 filename="{p}"')
    time.sleep(2.5)
print("=== DONE ===")
