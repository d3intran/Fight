import unreal

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actor = [a for a in actor_sub.get_all_level_actors() if "BP_DariusCharacter" in a.get_name()][0]
mesh = actor.get_component_by_class(unreal.SkeletalMeshComponent)

# Get bone locations
for b in ["head", "hand_r", "hand_l", "foot_r", "foot_l", "clavicle_r", "clavicle_l"]:
    b_name = unreal.Name(b)
    loc = mesh.get_socket_location(b_name)
    unreal.log(f"Bone {b:12s}: world={loc}")
