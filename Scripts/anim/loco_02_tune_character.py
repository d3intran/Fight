import unreal

eal = unreal.EditorAssetLibrary
BP_PATH = "/Game/Character/Darius/Blueprints/BP_DariusCharacter"

bp = eal.load_asset(BP_PATH)
subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)

for h in handles:
    data = subsystem.k2_find_subobject_data_from_handle(h)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
    if isinstance(obj, unreal.SpringArmComponent):
        obj.set_editor_property("target_arm_length", 380.0)
        obj.set_editor_property("target_offset", unreal.Vector(0.0, 0.0, 50.0))
        obj.set_editor_property("socket_offset", unreal.Vector(0.0, 45.0, 20.0))
        obj.set_editor_property("enable_camera_lag", True)
        obj.set_editor_property("camera_lag_speed", 9.0)
        obj.set_editor_property("enable_camera_rotation_lag", True)
        obj.set_editor_property("camera_rotation_lag_speed", 12.0)
        obj.set_editor_property("use_pawn_control_rotation", True)

unreal.BlueprintEditorLibrary.compile_blueprint(bp)
eal.save_asset(BP_PATH, only_if_is_dirty=False)
unreal.log("Updated SpringArm framing on BP_DariusCharacter.")

# Also update PlayerStart rotation in level
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.PlayerStart):
        a.set_actor_rotation(unreal.Rotator(pitch=-12.0, yaw=0.0, roll=0.0), False)
        unreal.log(f"Set PlayerStart rotation: {a.get_actor_rotation()}")
unreal.EditorLevelLibrary.save_current_level()
unreal.log("Saved current level.")
