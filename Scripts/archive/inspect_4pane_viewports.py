import unreal
import inspect

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
unreal.log(f"Help on set_level_viewport_camera_info: {help(les.set_level_viewport_camera_info)}")

for k in les.get_viewport_config_keys():
    try:
        info = les.get_level_viewport_camera_info(k)
        unreal.log(f"Viewport [{k}]: camera={info}")
    except Exception as e:
        unreal.log(f"Viewport [{k}] error: {e}")
