import unreal

bp_class = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
unreal.log(f"bp_class: {bp_class}")

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actor = actor_sub.spawn_actor_from_class(bp_class, unreal.Vector(0, 0, 150))
unreal.log(f"spawned: {actor}")
