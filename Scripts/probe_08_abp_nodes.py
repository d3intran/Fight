import unreal

abp = unreal.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed")
print("ABP_Unarmed:", abp)
print("target_skeleton:", abp.get_editor_property("target_skeleton") if abp else None)
print()
print("=== 该 ABP 中的各类节点 ===")
for cls_name in ["AnimGraphNode_SequencePlayer", "AnimGraphNode_BlendSpacePlayer", "AnimGraphNode_StateMachine",
                 "AnimGraphNode_Root", "AnimGraphNode_StateResult", "AnimGraphNode_TransitionResult",
                 "AnimGraphNode_LayeredBoneBlend", "AnimGraphNode_TwoBoneIK", "AnimGraphNode_BlendListByBool",
                 "AnimGraphNode_UseCachedPose", "AnimGraphNode_SaveCachedPose", "AnimGraphNode_SequenceEvaluator"]:
    cls = getattr(unreal, cls_name, None)
    if cls is None:
        continue
    try:
        nodes = unreal.AnimationLibrary.get_nodes_of_class(abp, cls)
    except Exception as e:
        print(f"  {cls_name}: err {e}")
        continue
    if nodes:
        print(f"  {cls_name}: {len(nodes)}")
        for n in nodes:
            info = ""
            try:
                info = " seq=" + str(n.get_editor_property("sequence"))
            except Exception:
                pass
            try:
                info += " bs=" + str(n.get_editor_property("blend_space"))
            except Exception:
                pass
            print("     ", n.get_name(), info)
print("=== DONE ===")
