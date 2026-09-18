import unreal
import os

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

les.editor_invalidate_viewports()

screenshot_path = "E:/UE/Fight/Saved/Screenshots/Darius_Hand_Piloted.png"
if os.path.exists(screenshot_path):
    try:
        os.remove(screenshot_path)
    except:
        pass

unreal.SystemLibrary.execute_console_command(None, f"HighResShot 1920x1080 filename=\"{screenshot_path}\"")
unreal.log(f"Triggered HighResShot from piloted camera -> {screenshot_path}")
