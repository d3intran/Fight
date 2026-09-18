import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
loc, rot = ues.get_level_viewport_camera_info()
unreal.log(f"Current Viewport Camera: Loc={loc}, Rot={rot}")

# Check all cameras or viewports
el = unreal.EditorLevelLibrary
el_loc, el_rot = el.get_level_viewport_camera_info()
unreal.log(f"EditorLevelLibrary Viewport Camera: Loc={el_loc}, Rot={el_rot}")
