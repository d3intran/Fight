import unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if les.is_in_play_in_editor():
    unreal.log("already in PIE")
else:
    les.editor_request_begin_play()
    unreal.log("begin play requested")
