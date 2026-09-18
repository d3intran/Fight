import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()
print("EditorWorld:", ew.get_name() if ew else None)

sk = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
print("SK:", sk)
s = sk.find_socket(unreal.Name("hand_rSocket"))
print("hand_rSocket:", s)
if s:
    print("  relScale:", s.get_editor_property("relative_scale"))
    print("  relLoc:", s.get_editor_property("relative_location"))
    print("  relRot:", s.get_editor_property("relative_rotation"))
    print("  boneName:", s.get_editor_property("bone_name"))
print("All socket names on SK:")
try:
    for n in sk.get_editor_property("sockets"):
        print("   ", n.get_editor_property("socket_name"), n.get_editor_property("relative_scale"))
except Exception as e:
    print("   list err:", e)

print()
print("=== M_Invisible 材质设置 ===")
mi = unreal.EditorAssetLibrary.load_asset("/Game/Character/Darius/Materials/M_Invisible")
print("M_Invisible:", mi)
if mi:
    for prop in ["blend_mode", "shading_model", "two_sided", "opacity_mask_clip_value",
                 "material_domain", "b_cast_dynamic_shadow_as_masked", "used_with_skeletal_mesh"]:
        try:
            print(f"  {prop}:", mi.get_editor_property(prop))
        except Exception as e:
            print(f"  {prop}: <{e}>")
    try:
        print("  base_color expr:", mi.get_editor_property("base_color"))
    except Exception as e:
        print("  base_color err", e)

print()
print("=== 编辑器世界中的 Darius ===")
found = False
for a in unreal.GameplayStatics.get_all_actors_of_class(ew, unreal.Actor):
    if "Darius" in a.get_name():
        found = True
        print("Actor:", a.get_name(), "loc:", a.get_actor_location())
        for c in a.get_components_by_class(unreal.ActorComponent):
            if isinstance(c, unreal.StaticMeshComponent):
                print("   StaticMeshComp:", c.get_name(), "worldScale:", c.get_world_scale(),
                      "mesh:", c.get_editor_property("static_mesh"))
                try:
                    print("      socket:", c.get_attach_socket_name())
                except Exception:
                    pass
        mesh = a.get_component_by_class(unreal.SkeletalMeshComponent)
        if mesh:
            print("   SkeletalMesh worldScale:", mesh.get_world_scale())
            print("   hand_rSocket world scale:", mesh.get_socket_transform(unreal.Name("hand_rSocket"),
                                                                          unreal.RelativeTransformSpace.RTS_WORLD).scale3d)
            print("   num materials:", mesh.get_num_materials())
            for i in range(mesh.get_num_materials()):
                print(f"      Slot[{i}] ->", mesh.get_material(i))
if not found:
    print("  (编辑器关卡中无 Darius Actor)")

print()
print("=== SK 全部骨骼名 (供重定向映射) ===")
if sk:
    ref = sk.get_editor_property("reference_skeleton")
    try:
        cnt = ref.get_num()
        print("bone count:", cnt)
        names = []
        for i in range(cnt):
            info = ref.get_reference_bone_info(i)
            names.append(str(info.get_editor_property("name")))
        print(names)
    except Exception as e:
        print("  err:", e)
print("=== DONE ===")
