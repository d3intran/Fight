import unreal

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
print("=== [1] PIE 状态 ===")
in_pie = les.is_in_play_in_editor()
print("is_in_play_in_editor:", in_pie)

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
ew = ues.get_editor_world()
print("GameWorld:", gw.get_name() if gw else None)
print("EditorWorld:", ew.get_name() if ew else None)

print()
print("=== [2] SK_Darius_GodKing 资产 ===")
sk = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
print("Loaded:", sk)
if sk:
    mats = sk.get_editor_property("materials")
    for i, m in enumerate(mats):
        mi = m.get_editor_property("material_interface")
        print(f"  Slot[{i}] name={m.get_editor_property('material_slot_name')} -> {mi.get_path_name() if mi else None}")
    print("--- Sockets ---")
    for s in sk.get_editor_property("sockets"):
        print(f"  Socket: {s.get_editor_property('socket_name')} parent={s.get_editor_property('parent_socket_name')} "
              f"relLoc={s.get_editor_property('relative_location')} relRot={s.get_editor_property('relative_rotation')} "
              f"relScale={s.get_editor_property('relative_scale')}")

print()
print("=== [3] SM_Darius_GodKing_Axe 资产 ===")
sm = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")
print("Loaded:", sm)
if sm:
    bb = sm.get_bounds()
    print("  Bounds BoxExtent:", bb.box_extent, " Origin:", bb.origin, " SphereRadius:", bb.sphere_radius)
    for i, m in enumerate(sm.get_editor_property("static_materials")):
        mi = m.get_editor_property("material_interface")
        print(f"  Slot[{i}] {m.get_editor_property('material_slot_name')} -> {mi.get_path_name() if mi else None}")
    print("  Sockets:", [s.get_editor_property('socket_name') for s in sm.get_editor_property('sockets')])

print()
print("=== [4] 世界中 Darius Actor（GameWorld） ===")
target_world = gw if gw else ew
if target_world:
    for a in unreal.GameplayStatics.get_all_actors_of_class(target_world, unreal.Actor):
        if "Darius" in a.get_name() or "Darius" in a.get_class().get_name():
            print("Actor:", a.get_name(), "|", a.get_class().get_name())
            print("  Loc:", a.get_actor_location(), "Scale:", a.get_actor_scale3d())
            for c in a.get_components_by_class(unreal.ActorComponent):
                extra = ""
                if isinstance(c, unreal.SceneComponent):
                    extra = f" relLoc={c.get_editor_property('relative_location')} relScale={c.get_editor_property('relative_scale3d')}"
                print(f"    - {c.get_name()} ({c.get_class().get_name()}){extra}")
            for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
                print("  >>> SkeletalMesh comp:", c.get_name())
                print("      mesh asset:", c.get_editor_property("skeletal_mesh_asset"))
                print("      comp relScale:", c.get_editor_property("relative_scale3d"), " worldScale:", c.get_world_scale())
                try:
                    st = c.get_socket_transform(unreal.Name("hand_rSocket"), unreal.RelativeTransformSpace.RTS_WORLD)
                    print("      hand_rSocket WORLD:", st.translation, st.rotation, st.scale3d)
                except Exception as e:
                    print("      socket err:", e)

print()
print("=== [5] BP_DariusCharacter CDO ===")
bp = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/Blueprints/BP_DariusCharacter")
print("BP:", bp)
if bp:
    cls = bp.generated_class()
    cdo = unreal.get_default_object(cls)
    for c in cdo.get_components_by_class(unreal.ActorComponent):
        line = f"  CDO comp: {c.get_name()} ({c.get_class().get_name()})"
        print(line)
        if isinstance(c, unreal.SceneComponent):
            print("     relLoc:", c.get_editor_property("relative_location"))
            print("     relScale:", c.get_editor_property("relative_scale3d"))
            print("     attachSocket:", c.get_editor_property("attach_socket_name"))
        if isinstance(c, unreal.StaticMeshComponent):
            print("     staticMesh:", c.get_editor_property("static_mesh"))
print("=== DONE ===")
