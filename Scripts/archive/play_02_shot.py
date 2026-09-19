import unreal, os, time
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
print("game world:", gw.get_name() if gw else None)
if gw:
    for cmd in ["t.IdleWhenNotForeground 0", "ShowFlag.Selection 0"]:
        unreal.SystemLibrary.execute_console_command(gw, cmd)
    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    pawn = pc.get_pawn() if pc else None
    print("pawn:", pawn.get_name() if pawn else None)
    out = r"E:/UE/Fight/Saved/Shots"
    os.makedirs(out, exist_ok=True)
    p = out + "/AFTER_pie.png"
    if os.path.exists(p): os.remove(p)
    unreal.SystemLibrary.execute_console_command(gw, f'HighResShot 1600x900 filename="{p}"')
    time.sleep(3)
    print("exists:", os.path.exists(p))
