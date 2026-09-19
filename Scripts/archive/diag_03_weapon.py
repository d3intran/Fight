import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()

print("=== WeaponAxe 组件实况 ===")
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "Darius" not in a.get_name():
        continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if "Weapon" not in c.get_name() and "Axe" not in c.get_name():
            continue
        print("Comp:", c.get_name())
        print("  WorldLoc:", c.get_world_location())
        print("  WorldScale:", c.get_world_scale())
        print("  WorldRot:", c.get_world_rotation())
        print("  RelScale:", c.get_editor_property("relative_scale3d"))
        print("  AbsScale:", c.get_editor_property("absolute_scale"))
        print("  AttachSocket:", c.get_editor_property("attach_socket_name"))
        sm = c.get_editor_property("static_mesh")
        print("  StaticMesh:", sm.get_path_name() if sm else None)
        if sm:
            bb = sm.get_bounds()
            print("  MeshBounds Extent:", bb.box_extent, "Origin:", bb.origin)
            try:
                for i in range(sm.get_num_sections(0)):
                    pass
            except Exception:
                pass
        # 每槽材质
        try:
            n = c.get_num_materials()
            for i in range(n):
                mi = c.get_material(i)
                print(f"  Slot[{i}] -> {mi.get_path_name() if mi else None}")
        except Exception as e:
            print("  mat err:", e)

print()
print("=== CharacterMesh0 材质槽实况 (PIE) ===")
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "Darius" not in a.get_name():
        continue
    mesh = a.get_component_by_class(unreal.SkeletalMeshComponent)
    print("Mesh comp:", mesh.get_name())
    n = mesh.get_num_materials()
    print("num materials:", n)
    for i in range(n):
        mi = mesh.get_material(i)
        print(f"  Slot[{i}] -> {mi.get_path_name() if mi else None}")
    ska = mesh.get_editor_property("skeletal_mesh_asset")
    print("SK asset:", ska.get_path_name() if ska else None)
    print("NumBones:", mesh.get_num_bones())
    for i in [0, 1, 2]:
        if i < mesh.get_num_bones():
            bn = mesh.get_bone_name(i)
            cs = mesh.get_socket_transform(bn, unreal.RelativeTransformSpace.RTS_COMPONENT)
            print(f"  Bone[{i}] {bn} compSpace scale={cs.scale3d}")
    # 骨骼 socket 列表
    try:
        sks = ska.get_editor_property("sockets")
        print("SK sockets count:", len(sks))
        for s in sks:
            print("   ", s.get_editor_property("socket_name"), "relScale=", s.get_editor_property("relative_scale"))
    except Exception as e:
        print("  socket list err:", e)
print("=== DONE ===")
