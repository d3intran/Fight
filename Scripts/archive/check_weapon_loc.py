import unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "BP_DariusCharacter" in a.get_name():
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if "Axe" in c.get_name() or "Weapon" in c.get_name():
                print("Axe WorldLocation:", c.get_world_location())
                print("Axe WorldScale:", c.get_world_scale())
                print("Axe StaticMesh:", c.get_editor_property("static_mesh").get_name() if c.get_editor_property("static_mesh") else None)
