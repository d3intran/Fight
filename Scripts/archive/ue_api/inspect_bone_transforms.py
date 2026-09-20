import unreal

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in actor_sub.get_all_level_actors():
    if "BP_DariusCharacter" in a.get_name():
        for m in a.get_components_by_class(unreal.SkeletalMeshComponent):
            unreal.log(f"Mesh: {m.get_name()}, AnimClass: {m.get_editor_property('anim_class')}")
            for b in ["root", "pelvis", "spine_01", "head", "hand_r", "hand_l", "weapon_r", "weapon_l"]:
                b_name = unreal.Name(b)
                loc = m.get_socket_location(b_name)
                rot = m.get_socket_rotation(b_name)
                unreal.log(f"  Bone [{b}]: loc={loc}, rot={rot}")
            for s in ["hand_rSocket", "hand_lSocket"]:
                s_name = unreal.Name(s)
                loc = m.get_socket_location(s_name)
                rot = m.get_socket_rotation(s_name)
                unreal.log(f"  Socket [{s}]: loc={loc}, rot={rot}")
