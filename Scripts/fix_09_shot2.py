import unreal, os, time
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
if gw is None:
    print("NOT IN PIE")
else:
    pawn = unreal.GameplayStatics.get_player_pawn(gw, 0)
    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    boom = pawn.get_component_by_class(unreal.SpringArmComponent)
    print("boom arm length:", boom.get_editor_property("target_arm_length"))
    cam = pawn.get_component_by_class(unreal.CameraComponent)
    print("camera rel loc:", cam.get_editor_property("relative_location"))
    good = unreal.Vector(479.96, 301.90, 132.0)
    for cmd in ["t.IdleWhenNotForeground 0", "ShowFlag.Selection 0"]:
        unreal.SystemLibrary.execute_console_command(gw, cmd)
    out = "E:/UE/Fight/Saved/Shots"
    for name, rot in [("FIX2_down45", unreal.Rotator(-45, 95, 0)), ("FIX2_down60", unreal.Rotator(-60, 95, 0))]:
        pc.set_control_rotation(rot)
        pawn.set_actor_location(good, False, False)
        time.sleep(2.0)
        print(name, "cam world:", cam.get_world_location())
        p = f"{out}/{name}.png"
        if os.path.exists(p): os.remove(p)
        unreal.SystemLibrary.execute_console_command(gw, f'HighResShot 1400x900 filename="{p}"')
        time.sleep(2.5)
print("=== DONE ===")
