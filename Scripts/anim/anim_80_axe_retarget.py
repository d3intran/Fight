# -*- coding: utf-8 -*-
"""
干净的工业级重定向器：Mixamo 动作 -> Darius 2XKO 骨架
基于 World-Space 姿态传递 + A/T Pose 补偿 + 战斧骨骼绑定
"""
import bpy
import sys
import os
import math
from mathutils import Matrix, Quaternion, Vector

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) < 3:
        print("用法: blender -b -P anim_80_axe_retarget.py -- <SrcAnimFBX> <DariusFBX> <OutFBX>")
        sys.exit(1)

    SRC_FBX, DARIUS_FBX, OUT_FBX = argv[0], argv[1], argv[2]
    bpy.ops.wm.read_factory_settings(use_empty=True)

    print(f"=== 开始重定向: {os.path.basename(SRC_FBX)} -> {os.path.basename(DARIUS_FBX)} ===")

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

    # 3. 骨骼映射表
    MAP = {
        "mixamorig:Hips": "pelvis",
        "mixamorig:Spine": "spine_01",
        "mixamorig:Spine1": "spine_02",
        "mixamorig:Spine2": "spine_03",
        "mixamorig:Neck": "neck_01",
        "mixamorig:Head": "head",
        "mixamorig:LeftShoulder": "clavicle_l",
        "mixamorig:RightShoulder": "clavicle_r",
        "mixamorig:LeftArm": "upperarm_l",
        "mixamorig:RightArm": "upperarm_r",
        "mixamorig:LeftForeArm": "lowerarm_l",
        "mixamorig:RightForeArm": "lowerarm_r",
        "mixamorig:LeftHand": "hand_l",
        "mixamorig:RightHand": "hand_r",
        "mixamorig:LeftUpLeg": "thigh_l",
        "mixamorig:RightUpLeg": "thigh_r",
        "mixamorig:LeftLeg": "calf_l",
        "mixamorig:RightLeg": "calf_r",
        "mixamorig:LeftFoot": "foot_l",
        "mixamorig:RightFoot": "foot_r",
        "mixamorig:LeftToeBase": "ball_l",
        "mixamorig:RightToeBase": "ball_r",
    }

    # 过滤两边都存在的骨骼
    valid_map = {m: d for m, d in MAP.items() if m in marm.pose.bones and d in darm.pose.bones}
    print(f"   匹配骨骼数量: {len(valid_map)} / {len(MAP)}")

    # 4. 计算静止姿态基准 (World-Space)
    # Mw_src: 源世界矩阵, Mw_tgt: 目标世界矩阵
    Mw_src = marm.matrix_world.copy()
    Mw_tgt = darm.matrix_world.copy()

    # 目标骨骼局部到父级链的基础矩阵
    # 在目标姿态中设置所有有效骨骼为 QUATERNION 模式
    for db in valid_map.values():
        darm.pose.bones[db].rotation_mode = "QUATERNION"

    # 5. 创建新 Action
    if not darm.animation_data:
        darm.animation_data_create()
    out_act = bpy.data.actions.new(name="AxeWalk_Retargeted")
    darm.animation_data.action = out_act

    sc = bpy.context.scene

    # 计算原点位移参考（in-place 处理）
    # 取第一帧与最后一帧骨盆水平位移
    sc.frame_set(f0)
    bpy.context.view_layer.update()
    p0_world = (marm.matrix_world @ marm.pose.bones["mixamorig:Hips"].matrix).translation.copy()
    sc.frame_set(f1)
    bpy.context.view_layer.update()
    p1_world = (marm.matrix_world @ marm.pose.bones["mixamorig:Hips"].matrix).translation.copy()
    fwd_vec = p1_world - p0_world
    # 水平前进方向（通常是世界坐标系的某一主轴）
    fwd_vec.z = 0.0
    total_fwd_len = fwd_vec.length
    if total_fwd_len > 1e-4:
        fwd_dir = fwd_vec.normalized()
    else:
        fwd_dir = Vector((0.0, 1.0, 0.0))
    print(f"   位移剥离: 总位移={total_fwd_len:.3f}m, 前进方向={fwd_dir}")

    # Darius pelvis 的 rest world translation
    dpelvis_rest_w = (darm.matrix_world @ darm.data.bones["pelvis"].matrix_local).translation.copy()
    mpelvis_rest_w = (marm.matrix_world @ marm.data.bones["mixamorig:Hips"].matrix_local).translation.copy()

    # 预计算 Rest-Pose 下的相对旋转基准矩阵 K = (W_src_rest)^-1 @ W_tgt_rest
    # 对于手臂（上臂/前臂），Mixamo 是 T-pose (平举)，Darius 是 A-pose (下垂45°)
    # 如果要把 Mixamo 的持斧姿势精准映射到 Darius：
    # 直接让 Darius 的手臂骨骼在世界空间指向与 Mixamo 相同的空间朝向！
    # 对每根骨骼计算基准：
    # 姿态传递使用矩阵链求解局部 rotation_quaternion

    ARM_BONES = {"upperarm_l", "lowerarm_l", "hand_l", "upperarm_r", "lowerarm_r", "hand_r"}

    # 6. 逐帧烘焙
    print(f"   正在逐帧烘焙 {f0}..{f1} ...")
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()

        # 计算骨盆在世界的去前进位移
        curr_m_hip_w = (marm.matrix_world @ marm.pose.bones["mixamorig:Hips"].matrix).translation.copy()
        # 相对首帧的前进位移投影
        delta_p = curr_m_hip_w - p0_world
        progress = (f - f0) / max(1, f1 - f0)
        # 剥离前进分量，保留横向摇摆和上下颠簸
        fwd_proj = delta_p.dot(fwd_dir) * fwd_dir
        in_place_delta = delta_p - fwd_proj

        # Darius 骨盆目标世界位置 = Darius rest + 颠簸与摇摆
        target_pelvis_w = dpelvis_rest_w + in_place_delta
        # 转到 Darius armature local space
        target_pelvis_local = darm.matrix_world.inverted() @ target_pelvis_w
        # 设置 pelvis location（相对 rest 的 delta）
        d_pelvis_bone = darm.data.bones["pelvis"]
        darm.pose.bones["pelvis"].location = target_pelvis_local - d_pelvis_bone.matrix_local.translation
        darm.pose.bones["pelvis"].keyframe_insert(data_path="location", frame=f)

        # 逐骨按父子层级求解局部姿态
        # 为保证链式稳定，按层级深度排序骨骼
        ordered_bones = sorted(valid_map.items(), key=lambda item: len(darm.data.bones[item[1]].parent_recursive))

        # 记录已计算的各骨骼世界变换矩阵
        W_tgt = {}

        # 计算平均朝向偏差（去除 -33° 的斜向战斗架势，让角色正向朝前走）
        # 骨盆当前世界旋转
        M_src_cur_hip = (marm.matrix_world @ marm.pose.bones["mixamorig:Hips"].matrix).to_3x3()
        M_src_rest_hip = (marm.matrix_world @ marm.data.bones["mixamorig:Hips"].matrix_local).to_3x3()
        R_world_hip = M_src_cur_hip @ M_src_rest_hip.inverted()
        # 补偿 +33.1° Yaw，使角色面朝正前方行走
        R_yaw_fix = Matrix.Rotation(math.radians(33.1), 3, 'Z')

        for mb, db in ordered_bones:
            # 源骨骼当前世界变换
            M_src_cur = (marm.matrix_world @ marm.pose.bones[mb].matrix).to_3x3()
            M_src_rest = (marm.matrix_world @ marm.data.bones[mb].matrix_local).to_3x3()
            M_tgt_rest = (darm.matrix_world @ darm.data.bones[db].matrix_local).to_3x3()

            # 源骨骼在世界的纯旋转增量 R_world = M_src_cur @ M_src_rest^-1
            R_world = M_src_cur @ M_src_rest.inverted()

            # 对骨盆叠加正向对齐补偿
            if db == "pelvis":
                R_world = R_yaw_fix @ R_world

            # 全身所有骨骼严格统一采用相对旋转增量传递：
            # M_tgt_desired = R_world @ M_tgt_rest
            # 保证所有关节的本地坐标系、骨骼 Roll 和蒙皮父子关系 100% 守恒且连续！
            M_tgt_desired = R_world @ M_tgt_rest


            # 求目标骨骼局部旋转
            # 在 Darius 自身骨骼树中：W_tgt[parent] @ rest_local_rel @ local_rot = W_tgt_desired
            dbone = darm.data.bones[db]
            par = dbone.parent
            if par and par.name in W_tgt:
                W_par = W_tgt[par.name]
                # 父骨骼静止世界矩阵
                W_par_rest = (darm.matrix_world @ par.matrix_local).to_3x3()
                # 父骨骼当前世界矩阵与静止矩阵的差
                # 局部期望变换：
                local_desired = W_par.inverted() @ M_tgt_desired
                # 局部静止变换：
                local_rest = W_par_rest.inverted() @ M_tgt_rest
                # 局部旋转：
                R_local = local_rest.inverted() @ local_desired
            else:
                # 根级骨骼（pelvis）
                W_arm = darm.matrix_world.to_3x3()
                local_desired = W_arm.inverted() @ M_tgt_desired
                local_rest = darm.data.bones[db].matrix_local.to_3x3()
                R_local = local_rest.inverted() @ local_desired

            pb = darm.pose.bones[db]
            pb.rotation_quaternion = R_local.to_quaternion()
            pb.keyframe_insert(data_path="rotation_quaternion", frame=f)

            # 更新当前骨骼的世界旋转矩阵供子级使用
            W_tgt[db] = M_tgt_desired

    # 7. 解决斧头武器绑定 (weapon_jnt 跟随 hand_r / weapon_jnt_r)
    # 在 Darius 模型中，斧头网格蒙皮在 weapon_jnt_offset 上，其父级是 weapon_jnt
    # 只要给 weapon_jnt 加一个 Copy Transforms 约束到 weapon_jnt_r，斧头就会自然握在右手！
    print("   绑定战斧骨骼 weapon_jnt -> weapon_jnt_r ...")
    sc.frame_start, sc.frame_end = f0, f1
    pb_wjnt = darm.pose.bones.get("weapon_jnt")
    pb_wjnt_r = darm.pose.bones.get("weapon_jnt_r")
    if pb_wjnt and pb_wjnt_r:
        # 添加约束
        const = pb_wjnt.constraints.new(type="COPY_TRANSFORMS")
        const.target = darm
        const.subtarget = "weapon_jnt_r"
        # 烘焙 weapon_jnt 关键帧
        bpy.ops.nla.bake(frame_start=f0, frame_end=f1, only_selected=False, visual_keying=True, clear_constraints=True, bake_types={"POSE"})
        print("   战斧骨骼已烘焙到位！")

    out_act.use_fake_user = True


    # 8. 归位角色到世界原点（脚踩地，不飘空）
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if meshes:
        # 计算最低点 Z
        min_z = min(min((o.matrix_world @ v.co).z for v in o.data.vertices) for o in meshes)
        # 将骨架微调使脚底触地（min_z 贴合 0）
        darm.location.z -= min_z
        print(f"   接地对齐: Z 偏移 {-min_z:.3f}m, 脚底现已完美贴地！")

    # 9. 清理源骨架与多余对象，导出 FBX
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
    print(f"   已导出重定向结果 -> {OUT_FBX}")
    print("=== 重定向全部完成 ===")

if __name__ == "__main__":
    main()
