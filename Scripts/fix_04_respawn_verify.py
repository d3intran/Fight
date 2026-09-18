import unreal

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in actor_sub.get_all_level_actors():
    if "BP_DariusCharacter" in a.get_name():
        actor_sub.destroy_actor(a)

bp_class = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
actor = actor_sub.spawn_actor_from_class(bp_class, unreal.Vector(0, 0, 125), unreal.Rotator(0, 0, 180))
actor.set_actor_label("DariusDiag")
print("respawned:", actor.get_name())
mesh = actor.get_component_by_class(unreal.SkeletalMeshComponent)
st = mesh.get_socket_transform(unreal.Name("hand_rSocket"), unreal.RelativeTransformSpace.RTS_WORLD)
print("hand_rSocket world scale:", st.scale3d)
for c in actor.get_components_by_class(unreal.StaticMeshComponent):
    if "Weapon" in c.get_name():
        print("WeaponAxe worldScale:", c.get_world_scale())
        print("WeaponAxe worldLoc:", c.get_world_location())
        print("WeaponAxe relScale:", c.get_editor_property("relative_scale3d"))
        bb = c.get_editor_property("static_mesh").get_bounds()
        print("mesh bounds extent:", bb.box_extent)
        print("=> 世界尺寸(cm): X", bb.box_extent.x * 2 * c.get_world_scale().x,
              " Y", bb.box_extent.y * 2 * c.get_world_scale().y,
              " Z", bb.box_extent.z * 2 * c.get_world_scale().z)
print("=== DONE ===")
