import unreal

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in actor_sub.get_all_level_actors():
    if isinstance(a, unreal.StaticMeshActor):
        sm = a.static_mesh_component.get_editor_property('static_mesh')
        unreal.log(f"StaticMeshActor: {a.get_name()}, Loc: {a.get_actor_location()}, Mesh: {sm.get_name() if sm else 'None'}")
