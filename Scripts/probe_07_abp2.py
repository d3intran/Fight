import unreal
print("IKRetargetBatchOperation:", [m for m in dir(unreal.IKRetargetBatchOperation) if not m.startswith("_")])
print()
print("IKRetargeterController:", [m for m in dir(unreal.IKRetargeterController) if not m.startswith("_")])
print()
print("IKRigController:", [m for m in dir(unreal.IKRigController) if not m.startswith("_")])
print()
for n in ["K2Node", "K2Node_CallFunction", "EdGraphNode", "EdGraphSchema_K2", "AnimGraphNode_Base",
          "AnimGraphNode_SequenceEvaluator", "AnimGraphNode_BlendListByBool", "AnimGraphNode_ApplyAdditive",
          "AnimGraphNode_LayeredBoneBlend", "AnimGraphNode_LinkedInputPose", "AnimStateAliasNode",
          "AnimGraphNode_TransitionResult", "AnimGraphNode_StateResult", "AnimGraphNode_UseCachedPose"]:
    print(f"unreal.{n}:", hasattr(unreal, n))
print()
print("AnimGraphNode_Base:", [m for m in dir(unreal.AnimGraphNode_Base) if not m.startswith("_")])
print()
print("AnimGraphNode_SequencePlayer 属性:")
try:
    d = unreal.AnimGraphNode_SequencePlayer.get_default_object()
    print("  node:", d)
except Exception as e:
    print("  err", e)
print()
print("AnimBlueprintFactory:", [m for m in dir(unreal.AnimBlueprintFactory) if not m.startswith("_")])
print("=== DONE ===")
