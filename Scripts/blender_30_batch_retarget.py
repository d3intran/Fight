"""
批量重定向：从 all_anims.glb 中挑出 locomotion 动画集，逐个重定向到 2XKO 骨架并导出
用法: blender -b -P blender_30_batch_retarget.py -- <SRC_GLB> <TGT_FBX> <OUTDIR> <spine_pitch> [anim1,anim2,...] [--list]
"""
import bpy, sys, os, math
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC_GLB, TGT_FBX, OUTDIR = argv[0], argv[1], argv[2]
SPINE_PITCH = float(argv[3]) if len(argv) > 3 else 12.0
WANT = []
LIST_ONLY = "--list" in argv
for a in argv[4:]:
    if a == "--list":
        continue
    WANT.extend(a.split(","))
os.makedirs(OUTDIR, exist_ok=True)

BONE_MAP = [
    ("Root", "root"), ("Pelvis", "pelvis"), ("Spine1", "spine_01"), ("Spine2", "spine_02"),
    ("Neck", "neck_01"), ("Head", "head"),
    ("L_Clavicle", "clavicle_l"), ("L_Shoulder", "upperarm_l"), ("L_Elbow", "lowerarm_l"), ("L_Hand", "hand_l"),
    ("R_Clavicle", "clavicle_r"), ("R_Shoulder", "upperarm_r"), ("R_Elbow", "lowerarm_r"), ("R_Hand", "hand_r"),
    ("L_Hip", "thigh_l"), ("L_KneeLower", "calf_l"), ("L_Foot", "foot_l"), ("L_Toe", "toe_l"),
    ("R_Hip", "thigh_r"), ("R_KneeLower", "calf_r"), ("R_Foot", "foot_r"), ("R_Toe", "toe_r"),
]
SPINE_CHAIN = {"spine_01": 0.45, "spine_02": 0.35, "spine_03": 0.20}
NECK_CHAIN = {"neck_01": -0.6}

def import_new(path, kind):
    before = set(bpy.data.objects)
    if kind == "fbx":
        bpy.ops.import_scene.fbx(filepath=path, automatic_bone_orientation=True)
    else:
        bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    return [o for o in new if o.type == 'ARMATURE'][0], [o for o in new if o.type == 'MESH']

bpy.ops.wm.read_factory_settings(use_empty=True)
# 关键：场景帧率设为 30，保证导出的 FBX 时长落在 30fps 帧边界上，
# 否则 UE Interchange 会报 "Animation length ... is not compatible with import frame-rate 30 fps" 并拒绝导入
bpy.context.scene.render.fps = 30
bpy.context.scene.render.fps_base = 1.0
tgt_arm, tgt_meshes = import_new(TGT_FBX, "fbx")
print("target:", tgt_arm.name, len(tgt_arm.data.bones))
src_arm, src_meshes = import_new(SRC_GLB, "glb")
print("source:", src_arm.name, len(src_arm.data.bones))

acts = [a for a in bpy.data.actions]
names = sorted(set(a.name for a in acts))
print(f"源动作总数 {len(names)}:")
for n in names:
    print("   ", n)
if LIST_ONLY:
    print("=== LIST DONE ===")
    raise SystemExit

sc = bpy.context.scene

# ---- 空间对齐 ----
def rest_basis(arm, l, r):
    L = arm.matrix_world @ arm.data.bones[l].head_local
    R = arm.matrix_world @ arm.data.bones[r].head_local
    rt = (R - L); rt.z = 0.0
    if rt.length < 1e-6: rt = Vector((1, 0, 0))
    rt.normalize()
    up = Vector((0, 0, 1))
    return Matrix((rt, up.cross(rt), up)).transposed()

Q = rest_basis(tgt_arm, "thigh_l", "thigh_r") @ rest_basis(src_arm, "L_Hip", "R_Hip").inverted()
Q_inv = Q.inverted()
print("Q (deg about Z):", round(math.degrees(Q.to_euler().z), 2))

def head_z(arm, n):
    b = arm.data.bones.get(n)
    return (arm.matrix_world @ b.head_local).z if b else None

src_h = head_z(src_arm, "Head"); tgt_h = head_z(tgt_arm, "head")
src_f = min(v for v in [head_z(src_arm, "L_Toe"), head_z(src_arm, "R_Toe")] if v is not None)
tgt_f = min(v for v in [head_z(tgt_arm, "toe_l"), head_z(tgt_arm, "toe_r")] if v is not None)
SCALE = (tgt_h - tgt_f) / max(1e-6, (src_h - src_f))
print("SCALE:", round(SCALE, 6))

src_bones = [s for s, _ in BONE_MAP]
src_rest_rot = {s: src_arm.data.bones[s].matrix_local.to_3x3() for s in src_bones if src_arm.data.bones.get(s)}
tgt_rest_rot = {t: tgt_arm.data.bones[t].matrix_local.to_3x3() for _, t in BONE_MAP if tgt_arm.data.bones.get(t)}
src_root_rest_head = (src_arm.matrix_world @ src_arm.data.bones["Root"].head_local).copy()

order = []
def _walk(b):
    order.append(b.name)
    for c in b.children: _walk(c)
for b in tgt_arm.data.bones:
    if b.parent is None: _walk(b)
rest_rel_all = {}
for b in tgt_arm.data.bones:
    rest_rel_all[b.name] = (b.matrix_local.to_3x3() if b.parent is None
                            else b.parent.matrix_local.to_3x3().inverted() @ b.matrix_local.to_3x3())
map_tgt = {t: s for s, t in BONE_MAP}
pitch_mats = {n: Matrix.Rotation(math.radians(SPINE_PITCH) * w, 3, 'X')
              for n, w in list(SPINE_CHAIN.items()) + list(NECK_CHAIN.items())}

for pb in tgt_arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'

def iter_fcurves(a):
    try:
        return list(a.fcurves)
    except AttributeError:
        out = []
        for layer in getattr(a, "layers", []):
            for strip in getattr(layer, "strips", []):
                for cb in getattr(strip, "channelbags", []):
                    out.extend(cb.fcurves)
        return out

results = []
for want in WANT:
    act = None
    for a in bpy.data.actions:
        if a.name == want or a.name.endswith("_" + want) or a.name.endswith(want):
            act = a
            break
    if act is None:
        print(f"!! 找不到动作 {want}，跳过")
        continue
    src_arm.animation_data.action = act
    F0, F1 = int(act.frame_range[0]), int(act.frame_range[1])
    print(f"--- {want}: action={act.name} frames {F0}~{F1} ---")

    # 采样
    samples, root_delta = {}, {}
    for f in range(F0, F1 + 1):
        sc.frame_set(f); bpy.context.view_layer.update()
        samples[f] = {s: src_arm.pose.bones[s].matrix.to_3x3() for s in src_bones if src_arm.pose.bones.get(s)}
        rp = src_arm.pose.bones.get("Root")
        root_delta[f] = ((src_arm.matrix_world @ rp.matrix).translation - src_root_rest_head) * SCALE if rp else Vector((0, 0, 0))

    # 烘焙到目标
    if tgt_arm.animation_data is None:
        tgt_arm.animation_data_create()
    for pb in tgt_arm.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    new_act = bpy.data.actions.new("A_Darius_" + want.title().replace("_", "") + "_TP")
    tgt_arm.animation_data.action = new_act

    for f in range(F0, F1 + 1):
        final_rot = {}
        for name in order:
            bone = tgt_arm.data.bones[name]; pb = tgt_arm.pose.bones[name]
            parent = bone.parent
            Rp = final_rot[parent.name] if parent is not None else Matrix.Identity(3)
            rr = rest_rel_all[name]
            s_name = map_tgt.get(name)
            if s_name and samples[f].get(s_name) is not None:
                D = Q @ (samples[f][s_name] @ src_rest_rot[s_name].inverted()) @ Q_inv
                Wt = D @ tgt_rest_rot[name]
                if name in pitch_mats: Wt = pitch_mats[name] @ Wt
                final_rot[name] = Wt
                pb.rotation_quaternion = (rr.inverted() @ Rp.inverted() @ Wt).to_quaternion()
                if name == "root":
                    pb.location = tgt_rest_rot[name].inverted() @ root_delta[f]
            else:
                final_rot[name] = Rp @ rr
        for name in order:
            tgt_arm.pose.bones[name].keyframe_insert("rotation_quaternion", frame=f)
            if name == "root":
                tgt_arm.pose.bones[name].keyframe_insert("location", frame=f)
    for fc in iter_fcurves(new_act):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    print(f"    烘焙 {new_act.name} 曲线数 {len(iter_fcurves(new_act))}")
    results.append(new_act.name)

# 导出
# ⚠️⚠️ 关键修复（2026-09-18）：原先是「循环内挂 action 逐个导出」，那会让 Blender 把
#      「当前帧的 pose」写成骨架节点变换 ⇒ bind pose 完全错误。
# 实测（plan_17）：挂 action 导出 → 间距偏差 5.843e-02；清 pose + all_actions=True → 1.198e-07。
# 历史影响（plan_16）：本脚本产出的 Saved/Retarget/Batch/*.fbx 已全部 BROKEN（偏差最高 15.4%）。
if tgt_arm.animation_data:
    tgt_arm.animation_data.action = None
for _pb in tgt_arm.pose.bones:
    _pb.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()

bpy.ops.object.select_all(action='DESELECT')
tgt_arm.select_set(True); bpy.context.view_layer.objects.active = tgt_arm
out = os.path.join(OUTDIR, "A_Darius_All_TP.fbx").replace("\\", "/")
bpy.ops.export_scene.fbx(
    filepath=out, use_selection=True, bake_anim=True, bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=False, bake_anim_use_all_actions=True,
    bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0,
    add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X',
    apply_unit_scale=True, global_scale=1.0, armature_nodetype='NULL')
print("导出（单文件多 take）:", out)
print("  ⚠️ 输出契约已变更：%d 个动作 → 1 个 FBX（多 take）。" % len(results))
print("=== BATCH DONE:", results, "===")
