import unreal
import time

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

unreal.log("Starting editor_play_simulate...")
les.editor_play_simulate()
time.sleep(1.0)

screenshot_path = "E:/UE/Fight/Saved/Screenshots/Darius_Simulate_Shot.png"
unreal.SystemLibrary.execute_console_command(None, f"HighResShot 1920x1080 filename=\"{screenshot_path}\"")
unreal.log("HighResShot called during simulate")
time.sleep(1.0)

les.editor_request_end_play()
unreal.log("editor_request_end_play called")
