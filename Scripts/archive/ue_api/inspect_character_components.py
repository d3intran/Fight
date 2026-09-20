import unreal

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actor = [a for a in actor_sub.get_all_level_actors() if "BP_DariusCharacter" in a.get_name()][0]

for c in actor.get_components_by_class(unreal.SceneComponent):
    unreal.log(f"Comp: {c.get_name()} ({c.get_class().get_name()})")
    unreal.log(f"  Parent: {c.get_attach_parent()}")
    unreal.log(f"  Socket: {c.get_attach_socket_name()}")
    unreal.log(f"  Visible: {c.is_visible()}")
    unreal.log(f"  HiddenInGame: {c.get_editor_property('hidden_in_game')}")
    unreal.log(f"  RelativeLoc: {c.get_editor_property('relative_location')}")
    unreal.log(f"  RelativeRot: {c.get_editor_property('relative_rotation')}")
    unreal.log(f"  RelativeScale: {c.get_editor_property('relative_scale3d')}")
    unreal.log(f"  WorldLoc: {c.get_world_location()}")
    unreal.log(f"  WorldRot: {c.get_world_rotation()}")
    if isinstance(c, unreal.StaticMeshComponent):
        sm = c.get_editor_property('static_mesh')
        unreal.log(f"  StaticMesh: {sm}")
        if sm:
            unreal.log(f"  SM Material 0: {sm.get_material(0)}")
            unreal.log(f"  Comp Material 0: {c.get_material(0)}")
