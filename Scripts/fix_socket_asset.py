import unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "BP_DariusCharacter" in a.get_name():
        mesh = a.get_component_by_class(unreal.SkeletalMeshComponent)
        sk = mesh.get_editor_property("skeletal_mesh_asset")
        sock = sk.find_socket(unreal.Name("hand_rSocket"))
        if sock:
            sock.set_editor_property("relative_scale", unreal.Vector(0.01, 0.01, 0.01))
            print("Updated hand_rSocket relative_scale to:", sock.get_editor_property("relative_scale"))
        
        # also update weapon in hand
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if "Axe" in c.get_name() or "Weapon" in c.get_name():
                c.set_editor_property("absolute_scale", False)
                c.set_world_scale3d(unreal.Vector(1.0, 1.0, 1.0))
                print("Live weapon in PIE fixed:")
                print("  WorldScale:", c.get_world_scale())
                print("  RelScale:", c.get_editor_property("relative_scale3d"))
