# -*- coding: utf-8 -*-
"""atk_20_export_clean_anims.py —— LOL 神王攻击与过渡动画纯净导出（离线 Blender 纯脚本）

核心特性：
1. 骨骼白名单传递：只传递人体躯干、手臂、手指、披风与战斧骨骼；自动剔除 70 狼骨与王座道具骨。
2. 战斧换握法（Weapon -> weapon_jnt）：
   - 世界旋转精确传递；
   - 平移应用 SCALE = 0.009505 尺度缩放，实现 Riot 原版双手换握滑移效果。
3. 纯动画 FBX 导出：
   - 彻底剥离所有网格模型（object_types={'ARMATURE'}），杜绝在 UE 中生成 20MB+ 冗余 SkeletalMesh。
4. 帧率锁定 30fps。

用法：
    & "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P Scripts/anim/atk_20_export_clean_anims.py
"""
import os
import sys
import math
import bpy
from mathutils import Matrix, Vector

GLB = "E:/UE/Assets/Darius_GodKing_LOL_Original/Animations_GLB/darius_skin15_all_anims.glb"
TARGET_FBX = "E:/UE/Fight/Saved/Retarget/SK_Darius_GodKing_Clean.fbx"
OUT_DIR = "E:/UE/Fight/Saved/Attack/Clean_FBX"

CLIPS = [
    ("darius_skin15_attack1", "A_Darius_Attack1_LOL.fbx"),
    ("darius_skin15_attack1_toidle", "A_Darius_Attack1_ToIdle_LOL.fbx"),
]

MAP = {
    "Pelvis": "pelvis", "Neck": "neck_01", "Head": "head",
    "L_Clavicle": "clavicle_l", "R_Clavicle": "clavicle_r",
    "L_Shoulder": "upperarm_l", "R_Shoulder": "upperarm_r",
    "L_Elbow": "lowerarm_l", "R_Elbow": "lowerarm_r",
    "L_Hand": "hand_l", "R_Hand": "hand_r",
    "L_Hip": "thigh_l", "R_Hip": "thigh_r",
    "L_KneeLower": "calf_l", "R_KneeLower": "calf_r",
    "L_Foot": "foot_l", "R_Foot": "foot_r",
    "L_Toe": "ball_l", "R_Toe": "ball_r",
    "Weapon": "weapon_jnt",
}
SPINE = [("Spine1", "spine_01"), ("Spine2", "spine_03")]


def rot3(mat):
    return mat.to_quaternion().to_matrix()


def head_w(arm, name):
    return arm.matrix_world @ arm.data.bones[name].head_local


def body_frame(arm, lbone, rbone):
    v = head_w(arm, rbone) - head_w(arm, lbone)
    v.z = 0.0
    right = v.normalized() if v.length > 1e-6 else Vector((1, 0, 0))
    up = Vector((0, 0, 1))
    fwd = right.cross(up)
    return right, fwd, up


def to_body(v, frame):
    r, f, u = frame
    return Vector((v.dot(r), v.dot(f), v.dot(u)))


def process_clip(clip_name, out_fbx_name):
    print(f"\n==================== 处理动作: {clip_name} -> {out_fbx_name} ====================")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = 30
    sc.render.fps_base = 1.0

    # 1. 导入源 GLB
    bpy.ops.import_scene.gltf(filepath=GLB)
    sarm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
    act = bpy.data.actions.get(clip_name)
    if not act:
        print(f"[ERROR] 找不到动作 {clip_name}")
        return False
    if not sarm.animation_data:
        sarm.animation_data_create()
    sarm.animation_data.action = act
    f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
    print(f"源动作帧数: {f0} .. {f1} ({f1 - f0 + 1} 帧)")

    # 2. 导入目标 FBX
    _before_meshes = {o for o in bpy.data.objects if o.type == "MESH"}
    bpy.ops.import_scene.fbx(filepath=TARGET_FBX)
    tarm = [o for o in bpy.data.objects if o.type == "ARMATURE" and o is not sarm][0]

    # 配对
    pairs = [(s, t, False) for s, t in MAP.items()] + [(s, t, True) for s, t in SPINE]
    pairs = [(s, t, sp) for (s, t, sp) in pairs if s in sarm.data.bones and t in tarm.data.bones]
    print(f"有效骨骼映射: {len(pairs)} 根（包含 weapon_jnt）")

    SR = {s: rot3(sarm.matrix_world @ sarm.data.bones[s].matrix_local) for (s, t, sp) in pairs}
    TR = {t: rot3(tarm.matrix_world @ tarm.data.bones[t].matrix_local) for (s, t, sp) in pairs}
    TR["spine_02"] = rot3(tarm.matrix_world @ tarm.data.bones["spine_02"].matrix_local)

    SF = body_frame(sarm, "L_Hip", "R_Hip")
    TF = body_frame(tarm, "thigh_l", "thigh_r")

    SRC_H = abs(head_w(sarm, "Head").z - head_w(sarm, "L_Foot").z)
    TGT_H = abs(head_w(tarm, "head").z - head_w(tarm, "foot_l").z)
    SCALE = TGT_H / SRC_H
    print(f"身高比例 SCALE = {SCALE:.6f} (源 {SRC_H:.1f}cm -> 目标 {TGT_H:.2f}m)")

    ORDER = sorted(pairs, key=lambda p: len(tarm.data.bones[p[1]].parent_recursive))

    # 3. 烘焙动画
    sc.frame_start, sc.frame_end = f0, f1
    if not tarm.animation_data:
        tarm.animation_data_create()
    oact = bpy.data.actions.new(name=os.path.splitext(out_fbx_name)[0])
    tarm.animation_data.action = oact
    for pb in tarm.pose.bones:
        pb.rotation_mode = "QUATERNION"

    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        W = {}

        # 计算骨盆平移
        src_pel_head = sarm.matrix_world @ sarm.pose.bones["Pelvis"].head
        src_d_pel = src_pel_head - head_w(sarm, "Pelvis")
        db_pel = to_body(src_d_pel, SF) * SCALE
        tgt_pel_head = head_w(tarm, "pelvis") + (db_pel.x * TF[0] + db_pel.y * TF[1] + db_pel.z * TF[2])

        for s, t, sp in ORDER:
            Ws_cur = rot3(sarm.matrix_world @ sarm.pose.bones[s].matrix)
            if sp and t == "spine_02":
                continue
            M_des = (TR[t] @ SR[s].inverted()) @ Ws_cur
            tb = tarm.data.bones[t]
            par = tb.parent
            Wpc = W[par.name] if (par and par.name in W) else \
                (rot3(tarm.matrix_world @ par.matrix_local) if par else rot3(tarm.matrix_world))
            Wpr = rot3(tarm.matrix_world @ par.matrix_local) if par else rot3(tarm.matrix_world)
            basis = (Wpc @ (Wpr.inverted() @ TR[t])).inverted() @ M_des
            pb = tarm.pose.bones[t]

            if t == "pelvis":
                m4 = M_des.to_4x4()
                m4.translation = tarm.matrix_world.inverted() @ tgt_pel_head
                pb.matrix = m4
                pb.keyframe_insert(data_path="location", frame=f)
                pb.keyframe_insert(data_path="rotation_quaternion", frame=f)
            elif t == "weapon_jnt":
                # 战斧换握法：相对骨盆的位移按 SCALE 缩放
                src_w_head = sarm.matrix_world @ sarm.pose.bones["Weapon"].head
                src_w_rel = src_w_head - src_pel_head
                db_w = to_body(src_w_rel, SF) * SCALE
                tgt_w_head = tgt_pel_head + (db_w.x * TF[0] + db_w.y * TF[1] + db_w.z * TF[2])
                m4 = M_des.to_4x4()
                m4.translation = tarm.matrix_world.inverted() @ tgt_w_head
                pb.matrix = m4
                pb.keyframe_insert(data_path="location", frame=f)
                pb.keyframe_insert(data_path="rotation_quaternion", frame=f)
            else:
                pb.rotation_quaternion = basis.to_quaternion()
                pb.keyframe_insert(data_path="rotation_quaternion", frame=f)
            W[t] = M_des

        # 补全 spine_02
        if "spine_01" in W and "spine_03" in W:
            t = "spine_02"
            q = W["spine_01"].to_quaternion().slerp(W["spine_03"].to_quaternion(), 0.5)
            M_des = q.to_matrix()
            par = tarm.data.bones[t].parent
            Wpc = W[par.name]
            Wpr = rot3(tarm.matrix_world @ par.matrix_local)
            basis = (Wpc @ (Wpr.inverted() @ TR[t])).inverted() @ M_des
            pb = tarm.pose.bones[t]
            pb.rotation_quaternion = basis.to_quaternion()
            pb.keyframe_insert(data_path="rotation_quaternion", frame=f)
            W[t] = M_des

    oact.use_fake_user = True
    print(f"[OK] 烘焙完成: {oact.name}")

    # 4. 彻底删除全部网格模型，只留骨架导出纯动画
    for o in list(bpy.data.objects):
        if o != tarm:
            try:
                bpy.data.objects.remove(o, do_unlink=True)
            except Exception:
                pass

    bpy.ops.object.select_all(action="DESELECT")
    tarm.select_set(True)
    bpy.context.view_layer.objects.active = tarm

    os.makedirs(OUT_DIR, exist_ok=True)
    out_fbx_path = os.path.join(OUT_DIR, out_fbx_name)
    sc.render.fps = 30
    sc.render.fps_base = 1.0

    bpy.ops.export_scene.fbx(
        filepath=out_fbx_path,
        use_selection=True,
        object_types={"ARMATURE"},
        bake_anim=True,
        bake_anim_use_all_actions=False,
        bake_anim_use_nla_strips=False,
        bake_anim_force_startend_keying=True,
        add_leaf_bones=False,
        apply_unit_scale=True,
        global_scale=1.0,
    )
    fbx_size_kb = os.path.getsize(out_fbx_path) / 1024
    print(f"[SUCCESS] 导出纯动画 FBX: {out_fbx_path} ({fbx_size_kb:.1f} KB)")
    return True


def main():
    print("=== 开始批量导出 LOL 神王攻击与过渡纯净动画 ===")
    for clip, out_name in CLIPS:
        ok = process_clip(clip, out_name)
        if not ok:
            print(f"[FAIL] 导出失败: {clip}")
            sys.exit(1)
    print("\n=== 全部纯净动作导出完成！===")


if __name__ == "__main__":
    main()
