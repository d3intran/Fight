import unreal

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actor = [a for a in actor_sub.get_all_level_actors() if "BP_DariusCharacter" in a.get_name()][0]
unreal.log(f"Actor Rotation: {actor.get_actor_rotation()}")

mesh = actor.get_component_by_class(unreal.SkeletalMeshComponent)
unreal.log(f"Mesh RelRot: {mesh.get_editor_property('relative_rotation')}")
unreal.log(f"Mesh WorldRot: {mesh.get_world_rotation()}")

# Which direction is forward in mesh space?
# Head location vs Pelvis location
head_loc = mesh.get_socket_location(unreal.Name("head"))
pelvis_loc = mesh.get_socket_location(unreal.Name("pelvis"))
unreal.log(f"Head: {head_loc}, Pelvis: {pelvis_loc}")
