import unreal

subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary

bp_path = "/Game/Character/Darius/Blueprints/BP_DariusCharacter"
bp = unreal.load_object(None, bp_path)
handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)

unreal.log(f"Subobject handles count: {len(handles)}")
for h in handles:
    data = subsystem.k2_find_subobject_data_from_handle(h)
    d_name = lib.get_display_name(data)
    obj = lib.get_object_for_blueprint(data, bp)
    unreal.log(f"Handle: Name='{d_name}', Obj={obj}")
    if obj and isinstance(obj, unreal.SceneComponent):
        parent = obj.get_attach_parent()
        unreal.log(f"  AttachParent: {parent}, Socket: {obj.get_attach_socket_name()}")
        if isinstance(obj, unreal.StaticMeshComponent):
            unreal.log(f"  StaticMesh: {obj.get_editor_property('static_mesh')}")
