import unreal

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

# Let's inspect BEFORE setting
unreal.log(f"UES Camera Before: {ues.get_level_viewport_camera_info()}")
for k in les.get_viewport_config_keys():
    unreal.log(f"LES Viewport [{k}] Before: {les.get_level_viewport_camera_info(k)}")

# Set to a radical position: (1000, 2000, 3000)
test_loc = unreal.Vector(1000.0, 2000.0, 3000.0)
test_rot = unreal.Rotator(pitch=0.0, yaw=45.0, roll=0.0)

for k in les.get_viewport_config_keys():
    les.set_level_viewport_camera_info(test_loc, test_rot, k)

# Check AFTER setting
unreal.log(f"UES Camera After: {ues.get_level_viewport_camera_info()}")
for k in les.get_viewport_config_keys():
    unreal.log(f"LES Viewport [{k}] After: {les.get_level_viewport_camera_info(k)}")
