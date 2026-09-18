import unreal, os, time

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
if gw is None:
    print("NOT IN PIE")
else:
    pawn = unreal.GameplayStatics.get_player_pawn(gw, 0)
    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    print("pawn:", pawn.get_name() if pawn else None)
    boom = pawn.get_component_by_class(unreal.SpringArmComponent)
    if boom:
        boom.set_editor_property("target_arm_length", 700.0)
        boom.set_editor_property("socket_offset", unreal.Vector(0, 0, 130))
        boom.set_editor_property("do_collision_test", False)
        print("boom len set 700")
    seq = unreal.load_asset("/Game/Character/Darius/Anims/A_Darius_LOL_Run_TP")
    mesh = pawn.get_component_by_class(unreal.SkeletalMeshComponent)
    mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    mesh.set_animation(seq)
    good = unreal.Vector(0.0, 0.0, 132.0)
    for cmd in ["t.IdleWhenNotForeground 0", "ShowFlag.Selection 0"]:
        unreal.SystemLibrary.execute_console_command(gw, cmd)
    out = "E:/UE/Fight/Saved/Shots"
    for name, rot in [("RUN2_side", unreal.Rotator(-10, 95, 0)), ("RUN2_front34", unreal.Rotator(-10, 150, 0))]:
        if pc:
            pc.set_control_rotation(rot)
        pawn.set_actor_location(good, False, False)
        time.sleep(1.5)
        p = f"{out}/{name}.png"
        if os.path.exists(p):
            os.remove(p)
        unreal.SystemLibrary.execute_console_command(gw, f'HighResShot 1400x900 filename="{p}"')
        time.sleep(2.2)
print("=== DONE ===")
