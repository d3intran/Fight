import unreal, os, time

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
gw = ues.get_game_world()
ew = ues.get_editor_world()
print("in pie:", les.is_in_play_in_editor())
print("game world:", gw.get_name() if gw else None)
print("editor world:", ew.get_name() if ew else None)

out = "E:/UE/Fight/Saved/Shots"
os.makedirs(out, exist_ok=True)

if les.is_in_play_in_editor() and gw:
    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    pawn = pc.pawn if pc else None
    print("pawn:", pawn.get_name() if pawn else None)
    if pawn:
        print("pawn loc:", pawn.get_actor_location())
        for c in pawn.get_components_by_class(unreal.StaticMeshComponent):
            print("   comp:", c.get_name(), "worldScale:", c.get_world_scale())
    for cmd in ["t.IdleWhenNotForeground 0", "ShowFlag.Selection 0"]:
        unreal.SystemLibrary.execute_console_command(gw, cmd)
    # 环绕三机位：调整控制器朝向让第三人称弹簧臂绕角色旋转
    shots = [("AFTER_back", unreal.Rotator(0, 0, 0)),
             ("AFTER_front", unreal.Rotator(-10, 180, 0)),
             ("AFTER_side", unreal.Rotator(-10, 90, 0))]
    for name, rot in shots:
        if pc:
            pc.set_control_rotation(rot)
        time.sleep(1.0)
        p = f"{out}/{name}.png"
        if os.path.exists(p):
            os.remove(p)
        unreal.SystemLibrary.execute_console_command(gw, f'HighResShot 1600x900 filename="{p}"')
        time.sleep(2.5)
        print("shot", name, "exists:", os.path.exists(p))
else:
    print("NOT in PIE - nothing to shoot")
print("=== DONE ===")
