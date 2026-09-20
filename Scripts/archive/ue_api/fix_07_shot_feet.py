import unreal, os, time
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
if gw is None:
    print("NOT IN PIE"); 
else:
    pawn = unreal.GameplayStatics.get_player_pawn(gw, 0)
    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    print("pawn:", pawn.get_name() if pawn else None)
    boom = pawn.get_component_by_class(unreal.SpringArmComponent)
    if boom:
        boom.set_editor_property("target_arm_length", 420.0)
        boom.set_editor_property("socket_offset", unreal.Vector(0, 0, 60))
        boom.set_editor_property("do_collision_test", False)
    good = unreal.Vector(479.96, 301.90, 132.0)
    pawn.set_actor_location(good, False, False)
    for cmd in ["t.IdleWhenNotForeground 0", "ShowFlag.Selection 0"]:
        unreal.SystemLibrary.execute_console_command(gw, cmd)
    out = "E:/UE/Fight/Saved/Shots"
    for name, rot in [("FEET_down", unreal.Rotator(-38, 95, 0)), ("FEET_front", unreal.Rotator(-30, 180, 0))]:
        pc.set_control_rotation(rot)
        pawn.set_actor_location(good, False, False)
        time.sleep(1.5)
        p = f"{out}/{name}.png"
        if os.path.exists(p): os.remove(p)
        unreal.SystemLibrary.execute_console_command(gw, f'HighResShot 1400x900 filename="{p}"')
        time.sleep(2.2)
print("=== DONE ===")
