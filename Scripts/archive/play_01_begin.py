import unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
print("in pie:", les.is_in_play_in_editor())
les.editor_request_begin_play()
print("begin play requested")
