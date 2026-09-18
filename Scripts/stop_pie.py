import unreal
import time

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

while les.is_in_play_in_editor():
    unreal.log("Ending PIE...")
    les.editor_request_end_play()
    time.sleep(0.5)

unreal.log(f"PIE ended cleanly! is_in_play_in_editor = {les.is_in_play_in_editor()}")
