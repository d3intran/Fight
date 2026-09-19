import unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
dest = r"C:\Users\29226\.gemini\antigravity\brain\d4c072f2-5030-4073-9e3a-1bdf8c0566d0\darius_axe_scale_fixed.png"
unreal.SystemLibrary.execute_console_command(gw, f"HighResShot 1920x1080 filename=\"{dest}\"")
print("HighResShot requested to:", dest)
