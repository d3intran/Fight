import unreal
print("BlueprintType:", [m for m in dir(unreal.BlueprintType) if not m.startswith("_")])
FACT = unreal.AnimBlueprintFactory()
FACT.set_editor_property("target_skeleton", unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton"))
try:
    FACT.set_editor_property("parent_class", unreal.AnimInstance)
except Exception as e:
    print("parent err:", e)
at = unreal.AssetToolsHelpers.get_asset_tools()
if unreal.EditorAssetLibrary.does_asset_exist("/Game/Character/Darius/Blueprints/ABP_NodeTest"):
    unreal.EditorAssetLibrary.delete_asset("/Game/Character/Darius/Blueprints/ABP_NodeTest")
abp = None
try:
    abp = at.create_asset("ABP_NodeTest", "/Game/Character/Darius/Blueprints", unreal.AnimBlueprint, FACT)
except Exception as e:
    print("create err:", e)
print("abp:", abp)
if abp:
    print("  target_skeleton:", abp.get_editor_property("target_skeleton"))
    graphs = unreal.AnimationLibrary.get_animation_graphs(abp)
    print("  anim graphs:", [(g.get_name(), g.get_class().get_name()) for g in graphs])
    tg = graphs[0] if graphs else None
    if tg:
        try:
            n = unreal.new_object(unreal.AnimGraphNode_SequencePlayer, tg)
            n.set_editor_property("node_pos_x", 300)
            n.set_editor_property("node_pos_y", 100)
            print("  created:", n.get_name())
            after = unreal.AnimationLibrary.get_nodes_of_class(abp, unreal.AnimGraphNode_SequencePlayer)
            print("  get_nodes_of_class:", after)
            print("  RESULT:", "WORKS" if len(after) > 0 else "FAILED")
        except Exception as e:
            print("  node err:", e)
print("=== DONE ===")
