import unreal

# Try setting throttling console variables
commands = [
    "t.IdleWhenNotForeground 0",
    "r.Editor.Viewport.Throttle 0",
    "Editor.bThrottleWhenHidden 0"
]

for cmd in commands:
    res = unreal.SystemLibrary.execute_console_command(None, cmd)
    unreal.log(f"Executed: {cmd}")

# Force viewport refresh
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for k in les.get_viewport_config_keys():
    try:
        les.editor_set_viewport_realtime(True, k)
    except:
        pass
les.editor_invalidate_viewports()
unreal.log("Viewports set to Realtime=True and invalidated!")
