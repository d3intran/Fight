"""
=============================================================================
 武器与骨骼拓扑探查脚本 (inspect_weapon_rig.py)
 -----------------------------------------------------------------------------
 作用：
 1. 深度解析神王德莱厄斯骨骼中关于武器骨骼（weapon_jnt 等）与右手（hand_r）
    在参考姿态（Reference / Bind Pose）下的世界坐标与相对层级。
 2. 计算战斧几何中心、手部握柄偏移量，为武器自动吸附与挂载提供数学基准。
 3. 查询当前骨骼已存在的 Socket 列表。
=============================================================================
"""

import unreal

eal = unreal.EditorAssetLibrary

sk_mesh_path = "/Game/Character/Darius/SK_Darius_GodKing"
skel_path = "/Game/Character/Darius/SK_Darius_GodKing_Skeleton"

sk_mesh = eal.load_asset(sk_mesh_path)
skel = eal.load_asset(skel_path)

ref_pose = skel.get_reference_pose()
bone_names = [str(b) for b in ref_pose.get_bone_names()]

unreal.log("==================== [WEAPON RIG INSPECTION] ====================")

target_bones = ['root', 'pelvis', 'hand_r', 'hand_l', 'weapon_jnt', 'weapon_jnt_r', 'weapon_jnt_l', 'weapon_jnt_offset']
for b in target_bones:
    if b in bone_names:
        # Get ref pose relative transform
        rel_trans = ref_pose.get_ref_bone_pose(b)
        unreal.log(f"Bone [{b}]: loc={rel_trans.translation}, rot={rel_trans.rotation.rotator()}, scale={rel_trans.scale3d}")
    else:
        unreal.log(f"Bone [{b}]: NOT FOUND")

# Check existing sockets on Skeleton and Mesh
skel_sockets = skel.get_editor_property('sockets')
unreal.log(f"Skeleton sockets count: {len(skel_sockets)}")
for s in skel_sockets:
    unreal.log(f"  Skeleton Socket: {s.get_editor_property('socket_name')} on bone {s.get_editor_property('bone_name')}")

mesh_sockets = sk_mesh.get_editor_property('sockets')
unreal.log(f"Mesh sockets count: {len(mesh_sockets)}")
for s in mesh_sockets:
    unreal.log(f"  Mesh Socket: {s.get_editor_property('socket_name')} on bone {s.get_editor_property('bone_name')}")

unreal.log("=================================================================")
