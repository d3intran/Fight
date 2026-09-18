import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()

def safe(fn, label):
    try:
        return fn()
    except Exception as e:
        print(f"   [{label} ERR] {e}")
        return None

print("=== WeaponAxe ===")
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "Darius" not in a.get_name():
        continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if "Weapon" not in c.get_name() and "Axe" not in c.get_name():
            continue
        print("Comp:", c.get_name())
        print("  WorldLoc:", c.get_world_location())
        print("  WorldScale:", c.get_world_scale())
        sm = c.get_editor_property("static_mesh")
        print("  StaticMesh:", sm.get_path_name() if sm else None)
        if sm:
            bb = sm.get_bounds()
            print("  MeshBounds Extent:", bb.box_extent, "Origin:", bb.origin)
        print("  AttachSocketName:", safe(lambda: c.get_attach_socket_name(), "attachsock"))
        print("  AttachParent:", safe(lambda: c.get_attach_parent().get_name(), "attachparent"))
        n = safe(lambda: c.get_num_materials(), "nummat")
        if n is not None:
            for i in range(n):
                mi = c.get_material(i)
                print(f"  Slot[{i}] -> {mi.get_path_name() if mi else None}")

print()
print("=== CharacterMesh0 ===")
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "Darius" not in a.get_name():
        continue
    mesh = a.get_component_by_class(unreal.SkeletalMeshComponent)
    ska = mesh.get_editor_property("skeletal_mesh_asset")
    print("SK:", ska.get_path_name() if ska else None)
    n = mesh.get_num_materials()
    print("num materials:", n)
    for i in range(n):
        mi = mesh.get_material(i)
        print(f"  Slot[{i}] -> {mi.get_path_name() if mi else None}")
    print("NumBones:", mesh.get_num_bones())
    for i in range(0, 8):
        if i < mesh.get_num_bones():
            bn = mesh.get_bone_name(i)
            cs = mesh.get_socket_transform(bn, unreal.RelativeTransformSpace.RTS_COMPONENT)
            ps = mesh.get_socket_transform(bn, unreal.RelativeTransformSpace.RTS_PARENT_BONE_SPACE)
            print(f"  Bone[{i}] {bn} | compScale={cs.scale3d} | parentScale={ps.scale3d}")
    if ska:
        sks = safe(lambda: ska.get_editor_property("sockets"), "sockets")
        if sks is not None:
            print("SK sockets count:", len(sks))
            for s in sks:
                print("   ", s.get_editor_property("socket_name"),
                      "parent=", s.get_editor_property("parent_socket_name"),
                      "relScale=", s.get_editor_property("relative_scale"),
                      "relLoc=", s.get_editor_property("relative_location"))
        mats = safe(lambda: ska.get_editor_property("materials"), "skmats")
        if mats is not None:
            print("SK material slots:", len(mats))
            for i, m in enumerate(mats):
                mi = m.get_editor_property("material_interface")
                print(f"   Slot[{i}] {m.get_editor_property('material_slot_name')} -> {mi.get_path_name() if mi else None}")
print("=== DONE ===")
