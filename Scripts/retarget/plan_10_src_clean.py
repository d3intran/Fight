# -*- coding: utf-8 -*-
"""
plan_10_src_clean.py —— 源骨架白名单净化（LOL 俯视角动画 → UE IK Retargeter 可用的干净源 FBX）

背景（实测，见 Saved/Retarget/probe_src_bones.txt / probe_action_api.txt）：
  * LOL skin15 骨架 179 骨，其中真正的人体形变链只有 ~59 根；
    其余是 Lion_*（四足狼灵 70 骨）、Throne/Gem/Piece_*（王座道具）、*Buffbone*（VFX 挂点）、
    Weapon 子树（原版插地斧 15 骨）——必须白名单剔除，否则会把王座/狮子当骨骼重定向。
  * 腿/臂各有一对「几何完全重合的孪生骨」：
        L_Hip -> L_KneeUpper -> L_KneeLower -> L_Foot
        L_Shoulder -> L_ElbowUpper -> L_Elbow -> L_Hand
    实测 matrix_basis 漂移（run 动画）：
        L_KneeUpper  rot = 0.000°   loc = 8.94     <- 纯占位，无旋转
        L_KneeLower  rot = 60.9°    loc = 0        <- 真正承载膝弯
        L_ElbowUpper rot = 0.000°   loc = 0        <- 纯占位
        L_Elbow      rot = 20.1°    loc = 0        <- 真正承载肘弯
    ⇒ **删 `*Upper`、保 `*Lower`**。（若反过来删 Lower，会丢掉整条腿 60~103° 的膝弯。）
  * 关节真值只能用 `head_local`；`tail` 与 bone.length 在 glTF 导入后不可信
    （实测 L_Hip.tail 指向 -Y 前方，而真实髋->膝方向是 -Z 下方）。
    踝关节 = `L_Foot.head`（z=16.93），**不是** `L_KneeLower.tail`（z=56.54，差 39.6）。

手术步骤：
  1) 采样：全部 action × 全帧，记录「被重挂骨」与「验证骨」的 armature-space 世界矩阵
  2) 重挂：L_KneeLower -> L_Hip、L_Elbow -> L_Shoulder（use_connect=False，rest 不变）
  3) 删除：所有不在 KEEP 白名单里的骨（含子树）
  4) 清理：删除指向已删骨的 fcurve
  5) 回写：把采样到的世界矩阵逐帧写回被重挂的骨（补偿消失的父级贡献）
  6) 验证：重新采样全部 action，逐帧比对世界矩阵（位置 + 旋转），并校验 rest pose 未变
  7) 导出 FBX（多 take，30fps）+ 写报告

用法：
  blender -b -P Scripts/retarget/plan_10_src_clean.py -- <SRC_GLB> <OUT_FBX> <OUT_REPORT_TXT>
"""
import bpy
import sys
import os
import math

from mathutils import Matrix, Vector, Quaternion

argv = sys.argv[sys.argv.index("--") + 1:]
SRC = argv[0]
OUT_FBX = argv[1]
OUT_REPORT = argv[2] if len(argv) > 2 else os.path.splitext(OUT_FBX)[0] + "_report.txt"

FPS = 30
# 世界矩阵逐帧比对容差。源单位≈cm。
# 实测残余偏差来源：float32 关键帧精度经骨链成比例放大（Root≈0 → 末梢 0.0135 单位 = 0.135mm）。
# 参照量：若漏补偿 L_KneeUpper 的 8.94 平移，偏差会是「8.94」量级 ⇒ 容差对其仍有 180 倍判别力。
POS_TOL_CM = 5e-2      # 0.5 mm
ROT_TOL_DEG = 5e-2     # 0.05°

lines = []


def P(s=""):
    """实时落盘——Blender 无头模式崩溃时也能保住已完成的进度。"""
    t = str(s)
    lines.append(t)
    print(t, flush=True)
    if OUT_REPORT:
        try:
            os.makedirs(os.path.dirname(OUT_REPORT), exist_ok=True)
            with open(OUT_REPORT, "a", encoding="utf-8") as f:
                f.write(t + "\n")
        except Exception:
            pass


if OUT_REPORT and os.path.isfile(OUT_REPORT):
    os.remove(OUT_REPORT)


# ============================================================ 白名单
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

KEEP = KEEP_BODY + KEEP_FINGERS + KEEP_CAPE

# 需要重挂父级的骨： {子骨: 新父骨}
REPARENT = {
    "L_KneeLower": "L_Hip",
    "R_KneeLower": "R_Hip",
    "L_Elbow": "L_Shoulder",
    "R_Elbow": "R_Shoulder",
}

# 用于逐帧验证的骨（覆盖主干 + 手脚 + 重挂骨；这些骨的世界矩阵在净化前后必须一致）
VERIFY_BONES = [
    "Root", "Pelvis", "Spine1", "Spine2", "Neck", "Head", "Jaw",
    "L_Hip", "L_KneeLower", "L_Foot", "L_Toe",
    "R_Hip", "R_KneeLower", "R_Foot", "R_Toe",
    "L_Clavicle", "L_Shoulder", "L_Elbow", "L_Hand",
    "R_Clavicle", "R_Shoulder", "R_Elbow", "R_Hand",
    "Cape", "C_Cape1", "L_Cape1", "R_Cape1",
]
WRITE_BONES = list(REPARENT.keys())


# ============================================================ 工具
def action_fcurves(act):
    """Blender 4.4+ slotted action 兼容读取。"""
    out = []
    for layer in getattr(act, "layers", []):
        for strip in getattr(layer, "strips", []):
            for cb in (getattr(strip, "channelbags", None) or []):
                out.extend(cb.fcurves)
    if out:
        return out
    try:
        return list(act.fcurves)
    except AttributeError:
        return []


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


# ============================================================ 导入
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
sc.render.fps_base = 1.0

bpy.ops.import_scene.gltf(filepath=SRC)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]

P("=" * 100)
P("### plan_10_src_clean —— 源骨架白名单净化")
P("=" * 100)
P("SRC      = %s" % SRC)
P("OUT_FBX  = %s" % OUT_FBX)
P("fps      = %d" % FPS)
P("bone count (原始) = %d" % len(arm.data.bones))
P("白名单 KEEP = %d 骨" % len(KEEP))

bones_now = set(b.name for b in arm.data.bones)
missing = [n for n in KEEP if n not in bones_now]
if missing:
    raise SystemExit("白名单里有源骨架不存在的骨: %s" % missing)
extra = sorted(bones_now - set(KEEP))
P("超出白名单待删 = %d 骨" % len(extra))

# 源身高（用于把偏差换算成相对量）。
# 定义：Head.tail.z - min(L_Toe.head.z, R_Toe.head.z)。
# 不能用「全骨 z 范围」——源骨架里 Gem / L_Throne / R_Throne 等道具骨的 tail 在 z=660~836，
# 会把「身高」算成 927（已实测踩过）。
_mw = arm.matrix_world
SRC_HEIGHT = ((_mw @ arm.data.bones["Head"].tail_local).z
              - min((_mw @ arm.data.bones[n].head_local).z for n in ("L_Toe", "R_Toe")))
P("源骨架 bind 身高（Head.tail - Toe.head）= %.4f 单位" % SRC_HEIGHT)

# rest pose 基线（净化后必须逐位不变）
rest_base = {}
for n in KEEP:
    rest_base[n] = arm.data.bones[n].matrix_local.copy()

# 父级基线
parent_base = {}
for n in KEEP:
    b = arm.data.bones[n]
    parent_base[n] = b.parent.name if b.parent else None

# ============================================================ 1) 采样
acts = sorted(bpy.data.actions, key=lambda a: a.name)
P("")
P("=== [1] 采样 %d 个 action ===" % len(acts))

# wb_sample[act][frame][bone] = Matrix (armature space)
wb_sample = {}
# vf_sample[act][frame][bone] = (loc3, quat4)
vf_sample = {}
act_range = {}

for a in acts:
    if not set_action(arm, a):
        P("  !! 无法绑定 action %s —— 跳过" % a.name)
        continue
    fr = a.frame_range
    f0, f1 = int(round(fr[0])), int(round(fr[1]))
    act_range[a.name] = (f0, f1)
    wb_sample[a.name] = {}
    vf_sample[a.name] = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        wbs = {}
        for bn in WRITE_BONES:
            pb = arm.pose.bones.get(bn)
            if pb:
                wbs[bn] = pb.matrix.copy()
        wb_sample[a.name][f] = wbs
        vfs = {}
        for bn in VERIFY_BONES:
            pb = arm.pose.bones.get(bn)
            if pb:
                vfs[bn] = pb.matrix.copy()      # 存完整 4x4：覆盖平移/旋转/缩放
        vf_sample[a.name][f] = vfs
    P("  %-42s frames %3d..%3d (%3d 帧)" % (a.name, f0, f1, f1 - f0 + 1))

total_frames = sum(v[1] - v[0] + 1 for v in act_range.values())
P("  合计 %d 帧 × %d 验证骨" % (total_frames, len(VERIFY_BONES)))

# ============================================================ 2) 重挂 + 3) 删除
P("")
P("=== [2] 重挂父级 ===")
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones

# 进入 edit mode 后立刻快照全部保留骨的 rest 定义。
# 动机（实测）：`bpy.ops.armature.delete()` 会触发 edit_bone 的 roll 重算，
# 而 R_Foot 是 0.014 单位微骨且 Y 轴指向 -Z，重算产生 2.68e-4 的 rest 漂移，
# 经骨链放大成 0.0135 单位的世界位置偏差。对照实验（仅进出 edit mode、零修改）
# 证明这不是 Blender 的固有行为，而是删除操作引入的 —— 故在删除后显式写回。
rest_snap = {}
for n in KEEP:
    b = eb.get(n)
    if b is not None:
        rest_snap[n] = (b.head.copy(), b.tail.copy(), b.roll)

for child, newp in REPARENT.items():
    old_p = eb[child].parent.name if eb[child].parent else None
    head_before = eb[child].head.copy()
    eb[child].parent = eb[newp]
    eb[child].use_connect = False
    P("  %-16s  parent: %-16s -> %-16s   head 位移=%.6f" % (
        child, old_p, newp, (eb[child].head - head_before).length))

P("")
P("=== [3] 删除非白名单骨（含子树）===")
bpy.ops.armature.select_all(action='DESELECT')
deleted_sel = []
for b in eb:
    if b.name not in KEEP:
        b.select = True
        deleted_sel.append(b.name)
P("  选中待删 %d 骨" % len(deleted_sel))
bpy.ops.armature.delete()

P("")
P("=== [3a] 写回 rest 快照（抵消 delete 触发的 roll 重算漂移）===")
rest_restore_dev = 0.0
rest_restore_bone = ""
# 两趟：先全断开 use_connect，再写 head/tail/roll。
# 否则设定父骨 tail 时，仍处于 connect 状态的子骨 head 会被一起拉走。
for n in KEEP:
    b = eb.get(n)
    if b is not None:
        b.use_connect = False
for n in KEEP:
    b = eb.get(n)
    if b is None:
        continue
    h, t, r = rest_snap[n]
    b.head = h
    b.tail = t
    b.roll = r
for n in KEEP:
    b = eb.get(n)
    if b is None:
        continue
    h, t, r = rest_snap[n]
    d = max((b.head - h).length, (b.tail - t).length, abs(b.roll - r))
    if d > rest_restore_dev:
        rest_restore_dev, rest_restore_bone = d, n
P("  写回后与快照偏差 = %.3e  (%s)" % (rest_restore_dev, rest_restore_bone))

bpy.ops.object.mode_set(mode='OBJECT')

remain = sorted(b.name for b in arm.data.bones)
P("  删除后剩余骨 = %d" % len(remain))
leftover = [n for n in remain if n not in KEEP]
stripped = [n for n in KEEP if n not in remain]
P("  非白名单残留 = %s" % (leftover if leftover else "无"))
P("  白名单被误删 = %s" % (stripped if stripped else "无"))
if leftover or stripped:
    P("  !! 结构异常")

# rest 校验
P("")
P("=== [3b] rest pose 校验（净化前后 matrix_local 应逐位一致）===")
worst_rest = 0.0
worst_name = ""
for n in KEEP:
    if n not in arm.data.bones:
        continue
    d = max(abs(arm.data.bones[n].matrix_local[i][j] - rest_base[n][i][j])
            for i in range(4) for j in range(4))
    if d > worst_rest:
        worst_rest, worst_name = d, n
P("  最大 rest 偏差 = %.3e  (%s)" % (worst_rest, worst_name))
P("  父级关系:")
for n in KEEP:
    if n not in arm.data.bones:
        continue
    pn = arm.data.bones[n].parent.name if arm.data.bones[n].parent else None
    old = parent_base[n]
    if pn != old:
        P("     %-16s %-16s -> %-16s" % (n, old, pn))

# ============================================================ 4) fcurve 清理
P("")
P("=== [4] 清理指向已删骨的 fcurve ===")
removed_fc = 0
for a in acts:
    killed = set(deleted_sel)
    for cb in channelbags(a):
        for fc in list(cb.fcurves):
            bn = fcurve_bone(fc)
            if bn is not None and bn not in KEEP:
                try:
                    cb.fcurves.remove(fc)
                    removed_fc += 1
                except Exception:
                    pass
P("  移除 fcurve = %d" % removed_fc)
for a in acts[:3]:
    P("  %-42s 剩余 fcurve = %d" % (a.name, len(action_fcurves(a))))

# ============================================================ 5) 回写
P("")
P("=== [5] 世界矩阵回写（补偿消失的父级贡献）===")
for bn in WRITE_BONES:
    pb = arm.pose.bones.get(bn)
    if pb:
        pb.rotation_mode = 'QUATERNION'

wb_imm = {}
wb_re = {}
P("  %-42s %12s %12s %s" % ("action", "immReadDev", "reEvalDev", "worst bone@frame"))
for a in acts:
    if a.name not in wb_sample:
        continue
    if not set_action(arm, a):
        continue
    f0, f1 = act_range[a.name]
    imm = 0.0
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for bn in WRITE_BONES:
            pb = arm.pose.bones.get(bn)
            if pb is None or bn not in wb_sample[a.name][f]:
                continue
            pb.matrix = wb_sample[a.name][f][bn]
            pb.keyframe_insert("location", frame=f)
            pb.keyframe_insert("rotation_quaternion", frame=f)
            # scale 也一起写：确认是否有骨骼缩放通道
            pb.keyframe_insert("scale", frame=f)
            d = (pb.matrix.translation - wb_sample[a.name][f][bn].translation).length
            if d > imm:
                imm = d
    # 重新求值后再读（模拟验证路径）
    re = 0.0
    re_f, re_b = 0, ""
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for bn in WRITE_BONES:
            pb = arm.pose.bones.get(bn)
            if pb is None or bn not in wb_sample[a.name][f]:
                continue
            d = (pb.matrix.translation - wb_sample[a.name][f][bn].translation).length
            if d > re:
                re, re_f, re_b = d, f, bn
    wb_imm[a.name] = imm
    wb_re[a.name] = re
    flag = ""
    if re > POS_TOL_CM:
        flag = "  <== WRITEBACK GAP"
    P("  %-42s %12.6f %12.6f %s%s" % (a.name, imm, re, ("%s@%d" % (re_b, re_f)) if re_b else "-", flag))
P("  回写完成：%d 个 action，%d 帧" % (len(act_range), total_frames))

# ============================================================ 6) 验证
P("")
P("=== [6] 验证：净化后逐帧重采样，与净化前比对 ===")
bone_maxdev = {bn: 0.0 for bn in VERIFY_BONES}
P("  %-42s %11s %11s %11s %8s %s" % (
    "action", "maxPosDev", "maxRotDev", "maxSclDev", "badFrames", "bad span"))
worst_pos_all = 0.0
worst_rot_all = 0.0
worst_where = ("", "", 0, 0.0)
fail_acts = []

for _ai, a in enumerate(acts):
    if a.name not in vf_sample:
        continue
    P("  [verify %d/%d] %s" % (_ai + 1, len(acts), a.name))
    if not set_action(arm, a):
        continue
    f0, f1 = act_range[a.name]
    max_pos = 0.0
    max_rot = 0.0
    max_scl = 0.0
    wp_bone, wp_frame = "", 0
    bad_frames = 0
    bad_first, bad_last = -1, -1
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        ref = vf_sample[a.name][f]
        fbad = False
        for bn in VERIFY_BONES:
            pb = arm.pose.bones.get(bn)
            if pb is None or bn not in ref:
                continue
            m = pb.matrix
            rm = ref[bn]
            dp = (m.translation - rm.translation).length
            dr = math.degrees(abs(m.to_quaternion().rotation_difference(rm.to_quaternion()).angle))
            ds = 0.0
            for i in range(3):
                ds = max(ds, abs(m.col[i].xyz.length - rm.col[i].xyz.length))
            if dp > max_pos:
                max_pos, wp_bone, wp_frame = dp, bn, f
            if dp > bone_maxdev[bn]:
                bone_maxdev[bn] = dp
            if dr > max_rot:
                max_rot = dr
            if ds > max_scl:
                max_scl = ds
            if dp > 1e-5 or dr > 1e-4 or ds > 1e-5:
                fbad = True
        if fbad:
            bad_frames += 1
            if bad_first < 0:
                bad_first = f
            bad_last = f
    tag = ""
    if max_pos > POS_TOL_CM or max_rot > ROT_TOL_DEG:
        tag = "  <== FAIL"
        fail_acts.append(a.name)
    P("  %-42s %11.6f %11.6f %11.6f %8d %s%s" % (
        a.name, max_pos, max_rot, max_scl, bad_frames,
        ("[%d..%d]" % (bad_first, bad_last)) if bad_frames else "-", tag))
    if max_pos > worst_pos_all:
        worst_pos_all = max_pos
        worst_where = (a.name, wp_bone, wp_frame, max_pos)
    if max_rot > worst_rot_all:
        worst_rot_all = max_rot

P("")
P("  全局最大位置偏差 = %.6f 单位  (%s / %s / frame %d)" % (
    worst_pos_all, worst_where[0], worst_where[1], worst_where[2]))
P("  全局最大旋转偏差 = %.6f 度" % worst_rot_all)
P("  超差 action = %s" % (fail_acts if fail_acts else "无 (全部 PASS)"))
P("  容差: pos < %.4f 单位, rot < %.2f 度" % (POS_TOL_CM, ROT_TOL_DEG))

P("")
P("=== [6c] 各验证骨的最大位置偏差 —— 判断是否为链式浮点累积 ===")
P("  若自 Root/Pelvis 向外单调放大，即为「float32 关键帧精度 × 骨链放大量级」的证据；")
P("  若有骨单独异常，则说明该处存在真实的结构损伤。")
P("  %-16s %12s %14s" % ("bone", "maxPosDev", "相对源身高"))
for bn in VERIFY_BONES:
    v = bone_maxdev.get(bn, 0.0)
    P("  %-16s %12.6f %13.3e" % (bn, v, v / SRC_HEIGHT if SRC_HEIGHT else 0.0))

# ============================================================ 6b) 被删骨活动性统计
P("")
P("=== [6b] 被删骨在动画中的活动性（用于确认删除无损失）===")
probe_del = [b for b in deleted_sel if b in ("Lion_Root", "Lion_Spine1", "Throne", "L_Throne",
                                             "Gem", "Piece_1", "Weapon", "Axe_Head", "SnapWeapon")]
P("  说明：这些骨已在步骤 3 删除，其活动性由步骤 1 之前的 probe 报告给出：")
P("    Lion_Root / Lion_Spine1 / Throne 在 idle1 / run / run_fast 中世界位置 spread = 0.0000")
P("    Weapon / Axe_Head 随右手运动（spread 80.99 / 80.22），但本管线用独立 SM 战斧，应删。")

# ============================================================ 7) 导出
P("")
P("=== [7] 准备导出（保留一个蒙皮网格作骨架载体）===")
# ⚠️ UE 的 FBX 导入需要**至少一个 SkeletalMesh** 才能建出 Skeleton + AnimSequence。
# 只导出纯骨架的 FBX，UE 会「导入成功但产出 0 个资产」（已实测，见 plan_14）。
# 因此保留源网格作为骨架载体，但清空材质槽与非白名单顶点组，避免导入无关贴图。
KEEP_MESH = "Mesh_0"
keep_obj = None
for o in list(bpy.data.objects):
    if o.type != 'MESH':
        continue
    if o.name == KEEP_MESH:
        keep_obj = o
        o.data.materials.clear()
        removed = 0
        for g in list(o.vertex_groups):
            if g.name not in KEEP:
                o.vertex_groups.remove(g)
                removed += 1
        P("  保留网格 %s：%d 顶点 / 清理 %d 个失效顶点组 / 剩余 %d 组" % (
            o.name, len(o.data.vertices), removed, len(o.vertex_groups)))
    else:
        P("  移除杂物网格: %s" % o.name)
        bpy.data.objects.remove(o, do_unlink=True)

bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True)
if keep_obj is not None:
    keep_obj.select_set(True)
    P("  导出选择集：armature + %s" % keep_obj.name)
bpy.context.view_layer.objects.active = arm

# ⚠️⚠️ 关键：导出前必须把 armature 复位到 rest pose。
# 实测（plan_13 端到端验收暴露）：若此时 armature 停在某个 action 的某帧，
# Blender 的 FBX 导出器会把这**当前 pose** 写成骨架的节点变换 —— 产出的 FBX
# 里 bind pose 完全错误：R_Hand 偏 58.5 单位、Root 偏 20.8 单位、肩宽差 2.0%、
# 躯干长差 3.9%。对重定向是致命伤（IK Retargeter 会用错误的 bind pose 建立参考系）。
# 该坑同样存在于项目里所有逐 action 导出的 FBX 脚本中（导出时 frame 停在哪帧就是哪帧）。
if arm.animation_data:
    arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
P("  导出前已复位到 rest pose（action=None + 清空全部 matrix_basis）")
_rh = arm.matrix_world @ arm.data.bones["Root"].head_local
P("  rest 自检：Root.head_local = (%.4f, %.4f, %.4f)  [源 rest = (0.0000, 0.0000, 127.3700)]"
  % (_rh.x, _rh.y, _rh.z))

os.makedirs(os.path.dirname(OUT_FBX), exist_ok=True)

export_kw = dict(
    filepath=OUT_FBX,
    use_selection=True,
    bake_anim=True,
    bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=False,
    bake_anim_use_all_actions=True,      # 一次导出全部 action 为多个 take
    bake_anim_force_startend_keying=True,
    bake_anim_simplify_factor=0.0,       # 不简化曲线
    add_leaf_bones=False,
    primary_bone_axis='Y',
    secondary_bone_axis='X',
    apply_unit_scale=True,
    global_scale=1.0,
    armature_nodetype='NULL',
)
OPTIONAL_KEYS = ["bake_anim_simplify_factor", "bake_anim_force_startend_keying",
                 "bake_anim_use_all_actions", "bake_anim_use_all_bones",
                 "bake_anim_use_nla_strips", "armature_nodetype"]

exported = False
for drop_n in range(0, len(OPTIONAL_KEYS) + 1):
    kw = {k: v for k, v in export_kw.items() if k not in OPTIONAL_KEYS[:drop_n]}
    try:
        bpy.ops.export_scene.fbx(**kw)
        exported = True
        P("  导出成功（剔除可选参数 %s）: %s" % (OPTIONAL_KEYS[:drop_n] or "无", OUT_FBX))
        break
    except TypeError as ex:
        P("  参数集不被支持（剔除 %s）: %s" % (OPTIONAL_KEYS[:drop_n], ex))
if not exported:
    P("  !! FBX 导出失败：所有参数组合均不可用")
else:
    P("  FBX 存在 = %s" % os.path.isfile(OUT_FBX))

if os.path.isfile(OUT_FBX):
    P("  FBX 大小 = %.2f MB" % (os.path.getsize(OUT_FBX) / 1024.0 / 1024.0))

# ============================================================ 8) 报告
P("")
P("=== [8] 汇总 ===")
P("  骨数：%d -> %d" % (len(bones_now), len(remain)))
P("  action 数：%d" % len(act_range))
P("  帧数合计：%d" % total_frames)
P("  rest pose 最大偏差：%.3e" % worst_rest)
P("  世界矩阵最大位置偏差：%.6f 单位" % worst_pos_all)
P("  世界矩阵最大旋转偏差：%.6f 度" % worst_rot_all)
P("  超差 action：%s" % (fail_acts if fail_acts else "无"))
P("=== DONE ===")

if OUT_REPORT:
    os.makedirs(os.path.dirname(OUT_REPORT), exist_ok=True)
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("WROTE report %s" % OUT_REPORT)
