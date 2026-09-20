import unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "BP_DariusCharacter" in a.get_name():
        mesh = a.get_component_by_class(unreal.SkeletalMeshComponent)
        sk = mesh.get_editor_property("skeletal_mesh_asset")
        # print bone names and transforms
        for i in range(min(5, sk.get_num_bones())):
            bname = sk.get_bone_name(i)
            print(f"Bone {i} ({bname}): ParentSpace Scale = {mesh.get_bone_transform_by_name(bname, unreal.RelativeTransformSpace.RTS_PARENT_BONE_SPACE).scale3d}")
            print(f"Bone {i} ({bname}): ComponentSpace Scale = {mesh.get_bone_transform_by_name(bname, unreal.RelativeTransformSpace.RTS_COMPONENT).scale3d}")
