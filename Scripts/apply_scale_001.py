import unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "BP_DariusCharacter" in a.get_name():
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if "Axe" in c.get_name() or "Weapon" in c.get_name():
                c.set_editor_property("relative_scale3d", unreal.Vector(0.01, 0.01, 0.01))
                print("Weapon in hand fixed:")
                print("  RelativeScale3D:", c.get_editor_property("relative_scale3d"))
                print("  WorldScale:", c.get_world_scale())
                print("  WorldLocation:", c.get_world_location())
