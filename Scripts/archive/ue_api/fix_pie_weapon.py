import unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "BP_DariusCharacter" in a.get_name():
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if "Axe" in c.get_name() or "Weapon" in c.get_name():
                c.set_world_scale3d(unreal.Vector(1.0, 1.0, 1.0))
                print("Weapon WorldScale:", c.get_world_scale())
                print("Weapon RelScale:", c.get_editor_property("relative_scale3d"))
                print("Weapon WorldLoc:", c.get_world_location())
