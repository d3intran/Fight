import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()

print("=== PIE 世界 Actor 概览 ===")
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    n = a.get_name()
    if any(k in n for k in ["BP_DariusCharacter", "PlayerStart", "StaticMeshActor", "Landscape", "Floor", "Ground", "Training", "DirectionalLight", "SkyLight", "Fog", "Sky"]):
        print(f"  {n} | {a.get_class().get_name()} | {a.get_actor_location()}")

ps = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.PlayerStart)
print("PlayerStarts:", [(p.get_name(), p.get_actor_location()) for p in ps])

pawn = None
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "BP_DariusCharacter" in a.get_name():
        pawn = a
if pawn and ps:
    loc = ps[0].get_actor_location()
    pawn.set_actor_location(unreal.Vector(loc.x, loc.y, loc.z + 20), False, False)
    print("teleported pawn to:", pawn.get_actor_location())
print("=== DONE ===")
