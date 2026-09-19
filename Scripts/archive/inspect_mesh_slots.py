import unreal

eal = unreal.EditorAssetLibrary

sk_mesh = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
mats = sk_mesh.get_editor_property('materials')
unreal.log(f"Total material slots: {len(mats)}")
for i, m in enumerate(mats):
    slot_name = m.get_editor_property('material_slot_name')
    mat_int = m.get_editor_property('material_interface')
    unreal.log(f"Slot {i}: {slot_name} -> {mat_int.get_name() if mat_int else None}")
