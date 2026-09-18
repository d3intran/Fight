import unreal, os, time

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
print("world:", gw.get_name() if gw else None)
if gw is None:
    print("NOT IN PIE")
else:
    pawn = unreal.GameplayStatics.get_player_pawn(gw, 0)
    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    print("pawn:", pawn.get_name() if pawn else None)
    good = unreal.Vector(479.96, 301.90, 132.0)
    if pawn:
        pawn.set_actor_location(good, False, False)
    seq = unreal.load_asset("/Game/Character/Darius/Anims/A_Darius_LOL_Run_TP")
    mesh = pawn.get_component_by_class(unreal.SkeletalMeshComponent) if pawn else None
    if mesh and seq:
        mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        mesh.set_animation(seq)
        print("set_animation OK")
        print("  anim mode:", mesh.get_editor_property("animation_mode"))
    for cmd in ["t.IdleWhenNotForeground 0", "ShowFlag.Selection 0"]:
        unreal.SystemLibrary.execute_console_command(gw, cmd)
    out = "E:/UE/Fight/Saved/Shots"
    for name, rot in [("RUN_side", unreal.Rotator(-6, 95, 0)), ("RUN_front34", unreal.Rotator(-6, 140, 0))]:
        if pc:
            pc.set_control_rotation(rot)
        if pawn:
            pawn.set_actor_location(good, False, False)
        time.sleep(1.2)
        p = f"{out}/{name}.png"
        if os.path.exists(p):
            os.remove(p)
        unreal.SystemLibrary.execute_console_command(gw, f'HighResShot 1400x900 filename="{p}"')
        time.sleep(2.0)
print("=== DONE ===")
