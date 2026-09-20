import unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if les.is_in_play_in_editor():
    les.editor_request_end_play()
    unreal.log("end play requested (again)")
else:
    unreal.log("not in PIE")
