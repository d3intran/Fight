import unreal

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
unreal.log("PIE before = %s" % les.is_in_play_in_editor())
if les.is_in_play_in_editor():
    les.editor_request_end_play()
    unreal.log("已请求结束 PIE（单次调用，不循环等待）")
else:
    unreal.log("本来就不在 PIE")
