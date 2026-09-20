import unreal

bp = unreal.load_object(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter")
unreal.log(f"BP object: {bp}")

bp_class = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
unreal.log(f"BP class: {bp_class}")

cdo = unreal.get_default_object(bp_class)
unreal.log(f"CDO: {cdo}")
for c in cdo.get_components_by_class(unreal.SceneComponent):
    unreal.log(f"  CDO Comp: {c.get_name()} ({c.get_class().get_name()}), Parent: {c.get_attach_parent()}, Socket: {c.get_attach_socket_name()}")
    if isinstance(c, unreal.StaticMeshComponent):
        unreal.log(f"    StaticMesh: {c.get_editor_property('static_mesh')}")
