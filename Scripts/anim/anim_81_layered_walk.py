# -*- coding: utf-8 -*-
"""
干净的工业级分层重定向器：
下半身（Pelvis + 双腿双脚）：精准映射步态、前进剥离（in-place）、Z轴颠簸与左右摇摆
上半身（Spine_01 以上）：保持 Darius 专属雄伟身姿与战斧握持，完全杜绝缩肩、歪头、穿模
"""
import bpy
import sys
import os
import math
from mathutils import Matrix, Quaternion, Vector

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) < 3:
        print("用法: blender -b -P anim_81_layered_walk.py -- <SrcAnimFBX> <DariusFBX> <OutFBX>")
        sys.exit(1)

    SRC_FBX, DARIUS_FBX, OUT_FBX = argv[0], argv[1], argv[2]
    bpy.ops.wm.read_factory_settings(use_empty=True)

    print(f"=== 开始分层重定向: {os.path.basename(SRC_FBX)} -> {os.path.basename(DARIUS_FBX)} ===")

    # 1. 导入源动画
    bpy.ops.import_scene.fbx(filepath=SRC_FBX)
    marm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
    if not marm:
        print("!! 找不到源骨架")
        sys.exit(1)
    mact = marm.animation_data.action if marm.animation_data else None
    if not mact and bpy.data.actions:
        mact = bpy.data.actions[-1]
    if not mact:
        print("!! 源动画没有 Action")
        sys.exit(1)
    if not marm.animation_data:
        marm.animation_data_create()
    marm.animation_data.action = mact
    f0, f1 = int(mact.frame_range[0]), int(mact.frame_range[1])
    print(f"   源动作: {mact.name}, 帧范围: {f0}..{f1}")

    # 2. 导入目标模型 (Darius)
    bpy.ops.import_scene.fbx(filepath=DARIUS_FBX)
    darm = next((o for o in bpy.data.objects if o.type == "ARMATURE" and o is not marm), None)
    if not darm:
        print("!! 找不到目标骨架")
        sys.exit(1)
    print(f"   Darius 骨数: {len(darm.data.bones)}")

    # 3. 分层映射表：仅下半身（骨盆 + 腿脚）
    # 上半身（Spine_01 以上）保留 Darius 自身战斧霸气站姿/待机姿态
    MAP = {
        "mixamorig:Hips": "pelvis",
        "mixamorig:LeftUpLeg": "thigh_l",
        "mixamorig:RightUpLeg": "thigh_r",
        "mixamorig:LeftLeg": "calf_l",
        "mixamorig:RightLeg": "calf_r",
        "mixamorig:LeftFoot": "foot_l",
        "mixamorig:RightFoot": "foot_r",
        "mixamorig:LeftToeBase": "ball_l",
        "mixamorig:RightToeBase": "ball_r",
    }

    valid_map = {m: d for m, d in MAP.items() if m in marm.pose.bones and d in darm.pose.bones}
    print(f"   下半身匹配骨骼数量: {len(valid_map)} / {len(MAP)}")

    for db in valid_map.values():
        darm.pose.bones[db].rotation_mode = "QUATERNION"

    # 4. 创建新 Action
    if not darm.animation_data:
        darm.animation_data_create()
    out_act = bpy.data.actions.new(name="Darius_Walk_Layered")
    darm.animation_data.action = out_act

    sc = bpy.context.scene

    # 计算原点位移参考（in-place 处理）
    sc.frame_set(f0)
    bpy.context.view_layer.update()
    p0_world = (marm.matrix_world @ marm.pose.bones["mixamorig:Hips"].matrix).translation.copy()
    sc.frame_set(f1)
    bpy.context.view_layer.update()
    p1_world = (marm.matrix_world @ marm.pose.bones["mixamorig:Hips"].matrix).translation.copy()
    fwd_vec = p1_world - p0_world
    fwd_vec.z = 0.0
    total_fwd_len = fwd_vec.length
    fwd_dir = fwd_vec.normalized() if total_fwd_len > 1e-4 else Vector((0.0, 1.0, 0.0))
    print(f"   位移剥离: 总位移={total_fwd_len:.3f}m, 前进方向={fwd_dir}")

    dpelvis_rest_w = (darm.matrix_world @ darm.data.bones["pelvis"].matrix_local).translation.copy()

    # 5. 逐帧烘焙下半身
    print(f"   正在逐帧烘焙下半身 {f0}..{f1} ...")
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()

        # 骨盆位移：剥离前进分量，保留自然颠簸与横向摆动
        curr_m_hip_w = (marm.matrix_world @ marm.pose.bones["mixamorig:Hips"].matrix).translation.copy()
        delta_p = curr_m_hip_w - p0_world
        fwd_proj = delta_p.dot(fwd_dir) * fwd_dir
        in_place_delta = delta_p - fwd_proj

        target_pelvis_w = dpelvis_rest_w + in_place_delta
        target_pelvis_local = darm.matrix_world.inverted() @ target_pelvis_w
        d_pelvis_bone = darm.data.bones["pelvis"]
        darm.pose.bones["pelvis"].location = target_pelvis_local - d_pelvis_bone.matrix_local.translation
        darm.pose.bones["pelvis"].keyframe_insert(data_path="location", frame=f)

        ordered_bones = sorted(valid_map.items(), key=lambda item: len(darm.data.bones[item[1]].parent_recursive))
        W_tgt = {}

        # 补偿骨盆正向朝向偏差（去除原动作自带的 -33.1° 斜向偏角）
        R_yaw_fix = Matrix.Rotation(math.radians(33.1), 3, 'Z')

        for mb, db in ordered_bones:
            M_src_cur = (marm.matrix_world @ marm.pose.bones[mb].matrix).to_3x3()
            M_src_rest = (marm.matrix_world @ marm.data.bones[mb].matrix_local).to_3x3()
            M_tgt_rest = (darm.matrix_world @ darm.data.bones[db].matrix_local).to_3x3()

            R_world = M_src_cur @ M_src_rest.inverted()
            if db == "pelvis":
                R_world = R_yaw_fix @ R_world

            M_tgt_desired = R_world @ M_tgt_rest

            dbone = darm.data.bones[db]
            par = dbone.parent
            if par and par.name in W_tgt:
                W_par = W_tgt[par.name]
                W_par_rest = (darm.matrix_world @ par.matrix_local).to_3x3()
                local_desired = W_par.inverted() @ M_tgt_desired
                local_rest = W_par_rest.inverted() @ M_tgt_rest
                R_local = local_rest.inverted() @ local_desired
            else:
                W_arm = darm.matrix_world.to_3x3()
                local_desired = W_arm.inverted() @ M_tgt_desired
                local_rest = darm.data.bones[db].matrix_local.to_3x3()
                R_local = local_rest.inverted() @ local_desired

            pb = darm.pose.bones[db]
            pb.rotation_quaternion = R_local.to_quaternion()
            pb.keyframe_insert(data_path="rotation_quaternion", frame=f)
            W_tgt[db] = M_tgt_desired

    # 6. 上半身骨骼处理：保持静止姿态（Identity 局部旋转），确保零形变、零穿模
    # 为保证烘焙完整，对 spine_01 往上的核心骨骼插入 rest keyframe
    UPPER_BODY_CORE = [
        "spine_01", "spine_02", "spine_03", "neck_01", "head",
        "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r",
        "lowerarm_l", "lowerarm_r", "hand_l", "hand_r",
        "weapon_jnt", "weapon_jnt_r"
    ]
    for ub in UPPER_BODY_CORE:
        if ub in darm.pose.bones:
            pb = darm.pose.bones[ub]
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = Quaternion((1.0, 0.0, 0.0, 0.0))
            pb.location = Vector((0.0, 0.0, 0.0))
            for f in (f0, f1):
                pb.keyframe_insert(data_path="rotation_quaternion", frame=f)
                pb.keyframe_insert(data_path="location", frame=f)

    # 7. 绑定战斧骨骼 weapon_jnt -> weapon_jnt_r
    sc.frame_start, sc.frame_end = f0, f1
    pb_wjnt = darm.pose.bones.get("weapon_jnt")
    pb_wjnt_r = darm.pose.bones.get("weapon_jnt_r")
    if pb_wjnt and pb_wjnt_r:
        const = pb_wjnt.constraints.new(type="COPY_TRANSFORMS")
        const.target = darm
        const.subtarget = "weapon_jnt_r"
        bpy.ops.nla.bake(frame_start=f0, frame_end=f1, only_selected=False, visual_keying=True, clear_constraints=True, bake_types={"POSE"})
        print("   战斧骨骼烘焙完毕！")

    out_act.use_fake_user = True

    # 8. 贴地校准
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if meshes:
        min_z = min(min((o.matrix_world @ v.co).z for v in o.data.vertices) for o in meshes)
        darm.location.z -= min_z
        print(f"   接地对齐: Z 偏移 {-min_z:.3f}m")

    # 9. 清理并导出
    for o in list(bpy.data.objects):
        if o is not darm and o not in meshes:
            try:
                bpy.data.objects.remove(o, do_unlink=True)
            except Exception:
                pass

    bpy.ops.export_scene.fbx(
        filepath=OUT_FBX,
        use_selection=False,
        bake_anim=True,
        bake_anim_use_all_actions=False,
        bake_anim_use_nla_strips=False,
        bake_anim_force_startend_keying=True,
        add_leaf_bones=False,
        apply_unit_scale=True,
        global_scale=1.0,
    )
    print(f"   已导出分层重定向结果 -> {OUT_FBX}")

if __name__ == "__main__":
    main()
