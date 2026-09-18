import unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
print("in PIE before:", les.is_in_play_in_editor())
les.editor_request_end_play()
print("end play requested")
