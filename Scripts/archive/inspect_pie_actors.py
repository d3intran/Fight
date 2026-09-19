import unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
print("Game World:", gw)
if gw:
    actors = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor)
    for a in actors:
        name = a.get_name()
        if any(k in name for k in ["Darius", "Axe", "Weapon", "StaticMesh"]):
            print(f"Actor: {name} ({a.get_class().get_name()})")
            print(f"  Location: {a.get_actor_location()}")
            print(f"  Scale: {a.get_actor_scale3d()}")
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                sm = c.get_editor_property("static_mesh")
                print(f"    SM: {sm.get_name() if sm else None}, RelScale: {c.get_editor_property('relative_scale3d')}, WorldScale: {c.get_world_scale()}")
