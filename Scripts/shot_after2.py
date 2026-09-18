import unreal, os, time

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
gw = ues.get_game_world()
print("in pie:", les.is_in_play_in_editor())

out = "E:/UE/Fight/Saved/Shots"
os.makedirs(out, exist_ok=True)

pawn = None
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "BP_DariusCharacter" in a.get_name():
        pawn = a
print("pawn:", pawn.get_name() if pawn else None)
if pawn:
    print("loc:", pawn.get_actor_location())
    for c in pawn.get_components_by_class(unreal.StaticMeshComponent):
        print("   ", c.get_name(), "worldScale:", c.get_world_scale())

for cmd in ["t.IdleWhenNotForeground 0", "ShowFlag.Selection 0"]:
    unreal.SystemLibrary.execute_console_command(gw, cmd)

pc = unreal.GameplayStatics.get_player_controller(gw, 0)
print("pc:", pc)

shots = [("AFTER_back", unreal.Rotator(0, 0, 0)),
         ("AFTER_front", unreal.Rotator(-8, 180, 0)),
         ("AFTER_side", unreal.Rotator(-8, 90, 0))]
for name, rot in shots:
    if pc:
        pc.set_control_rotation(rot)
    time.sleep(1.2)
    p = f"{out}/{name}.png"
    if os.path.exists(p):
        os.remove(p)
    unreal.SystemLibrary.execute_console_command(gw, f'HighResShot 1600x900 filename="{p}"')
    time.sleep(2.5)
    print("shot", name, "exists:", os.path.exists(p))
print("=== DONE ===")
