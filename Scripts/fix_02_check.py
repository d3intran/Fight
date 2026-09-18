import unreal

sk2 = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
s2 = sk2.find_socket(unreal.Name("hand_rSocket"))
print("SK hand_rSocket relScale now:", s2.get_editor_property("relative_scale"))

mat = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/Materials/M_Invisible")
print()
print("M_Invisible blend:", mat.get_editor_property("blend_mode"))
for p in ["opacity_mask", "opacity"]:
    try:
        v = mat.get_editor_property(p)
        print(f"{p}:", v)
        for f in ["use_constant", "constant", "expression"]:
            try:
                print(f"   {f}:", v.get_editor_property(f))
            except Exception as e:
                print(f"   {f}: <{e}>")
    except Exception as e:
        print(f"{p} err:", e)
try:
    print("MaterialEditingLibrary available:", unreal.MaterialEditingLibrary)
    node = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_OPACITY_MASK)
    print("OpacityMask input node:", node)
except Exception as e:
    print("MEL err:", e)
print("=== DONE ===")
