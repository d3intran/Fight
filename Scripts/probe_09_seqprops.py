import unreal
abp = unreal.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed")
nodes = unreal.AnimationLibrary.get_nodes_of_class(abp, unreal.AnimGraphNode_SequencePlayer)
print("SequencePlayer 节点数:", len(nodes))
for n in nodes:
    print("---", n.get_name(), "| full:", n.get_path_name())
    try:
        inner = n.get_editor_property("node")
        print("   inner:", inner)
        for p in ["sequence", "play_rate", "start_position", "loop_animation", "play_rate_scale"]:
            try:
                print(f"     {p}:", inner.get_editor_property(p))
            except Exception as e:
                print(f"     {p}: <{e}>")
    except Exception as e:
        print("   inner err:", e)
    try:
        print("   node_pos:", n.get_node_pos())
    except Exception as e:
        print("   pos err:", e)

print()
print("=== BlendSpacePlayer ===")
for n in unreal.AnimationLibrary.get_nodes_of_class(abp, unreal.AnimGraphNode_BlendSpacePlayer):
    print("---", n.get_name())
    try:
        inner = n.get_editor_property("node")
        print("   blend_space:", inner.get_editor_property("blend_space"))
    except Exception as e:
        print("   err:", e)
print("=== DONE ===")
