import unreal

mat = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/Materials/M_Invisible")
node = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, unreal.MaterialProperty.MP_OPACITY_MASK)
print("OpacityMask const node:", node)
for f in ["r", "g", "b", "a", "desc"]:
    try:
        print("  ", f, "=", node.get_editor_property(f))
    except Exception as e:
        print("  ", f, "<err>")

# 检查编辑器中 Darius 的武器世界缩放
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in actor_sub.get_all_level_actors():
    if "BP_DariusCharacter" in a.get_name():
        print("Actor:", a.get_name())
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            print("   ", c.get_name(), "worldScale:", c.get_world_scale())
        mesh = a.get_component_by_class(unreal.SkeletalMeshComponent)
        st = mesh.get_socket_transform(unreal.Name("hand_rSocket"), unreal.RelativeTransformSpace.RTS_WORLD)
        print("    hand_rSocket world scale:", st.scale3d, "loc:", st.translation)
print("=== DONE ===")
