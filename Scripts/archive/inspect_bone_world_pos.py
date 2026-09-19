import unreal

eal = unreal.EditorAssetLibrary

sk_mesh = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
skel = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")
ref_pose = skel.get_reference_pose()

# Get world transform of hand_r and weapon_jnt in reference pose
# We can evaluate bone path from root
def get_world_bone_transform(bone_name):
    # Traverse up to root
    curr = bone_name
    trans_list = []
    # Let's inspect bone hierarchy
    # In ref pose, get_ref_bone_pose gives local transform relative to parent
    return ref_pose.get_ref_bone_pose(bone_name)

unreal.log(f"hand_r local: {get_world_bone_transform('hand_r')}")
unreal.log(f"weapon_jnt local: {get_world_bone_transform('weapon_jnt')}")

# Also let's check bone position on SkeletalMeshComponent of Darius_Player
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in actor_sub.get_all_level_actors():
    if a.get_actor_label() == 'Darius_Player':
        sk_comp = a.get_component_by_class(unreal.SkeletalMeshComponent)
        if sk_comp:
            hand_r_trans = sk_comp.get_socket_transform('hand_r', unreal.RelativeTransformSpace.RTS_WORLD)
            weapon_trans = sk_comp.get_socket_transform('weapon_jnt', unreal.RelativeTransformSpace.RTS_WORLD)
            unreal.log(f"Darius_Player hand_r World Location: {hand_r_trans.translation}")
            unreal.log(f"Darius_Player weapon_jnt World Location: {weapon_trans.translation}")
