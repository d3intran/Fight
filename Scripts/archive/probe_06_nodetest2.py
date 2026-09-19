import unreal
abp = unreal.load_asset("/Game/Character/Darius/Blueprints/ABP_NodeTest")
print("abp:", abp)
graphs = unreal.AnimationLibrary.get_animation_graphs(abp)
tg = graphs[0]
print("graph:", tg.get_name())

# 不设任何属性，直接 new_object 看是否挂进图
try:
    n = unreal.new_object(unreal.AnimGraphNode_SequencePlayer, tg)
    print("created:", n.get_name(), n.get_class().get_name())
except Exception as e:
    print("create node err:", e)

after = unreal.AnimationLibrary.get_nodes_of_class(abp, unreal.AnimGraphNode_SequencePlayer)
print("get_nodes_of_class(SequencePlayer):", after)
after2 = unreal.AnimationLibrary.get_nodes_of_class(abp, unreal.AnimGraphNode_Root)
print("get_nodes_of_class(Root):", after2)
print("RESULT:", "AUTO-REGISTER WORKS" if len(after) > 0 else "AUTO-REGISTER FAILED")

# 也试试 add_node 的替代：直接操作 nodes 数组
try:
    nodes = tg.get_editor_property("nodes")
    print("graph nodes (read):", nodes)
except Exception as e:
    print("read nodes err:", e)
print("=== DONE ===")
