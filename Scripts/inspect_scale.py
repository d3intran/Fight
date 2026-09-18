import unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "BP_DariusCharacter" in a.get_name():
        mesh = a.get_component_by_class(unreal.SkeletalMeshComponent)
        print("CharacterMesh0 RelScale:", mesh.get_editor_property("relative_scale3d"))
        print("CharacterMesh0 WorldScale:", mesh.get_world_scale())
        print("hand_r socket WorldScale:", mesh.get_socket_transform(unreal.Name("hand_rSocket"), unreal.RelativeTransformSpace.RTS_WORLD).scale3d)
        print("hand_r socket ActorScale:", mesh.get_socket_transform(unreal.Name("hand_rSocket"), unreal.RelativeTransformSpace.RTS_ACTOR).scale3d)
        print("hand_r socket ComponentScale:", mesh.get_socket_transform(unreal.Name("hand_rSocket"), unreal.RelativeTransformSpace.RTS_COMPONENT).scale3d)
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if "Axe" in c.get_name() or "Weapon" in c.get_name():
                print("Weapon Component WorldScale:", c.get_world_scale())
                print("Weapon Component RelScale:", c.get_editor_property("relative_scale3d"))
