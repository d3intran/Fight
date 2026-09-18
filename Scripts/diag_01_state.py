import unreal

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
print("=== [1] PIE 状态 ===")
print("is_in_play_in_editor:", les.is_in_play_in_editor())

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()
print("EditorWorld:", ew.get_name())

print()
print("=== [2] SK_Darius_GodKing 资产 ===")
sk = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
print("Loaded:", sk)
mats = sk.get_editor_property("materials")
for i, m in enumerate(mats):
    mi = m.get_editor_property("material_interface")
    print(f"  Slot[{i}] name={m.get_editor_property('material_slot_name')} -> {mi.get_path_name() if mi else None}")

print()
print("--- Sockets ---")
sockets = sk.get_editor_property("sockets")
for s in sockets:
    print(f"  Socket: {s.get_editor_property('socket_name')} parent={s.get_editor_property('parent_socket_name')} "
          f"relLoc={s.get_editor_property('relative_location')} relRot={s.get_editor_property('relative_rotation')} "
          f"relScale={s.get_editor_property('relative_scale')}")

print()
print("=== [3] 骨骼参考姿态缩放 (前 6 根) ===")
ref_pose = sk.get_editor_property("reference_skeleton")
print("ReferenceSkeleton bones count:", ref_pose.get_num() if hasattr(ref_pose, "get_num") else "n/a")
try:
    for i in range(0, 6):
        info = ref_pose.get_reference_bone_info(i)
        print(f"  Bone[{i}] {info.get_editor_property('name')} parentIdx={info.get_editor_property('parent_index')} "
              f"pose={info.get_editor_property('local_pose')}")
except Exception as e:
    print("  err:", e)

print()
print("=== [4] SM_Darius_GodKing_Axe 资产 ===")
sm = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")
print("Loaded:", sm)
if sm:
    bb = sm.get_bounds()
    print("  Bounds BoxExtent:", bb.box_extent, " Origin:", bb.origin, " SphereRadius:", bb.sphere_radius)
    try:
        mats2 = sm.get_editor_property("static_materials")
        for i, m in enumerate(mats2):
            mi = m.get_editor_property("material_interface")
            print(f"  Slot[{i}] {m.get_editor_property('material_slot_name')} -> {mi.get_path_name() if mi else None}")
    except Exception as e:
        print("  mats err:", e)
    print("  Sockets:", [s.get_editor_property('socket_name') for s in sm.get_editor_property('sockets')])

print()
print("=== [5] 编辑器关卡中 Darius Actor ===")
for a in unreal.GameplayStatics.get_all_actors_of_class(ew, unreal.Actor):
    if "Darius" in a.get_name() or "Darius" in a.get_class().get_name():
        print("Actor:", a.get_name(), a.get_class().get_name())
        print("  Loc:", a.get_actor_location(), "Scale:", a.get_actor_scale3d())
        for c in a.get_components_by_class(unreal.ActorComponent):
            extra = ""
            if isinstance(c, unreal.SceneComponent):
                extra = f" relLoc={c.get_editor_property('relative_location')} relScale={c.get_editor_property('relative_scale3d')}"
                try:
                    extra += f" attach={c.get_attach_parent()}"
                except Exception:
                    pass
            print(f"    - {c.get_name()} ({c.get_class().get_name()}){extra}")

print()
print("=== [6] BP_DariusCharacter SCS 节点 ===")
bp = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/Blueprints/BP_DariusCharacter")
print("BP:", bp)
try:
    cls = bp.generated_class()
    cdo = unreal.get_default_object(cls)
    for c in cdo.get_components_by_class(unreal.ActorComponent):
        print(f"  CDO comp: {c.get_name()} ({c.get_class().get_name()})")
        if isinstance(c, unreal.StaticMeshComponent):
            print("     mesh:", c.get_editor_property("static_mesh"))
            print("     relScale:", c.get_editor_property("relative_scale3d"))
            print("     absScale:", c.get_editor_property("absolute_scale"))
        if isinstance(c, unreal.SceneComponent):
            try:
                print("     attachSocket:", c.get_editor_property("attach_socket_name"))
            except Exception:
                pass
except Exception as e:
    print("  err:", e)
print("=== DONE ===")
