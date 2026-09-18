import unreal

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in actor_sub.get_all_level_actors():
    if "BP_DariusCharacter" in a.get_name():
        unreal.log(f"Found Actor: {a.get_name()} at {a.get_actor_location()}, rot: {a.get_actor_rotation()}")
        for m in a.get_components_by_class(unreal.SkeletalMeshComponent):
            unreal.log(f"SkeletalMeshComp: {m.get_name()}, RelRot: {m.get_editor_property('relative_rotation')}, WorldRot: {m.get_world_rotation()}")
        for c in a.get_components_by_class(unreal.SceneComponent):
            if "Weapon" in c.get_name() or isinstance(c, unreal.StaticMeshComponent):
                unreal.log(f"Component: {c.get_name()} ({type(c)})")
                unreal.log(f"  Parent: {c.get_attach_parent()}")
                unreal.log(f"  Socket: {c.get_attach_socket_name()}")
                unreal.log(f"  WorldLoc: {c.get_world_location()}")
                unreal.log(f"  WorldRot: {c.get_world_rotation()}")
                unreal.log(f"  RelLoc: {c.get_editor_property('relative_location')}")
                unreal.log(f"  RelRot: {c.get_editor_property('relative_rotation')}")
                unreal.log(f"  RelScale: {c.get_editor_property('relative_scale3d')}")
                unreal.log(f"  Visible: {c.is_visible()}")
                if isinstance(c, unreal.StaticMeshComponent):
                    unreal.log(f"  StaticMesh: {c.get_editor_property('static_mesh')}")
                    mesh = c.get_editor_property('static_mesh')
                    if mesh:
                        unreal.log(f"  Mesh bounds: {mesh.get_bounds()}")
                        unreal.log(f"  Num materials: {mesh.get_num_sections(0) if hasattr(mesh, 'get_num_sections') else 'N/A'}")
                        for i in range(mesh.get_num_sections(0) if hasattr(mesh, 'get_num_sections') else 1):
                            unreal.log(f"    Mat {i}: {mesh.get_material(i)}")
