import unreal

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Clean previous actors
for a in actor_sub.get_all_level_actors():
    if "BP_DariusCharacter" in a.get_name():
        actor_sub.destroy_actor(a)

bp_class = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
actor = actor_sub.spawn_actor_from_class(bp_class, unreal.Vector(0, 0, 125), unreal.Rotator(0, 0, 0))

unreal.log(f"Spawned actor: {actor}")
for c in actor.get_components_by_class(unreal.SceneComponent):
    if "WeaponAxe" in c.get_name():
        unreal.log(f"Found {c.get_name()}:")
        unreal.log(f"  AttachParent: {c.get_attach_parent()}")
        unreal.log(f"  AttachSocket: {c.get_attach_socket_name()}")
        unreal.log(f"  WorldLoc: {c.get_world_location()}")
        unreal.log(f"  WorldRot: {c.get_world_rotation()}")
        unreal.log(f"  IsVisible: {c.is_visible()}")
        unreal.log(f"  StaticMesh: {c.get_editor_property('static_mesh')}")

mesh = actor.get_component_by_class(unreal.SkeletalMeshComponent)
if mesh:
    unreal.log(f"Mesh Socket hand_rSocket WorldLoc: {mesh.get_socket_location(unreal.Name('hand_rSocket'))}")
    unreal.log(f"Mesh Socket hand_rSocket WorldRot: {mesh.get_socket_rotation(unreal.Name('hand_rSocket'))}")
