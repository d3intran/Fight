import unreal

subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary

bp_path = "/Game/Character/Darius/Blueprints/BP_DariusCharacter"
bp = unreal.load_object(None, bp_path)
handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)

for h in handles:
    data = subsystem.k2_find_subobject_data_from_handle(h)
    d_name = lib.get_display_name(data)
    if "WeaponAxe" in str(d_name):
        obj = lib.get_object_for_blueprint(data, bp)
        unreal.log(f"WeaponAxe Template: {obj}")
        unreal.log(f"  RelativeLoc: {obj.get_editor_property('relative_location')}")
        unreal.log(f"  RelativeRot: {obj.get_editor_property('relative_rotation')}")
        unreal.log(f"  RelativeScale: {obj.get_editor_property('relative_scale3d')}")
        unreal.log(f"  Visible: {obj.get_editor_property('visible')}")
        unreal.log(f"  HiddenInGame: {obj.get_editor_property('hidden_in_game')}")
        unreal.log(f"  StaticMesh: {obj.get_editor_property('static_mesh')}")
        unreal.log(f"  Materials: {[obj.get_material(i) for i in range(1)]}")
