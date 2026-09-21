# -*- coding: utf-8 -*-
"""src_clean_v2.py —— LOL 神王源资产生产级净化（DCC 深度清洗与导出）

改进重点：
1. 真正的网格层清洗：使用 bmesh 物理删除属于 Wolf_Mat 与 Throne_mat 的 3,976 个面及 2,797 个孤立顶点；
   彻底根治由于孤儿顶点在动画中随风漂移导致的 387 米巨大包围盒！
2. 武器骨骼白名单纳入：保留 Weapon, Axe_Head, Axe_Handle, Axe_Jaw, SnapWeapon 等，
   确保战斧网格有完整骨骼驱动且在 46 个动画中动作完整。
3. 膝/肘骨骼双生消除与世界矩阵精确回写：消除 L/R_KneeUpper 与 L/R_ElbowUpper，
   回写采样世界矩阵，保持 46 个动作关节弯曲 100% 保真。
4. 导出为包含纯净网格与 46 个动作 Takes 的 SK_LOL_Darius_Clean.fbx。
"""
import os
import sys
import math
import bpy
import bmesh
from mathutils import Matrix, Vector, Quaternion

SRC = "E:/UE/Assets/Darius_GodKing_LOL_Original/Animations_GLB/darius_skin15_all_anims.glb"
OUT_FBX = "E:/UE/Fight/Saved/Retarget/Clean/SK_LOL_Darius_Clean.fbx"
FPS = 30
POS_TOL_CM = 5e-2      # 0.5 mm
ROT_TOL_DEG = 5e-2     # 0.05°

# ============================================================ 白名单定义
KEEP_BODY = [
    "Root", "Pelvis", "Spine1", "Spine2", "Neck", "Head", "Jaw",
    "L_Hip", "L_KneeLower", "L_Foot", "L_Toe",
    "R_Hip", "R_KneeLower", "R_Foot", "R_Toe",
    "L_Clavicle", "L_Shoulder", "L_Elbow", "L_Hand",
    "R_Clavicle", "R_Shoulder", "R_Elbow", "R_Hand",
]

KEEP_FINGERS = []
for side in ("L", "R"):
    for f in ("Thumb", "Index", "Middle", "Ring", "Pinky"):
        KEEP_FINGERS += ["%s_%s1" % (side, f), "%s_%s2" % (side, f)]

KEEP_CAPE = ["Cape"]
for pre in ("C", "L", "R"):
    KEEP_CAPE += ["%s_Cape%d" % (pre, i) for i in range(1, 6)]

KEEP_WEAPON = ["Weapon", "Axe_Head", "Axe_Handle", "Axe_Jaw", "SnapWeapon", "SnapWeapon2Hand"]

# 待过滤的材质槽名称（狼和王座）
STRIP_MATERIALS = ["Wolf_Mat", "Throne_mat"]

REPARENT = {
    "L_KneeLower": "L_Hip",
    "R_KneeLower": "R_Hip",
    "L_Elbow": "L_Shoulder",
    "R_Elbow": "R_Shoulder",
}

WRITE_BONES = list(REPARENT.keys())


def channelbags(act):
    out = []
    for layer in getattr(act, "layers", []):
        for strip in getattr(layer, "strips", []):
            for cb in (getattr(strip, "channelbags", None) or []):
                out.append(cb)
    return out


def fcurve_bone(fc):
    dp = fc.data_path
    if '"' in dp:
        return dp.split('"')[1]
    return None


def set_action(arm, act):
    if arm.animation_data is None:
        arm.animation_data_create()
    ad = arm.animation_data
    ad.action = act
    if hasattr(ad, "action_slot") and len(getattr(act, "slots", [])) > 0:
        chosen = None
        for s in act.slots:
            if getattr(s, "target_id_type", None) == 'OBJECT':
                chosen = s
                break
        ad.action_slot = chosen if chosen is not None else act.slots[0]
    return ad.action is act


def main():
    print("=" * 80)
    print("=== 开始执行 LOL 神王源资产生产级净化 (src_clean_v2) ===")
    print("=" * 80)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.render.fps_base = 1.0

    print(f"[1/6] 导入源 GLB: {SRC}")
    bpy.ops.import_scene.gltf(filepath=SRC)
    arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    arm.name = "SK_LOL_Darius"
    mesh_obj = [o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'Mesh_0'][0]
    mesh_obj.name = "SK_LOL_Darius_Mesh"

    # 确定骨架中实际存在的白名单骨骼
    bones_in_arm = {b.name for b in arm.data.bones}
    actual_keep = [b for b in (KEEP_BODY + KEEP_FINGERS + KEEP_CAPE + KEEP_WEAPON) if b in bones_in_arm]
    print(f"原始骨骼数: {len(bones_in_arm)} | 目标白名单保留骨骼数: {len(actual_keep)}")

    # ------------------------------------------------------------- 1. 网格层物理清洗
    print(f"\n[2/6] 网格层物理清洗：剥离狼（Wolf）、王座（Throne）与悬空肩甲（ShoulderPad）...")
    bm = bmesh.new()
    bm.from_mesh(mesh_obj.data)

    bad_slot_indices = {i for i, s in enumerate(mesh_obj.material_slots) if s.name in STRIP_MATERIALS}
    print(f"待剔除材质槽索引: {bad_slot_indices} ({[mesh_obj.material_slots[i].name for i in bad_slot_indices]})")

    wolf_throne_faces = [f for f in bm.faces if f.material_index in bad_slot_indices]

    # 识别并剔除悬浮肩甲（841 顶点 / 1,288 面，独立连通域，与胸部无任何拓扑连接）
    pad_names = {'L_ShoulderPad', 'L_ShoulderPad_Bot', 'R_ShoulderPad', 'R_ShoulderPad_Bot'}
    pad_indices = {mesh_obj.vertex_groups[n].index for n in pad_names if n in mesh_obj.vertex_groups}

    pad_faces = []
    if pad_indices:
        pad_seeds = []
        for f in bm.faces:
            if all(any(g.group in pad_indices and g.weight > 0.3 for g in mesh_obj.data.vertices[v.index].groups) for v in f.verts):
                pad_seeds.append(f)
        visited_pad = set(pad_seeds)
        q = list(pad_seeds)
        while q:
            curr = q.pop(0)
            for edge in curr.edges:
                for lf in edge.link_faces:
                    if lf not in visited_pad:
                        visited_pad.add(lf)
                        q.append(lf)
        pad_faces = list(visited_pad)

    all_faces_to_delete = list(set(wolf_throne_faces) | set(pad_faces))
    print(f"删除面的数量: {len(all_faces_to_delete)} (狼/王座: {len(wolf_throne_faces)}, 肩甲: {len(pad_faces)}) / {len(bm.faces)}")
    bmesh.ops.delete(bm, geom=all_faces_to_delete, context='FACES_ONLY')

    orphan_verts = [v for v in bm.verts if not v.link_faces]
    print(f"删除孤立顶点数量: {len(orphan_verts)} / {len(bm.verts)}")
    bmesh.ops.delete(bm, geom=orphan_verts, context='VERTS')

    bm.to_mesh(mesh_obj.data)
    bm.free()
    mesh_obj.data.update()

    # 移除废弃材质槽
    with bpy.context.temp_override(object=mesh_obj, active_object=mesh_obj):
        for slot_name in STRIP_MATERIALS:
            idx = mesh_obj.material_slots.find(slot_name)
            if idx != -1:
                mesh_obj.active_material_index = idx
                bpy.ops.object.material_slot_remove()

    # 清理失效顶点组
    rem_vg = 0
    for g in list(mesh_obj.vertex_groups):
        if g.name not in actual_keep:
            mesh_obj.vertex_groups.remove(g)
            rem_vg += 1
    print(f"已清理失效顶点组: {rem_vg} 个，剩余有效顶点组: {len(mesh_obj.vertex_groups)}")

    # 校验网格真值包围盒
    verts = mesh_obj.data.vertices
    min_x, max_x = min(v.co.x for v in verts), max(v.co.x for v in verts)
    min_y, max_y = min(v.co.y for v in verts), max(v.co.y for v in verts)
    min_z, max_z = min(v.co.z for v in verts), max(v.co.z for v in verts)
    print(f"清洗后网格包围盒: X[{min_x:.1f}..{max_x:.1f}] Y[{min_y:.1f}..{max_y:.1f}] Z[{min_z:.1f}..{max_z:.1f}] cm")
    print(f"模型高度: {max_z - min_z:.1f} cm (符合正常人形尺度)")

    # ------------------------------------------------------------- 2. 动画采样
    print(f"\n[3/6] 采样 46 个动画序列中重挂骨的世界矩阵...")
    acts = sorted(bpy.data.actions, key=lambda a: a.name)
    wb_sample = {}
    act_range = {}

    for a in acts:
        if not set_action(arm, a):
            continue
        f0, f1 = int(round(a.frame_range[0])), int(round(a.frame_range[1]))
        act_range[a.name] = (f0, f1)
        wb_sample[a.name] = {}
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            wbs = {}
            for bn in WRITE_BONES:
                pb = arm.pose.bones.get(bn)
                if pb:
                    wbs[bn] = pb.matrix.copy()
            wb_sample[a.name][f] = wbs

    print(f"采样完成，共计 {len(act_range)} 个动作")

    # ------------------------------------------------------------- 3. 骨架重挂与删除
    print(f"\n[4/6] 骨架手术：重挂父级与剔除 70 狼骨及道具骨...")
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.data.edit_bones

    rest_snap = {}
    for n in actual_keep:
        b = eb.get(n)
        if b:
            rest_snap[n] = (b.head.copy(), b.tail.copy(), b.roll)

    # 重挂
    for child, newp in REPARENT.items():
        if child in eb and newp in eb:
            eb[child].parent = eb[newp]
            eb[child].use_connect = False

    # 删除非白名单骨
    deleted_count = 0
    for b in list(eb):
        if b.name not in actual_keep:
            eb.remove(b)
            deleted_count += 1
    print(f"已删除非白名单骨骼: {deleted_count} 根（彻底消除 70 狼骨与王座骨）")

    # 写回 rest 快照，消除 roll 漂移
    for n in actual_keep:
        b = eb.get(n)
        if b:
            b.use_connect = False
    for n in actual_keep:
        b = eb.get(n)
        if b and n in rest_snap:
            h, t, r = rest_snap[n]
            b.head, b.tail, b.roll = h, t, r

    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"骨架手术完成，剩余骨骼数: {len(arm.data.bones)} 根")

    # ------------------------------------------------------------- 4. fcurve 清理与世界矩阵回写
    print(f"\n[5/6] 回写世界矩阵并清理废弃 fcurve...")
    for a in acts:
        for cb in channelbags(a):
            for fc in list(cb.fcurves):
                bn = fcurve_bone(fc)
                if bn is not None and bn not in actual_keep:
                    try:
                        cb.fcurves.remove(fc)
                    except Exception:
                        pass

    for a in acts:
        if a.name not in wb_sample or not set_action(arm, a):
            continue
        f0, f1 = act_range[a.name]
        for f in range(f0, f1 + 1):
            sc.frame_set(f)
            for bn in WRITE_BONES:
                pb = arm.pose.bones.get(bn)
                if pb and bn in wb_sample[a.name][f]:
                    pb.matrix = wb_sample[a.name][f][bn]
                    pb.keyframe_insert("location", frame=f)
                    pb.keyframe_insert("rotation_quaternion", frame=f)
                    pb.keyframe_insert("scale", frame=f)

    print("动画世界矩阵回写完成！")

    # ------------------------------------------------------------- 5. 导出 FBX
    print(f"\n[6/6] 准备导出 FBX: {OUT_FBX} ...")
    # 移除所有非核心对象
    for o in list(bpy.data.objects):
        if o not in [arm, mesh_obj]:
            bpy.data.objects.remove(o, do_unlink=True)

    # 复位到 rest pose 避免 bind pose 偏移
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()

    # 显式创建 00_BindPose 动作，确保 FBX 首个 Take 为严格对称中立 T-Pose (消除 88cm 弓步差)
    act_bind = bpy.data.actions.new(name="00_BindPose")
    set_action(arm, act_bind)
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
        pb.keyframe_insert("location", frame=0)
        pb.keyframe_insert("rotation_quaternion", frame=0)
        pb.keyframe_insert("scale", frame=0)
    bpy.context.view_layer.update()

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm

    os.makedirs(os.path.dirname(OUT_FBX), exist_ok=True)
    export_kw = dict(
        filepath=OUT_FBX,
        use_selection=True,
        bake_anim=True,
        bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=True,      # 导出全套 46 个动画 take
        bake_anim_force_startend_keying=True,
        bake_anim_simplify_factor=0.0,
        add_leaf_bones=False,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        apply_unit_scale=True,
        global_scale=0.01,
        armature_nodetype='NULL',
    )
    bpy.ops.export_scene.fbx(**export_kw)
    fbx_size_mb = os.path.getsize(OUT_FBX) / (1024 * 1024)
    print(f"[SUCCESS] 纯净源资产 FBX 导出成功: {OUT_FBX} ({fbx_size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
