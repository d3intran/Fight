import unreal

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith("BP_DariusCharacter") or a.get_name().startswith("CameraActor_"):
        actor_sub.destroy_actor(a)

bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
actor = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125), unreal.Rotator(0, 0, 180))
print("spawned:", actor.get_name())

mesh = actor.get_component_by_class(unreal.SkeletalMeshComponent)
ska = mesh.get_editor_property("skeletal_mesh_asset")
print("SK:", ska.get_path_name())
print("材质槽:")
for i in range(mesh.get_num_materials()):
    print(f"   Slot[{i}] ->", mesh.get_material(i))
print("骨骼数:", mesh.get_num_bones())
cs = mesh.get_socket_transform(unreal.Name("root"), unreal.RelativeTransformSpace.RTS_COMPONENT)
print("root 骨骼 ComponentSpace 缩放:", cs.scale3d)
st = mesh.get_socket_transform(unreal.Name("hand_rSocket"), unreal.RelativeTransformSpace.RTS_WORLD)
print("hand_rSocket 世界缩放:", st.scale3d, "位置:", st.translation)

for c in actor.get_components_by_class(unreal.StaticMeshComponent):
    if "Weapon" in c.get_name():
        print("WeaponAxe 世界缩放:", c.get_world_scale(), "世界位置:", c.get_world_location())
        sm = c.get_editor_property("static_mesh")
        bb = sm.get_bounds()
        ws = c.get_world_scale()
        print("  战斧世界尺寸(cm): X %.1f  Y %.1f  Z %.1f" % (bb.box_extent.x*2*ws.x, bb.box_extent.y*2*ws.y, bb.box_extent.z*2*ws.z))

sk = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
b = sk.get_bounds()
print("SK 包围盒 z 范围: %.1f ~ %.1f" % (b.origin.z - b.box_extent.z, b.origin.z + b.box_extent.z))

# 动画资产复核
seq = unreal.load_asset("/Game/Character/Darius/Anims/A_Darius_LOL_Run_TP")
print("AnimSequence:", seq, "len:", round(seq.get_editor_property("sequence_length"),3),
      "skeleton:", seq.get_editor_property("skeleton"))
print("=== DONE ===")
