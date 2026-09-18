import unreal

FACT = unreal.AnimBlueprintFactory()
FACT.set_editor_property("target_skeleton", unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton"))
FACT.set_editor_property("parent_class", unreal.AnimInstance)
FACT.set_editor_property("blueprint_type", unreal.BlueprintType.NORMAL)
at = unreal.AssetToolsHelpers.get_asset_tools()
abp = None
try:
    abp = at.create_asset("ABP_NodeTest", "/Game/Character/Darius/Blueprints", unreal.AnimBlueprint, FACT)
except Exception as e:
    print("create err:", e)
print("abp:", abp)

graphs = unreal.AnimationLibrary.get_animation_graphs(abp) if abp else []
print("anim graphs:", graphs)
for g in graphs:
    print("  graph:", g.get_name(), g.get_class().get_name())
    print("  nodes before:", [n.get_name() for n in (g.get_editor_property("nodes") if hasattr(g, "get_editor_property") else [])] if False else "n/a")

# 尝试用 new_object 造节点，看是否自动挂进图
target_graph = None
for g in graphs:
    if "AnimGraph" in g.get_name():
        target_graph = g
        break
if target_graph is None and graphs:
    target_graph = graphs[0]
print("target graph:", target_graph)

if target_graph:
    try:
        n = unreal.new_object(unreal.AnimGraphNode_SequencePlayer, target_graph)
        n.set_editor_property("node_pos_x", 300)
        n.set_editor_property("node_pos_y", 100)
        print("created node:", n.get_name())
        after = unreal.AnimationLibrary.get_nodes_of_class(abp, unreal.AnimGraphNode_SequencePlayer)
        print("get_nodes_of_class ->", after)
        print("RESULT:", "AUTO-REGISTER WORKS" if len(after) > 0 else "AUTO-REGISTER FAILED")
    except Exception as e:
        print("node err:", e)
print("=== DONE ===")
