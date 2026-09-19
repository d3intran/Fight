import unreal

print("=== 现有 AnimBlueprint ===")
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for a in ar.get_assets_by_path("/Game", recursive=True):
    cn = str(a.asset_class_path.asset_name)
    if "Anim" in cn or "BlendSpace" in cn:
        print("  ", a.package_name, "|", cn)

print()
print("=== BP_DariusCharacter 的 Mesh AnimClass ===")
bp = unreal.load_asset("/Game/Character/Darius/Blueprints/BP_DariusCharacter")
if bp:
    cdo = unreal.get_default_object(bp.generated_class())
    mesh = cdo.get_component_by_class(unreal.SkeletalMeshComponent)
    print("  anim_class:", mesh.get_editor_property("anim_class"))
    print("  animation_mode:", mesh.get_editor_property("animation_mode"))
    print("  anim_to_play:", mesh.get_editor_property("anim_to_play"))

print()
print("=== AnimGraph Python API 探测 ===")
names = ["AnimGraphNode_StateMachine", "AnimGraphNode_StateMachineBase", "AnimGraphNode_SequencePlayer",
         "AnimGraphNode_Root", "AnimGraphNode_BlendSpacePlayer", "AnimStateNode", "AnimStateTransitionNode",
         "AnimBlueprintFactory", "BlueprintEditorLibrary", "AnimGraphNode_LinkedAnimLayer",
         "AnimationGraph", "AnimBlueprint", "BlendSpace", "BlendSpaceFactory1D", "AnimationLibrary",
         "AnimGraphNode_TwoBoneIK", "AnimGraphNode_ModifyBone"]
for n in names:
    print(f"  unreal.{n}:", hasattr(unreal, n))

print()
print("BlueprintEditorLibrary 方法:")
try:
    print(" ", [m for m in dir(unreal.BlueprintEditorLibrary) if not m.startswith("_")])
except Exception as e:
    print("  err", e)
print()
print("AnimGraphNode_StateMachine 方法:")
try:
    print(" ", [m for m in dir(unreal.AnimGraphNode_StateMachine) if not m.startswith("_")])
except Exception as e:
    print("  err", e)
print()
print("EdGraph 方法:")
try:
    print(" ", [m for m in dir(unreal.EdGraph) if not m.startswith("_")])
except Exception as e:
    print("  err", e)
print("=== DONE ===")
