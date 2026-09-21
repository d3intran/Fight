import unreal

eal = unreal.EditorAssetLibrary

BP_PATH = "/Game/Character/Darius/Blueprints/BP_DariusCharacter"
bp = eal.load_asset(BP_PATH)

# Find CharacterMovementComponent in SimpleConstructionScript or CDO
cls = bp.generated_class()
cdo = unreal.get_default_object(cls)
cmc = cdo.get_components_by_class(unreal.CharacterMovementComponent)[0]

old_v = cmc.get_editor_property("jump_z_velocity")
old_g = cmc.get_editor_property("gravity_scale")
old_ac = cmc.get_editor_property("air_control")

unreal.log(f"Old CMC values: jump_z_velocity={old_v}, gravity_scale={old_g}, air_control={old_ac}")

NEW_V = 380.0
NEW_G = 1.8
NEW_AC = 0.15

cmc.set_editor_property("jump_z_velocity", NEW_V)
cmc.set_editor_property("gravity_scale", NEW_G)
cmc.set_editor_property("air_control", NEW_AC)

unreal.BlueprintEditorLibrary.compile_blueprint(bp)
saved = eal.save_asset(BP_PATH)
unreal.log(f"Compiled and saved BP_DariusCharacter: {saved}")

# Verify CDO
cdo_verify = unreal.get_default_object(bp.generated_class())
cmc_v = cdo_verify.get_components_by_class(unreal.CharacterMovementComponent)[0]
unreal.log(f"Verified CDO values: jump_z_velocity={cmc_v.get_editor_property('jump_z_velocity')}, gravity_scale={cmc_v.get_editor_property('gravity_scale')}, air_control={cmc_v.get_editor_property('air_control')}")
