import unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "BP_DariusCharacter" in a.get_name():
        for c in a.get_components_by_class(unreal.ActorComponent):
            print(f"Actor Component: {c.get_name()} ({c.get_class().get_name()})")
