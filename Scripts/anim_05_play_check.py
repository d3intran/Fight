import unreal, os, time

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
print("world:", gw.get_name() if gw else None)

pc = unreal.GameplayStatics.get_player_controller(gw, 0)
pawn = unreal.GameplayStatics.get_player_pawn(gw, 0)
print("pc:", pc, "pawn:", pawn.get_name() if pawn else None)
if pawn is None:
    for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
        if "BP_DariusCharacter" in a.get_name():
            pawn = a
            print("fallback pawn:", pawn.get_name())

good = unreal.Vector(479.96, 301.90, 132.0)
if pawn:
    pawn.set_actor_location(good, False, False)
    try:
        cm = pawn.get_component_by_class(unreal.CharacterMovementComponent)
        cm.set_editor_property("movement_mode", unreal.MovementMode.MOVE_Flying)
        print("movement set to flying (禁用重力)")
    except Exception as e:
        print("cm err:", e)

seq = unreal.load_asset("/Game/Character/Darius/Anims/A_Darius_LOL_Run_TP")
print("seq:", seq)
mesh = pawn.get_component_by_class(unreal.SkeletalMeshComponent) if pawn else None
if mesh and seq:
    mesh.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    mesh.set_anim_single_node_anim_sequence(seq)
    print("anim set")

for cmd in ["t.IdleWhenNotForeground 0", "ShowFlag.Selection 0"]:
    unreal.SystemLibrary.execute_console_command(gw, cmd)

out = "E:/UE/Fight/Saved/Shots"
shots = [("RUN_back", unreal.Rotator(-5, 0, 0)),
         ("RUN_side", unreal.Rotator(-5, 95, 0)),
         ("RUN_front", unreal.Rotator(-5, 180, 0))]
for name, rot in shots:
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
