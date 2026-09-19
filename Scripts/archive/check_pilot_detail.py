import unreal

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
pilot_actor = les.get_pilot_level_actor()
unreal.log(f"Pilot Level Actor: {pilot_actor}")
active_key = les.get_active_viewport_config_key()
unreal.log(f"Active Viewport Config Key: {active_key}")
all_keys = les.get_viewport_config_keys()
unreal.log(f"All Viewport Config Keys: {all_keys}")
