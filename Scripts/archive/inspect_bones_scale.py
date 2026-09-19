import unreal
sk = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
skeleton = sk.get_editor_property("skeleton")
print("Skeleton:", skeleton.get_name())
# Check reference pose bone scales
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "BP_DariusCharacter" in a.get_name():
        mesh = a.get_component_by_class(unreal.SkeletalMeshComponent)
        for bone in ["root", "pelvis", "spine_01", "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r"]:
            b_name = unreal.Name(bone)
            trans = mesh.get_bone_transform_by_name(b_name, unreal.RelativeTransformSpace.RTS_PARENT_BONE_SPACE)
            print(f"Bone {bone} in ParentSpace: Scale={trans.scale3d}")
