import unreal

eal = unreal.EditorAssetLibrary

mi_axe = eal.load_asset("/Game/Character/Darius/Materials/MI_Darius_Axe")
unreal.log(f"MI_Darius_Axe: {mi_axe}")
if mi_axe:
    unreal.log(f"  Parent: {mi_axe.get_editor_property('parent')}")
    # Texture parameters
    for p in mi_axe.get_editor_property('texture_parameter_values'):
        unreal.log(f"  Tex Param: {p.get_editor_property('parameter_info').name} = {p.get_editor_property('parameter_value')}")
    # Scalar parameters
    for p in mi_axe.get_editor_property('scalar_parameter_values'):
        unreal.log(f"  Scalar Param: {p.get_editor_property('parameter_info').name} = {p.get_editor_property('parameter_value')}")

# Also check SK_Darius_GodKing materials
sk = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
for idx, mat in enumerate(sk.get_editor_property('materials')):
    unreal.log(f"SK Slot {idx} ({mat.slot_name}): {mat.material_interface.get_name() if mat.material_interface else 'None'}")
