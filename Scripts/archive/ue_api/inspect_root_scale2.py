import unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "BP_DariusCharacter" in a.get_name():
        mesh = a.get_component_by_class(unreal.SkeletalMeshComponent)
        for i in range(min(5, mesh.get_num_bones())):
            bname = mesh.get_bone_name(i)
            print(f"Bone {i} ({bname}): ParentSpace Scale = {mesh.get_bone_transform_by_name(bname, unreal.RelativeTransformSpace.RTS_PARENT_BONE_SPACE).scale3d}")
            print(f"Bone {i} ({bname}): ComponentSpace Scale = {mesh.get_bone_transform_by_name(bname, unreal.RelativeTransformSpace.RTS_COMPONENT).scale3d}")
