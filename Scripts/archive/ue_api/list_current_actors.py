import unreal

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in actor_sub.get_all_level_actors():
    unreal.log(f"Actor: {a.get_name()} ({a.get_class().get_name()}) at {a.get_actor_location()}")
