import unreal
names = ["AnimGraphNode_StateMachine", "AnimGraphNode_StateMachineBase", "AnimGraphNode_SequencePlayer",
         "AnimGraphNode_Root", "AnimGraphNode_BlendSpacePlayer", "AnimStateNode", "AnimStateTransitionNode",
         "AnimBlueprintFactory", "BlueprintEditorLibrary", "AnimationGraph", "AnimBlueprint",
         "BlendSpace", "BlendSpaceFactory1D", "AnimationLibrary", "AnimGraphNode_TwoBoneIK",
         "AnimGraphNode_ModifyBone", "AnimGraphNode_SkeletalControlBase", "AnimGraphNode_Base",
         "AnimGraphNode_StateMachineEntry", "AnimGraphNode_StateResult", "AnimGraphNode_BlendListByBool"]
for n in names:
    print(f"unreal.{n}:", hasattr(unreal, n))
print()
print("BlueprintEditorLibrary:", [m for m in dir(unreal.BlueprintEditorLibrary) if not m.startswith("_")])
print()
print("EdGraph:", [m for m in dir(unreal.EdGraph) if not m.startswith("_")])
print()
print("AnimGraphNode_StateMachine:", [m for m in dir(unreal.AnimGraphNode_StateMachine) if not m.startswith("_")])
print()
print("AnimationLibrary:", [m for m in dir(unreal.AnimationLibrary) if not m.startswith("_")])
print()
print("AnimBlueprint:", [m for m in dir(unreal.AnimBlueprint) if not m.startswith("_")][:40])
print("=== DONE ===")
