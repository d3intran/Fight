import unreal

def bounds_of(sk, label):
    print(f"--- {label}: {sk.get_path_name()}")
    try:
        b = sk.get_bounds()
        print("   get_bounds():", b)
    except Exception as e:
        print("   bounds err:", e)
    try:
        print("   extended_bounds:", sk.get_editor_property("extended_bounds"))
    except Exception as e:
        print("   ext err:", e)
    try:
        skb = sk.get_editor_property("skinned_asset_bounds")
        print("   skinned_asset_bounds:", skb)
    except Exception as e:
        print("   skb err:", e)

orig = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
new = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_NoAxe")
bounds_of(orig, "原始(含斧头)")
bounds_of(new, "清理后")

print()
print("=== 原始网格材质/插槽 ===")
for i, m in enumerate(orig.get_editor_property("materials")):
    mi = m.get_editor_property("material_interface")
    print(f"   Slot[{i}] {m.get_editor_property('material_slot_name')} -> {mi.get_path_name() if mi else None}")
print("=== 清理后网格 ===")
for i, m in enumerate(new.get_editor_property("materials")):
    mi = m.get_editor_property("material_interface")
    print(f"   Slot[{i}] {m.get_editor_property('material_slot_name')} -> {mi.get_path_name() if mi else None}")
print("=== DONE ===")
