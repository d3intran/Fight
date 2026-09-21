"""LoL 神王 attack1 → Darius 骨架：世界空间姿态传递（v2，离线纯脚本）。

## 算法
逐骨、按层级顺序：
    Ws_rest = 源骨静止世界旋转      Ws_cur = 源骨当前世界旋转
    Wt_rest = 目标骨静止世界旋转
    G_bone  = Wt_rest · Ws_rest⁻¹              # 每根骨自己的「静止朝向对齐」（含跨骨架约定差）
    M_des   = G_bone · Ws_cur                  # 目标骨应有的世界朝向
    basis   = (W_par_cur · local_rest_rel)⁻¹ · M_des
    pb.rotation_quaternion = basis.to_quaternion()

**为什么用每骨 G_bone 而不是一个全局 G**：两套骨架的静止姿势本来就不同
（LoL 是 T-pose 系、Darius 是 A-pose 系，骨骼 roll 约定也不同）。
全局 G 只能修「整体朝向」，修不了「每根骨自己的朝向约定」。
`G_bone = Wt_rest·Ws_rest⁻¹` 让「静止时目标=目标 rest、源=源 rest」自动成立，
等价于标准重定向器的「local delta 传递」，但不需要额外的 retarget pose。

可选再叠一个全局 `G_extra`（默认单位阵）用于修正残余的整体朝向差。

## 指标（不用骨轴，用**关节连线方向** —— 与项目 `ik_37` 同一套判据）
对每个「父骨→子骨」段，比较源与产物在**世界系**下的连线方向夹角。

用法：
  blender -b -P Scripts/anim/atk_10_lol_upper_retarget.py -- \
      <GLB> <DariusFBX> <CLIP> <OUT_FBX> <OUT_JSON> [GYAW] [pitch] [roll] [sweep]
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
GLB, TGT_FBX, CLIP = argv[0], argv[1], argv[2]
OUT_FBX, OUT_JSON = argv[3], argv[4]
EXTRA = [float(a) for a in argv[5:8]] if len(argv) > 7 and argv[5] != "auto" else [0.0, 0.0, 0.0]
SWEEP = "sweep" in argv

LOG = []


def P(*a):
    s = " ".join(str(x) for x in a)
    LOG.append(s)
    print(s)


# ------------------------------------------------------------------ 骨映射
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
SPINE = [("Spine1", "spine_01"), ("Spine2", "spine_03")]   # spine_02 由这两者 slerp 中点

# 关节连线（父, 子）——用于验收指标
SEG_SRC = [("Pelvis", "Spine1"), ("Spine1", "Spine2"), ("Spine2", "Neck"), ("Neck", "Head"),
           ("L_Clavicle", "L_Shoulder"), ("L_Shoulder", "L_Elbow"), ("L_Elbow", "L_Hand"),
           ("R_Clavicle", "R_Shoulder"), ("R_Shoulder", "R_Elbow"), ("R_Elbow", "R_Hand"),
           ("L_Hip", "L_KneeLower"), ("L_KneeLower", "L_Foot"), ("L_Foot", "L_Toe"),
           ("R_Hip", "R_KneeLower"), ("R_KneeLower", "R_Foot"), ("R_Foot", "R_Toe")]
SEG_TGT = [("pelvis", "spine_01"), ("spine_02", "spine_03"), ("spine_03", "neck_01"), ("neck_01", "head"),
           ("clavicle_l", "upperarm_l"), ("upperarm_l", "lowerarm_l"), ("lowerarm_l", "hand_l"),
           ("clavicle_r", "upperarm_r"), ("upperarm_r", "lowerarm_r"), ("lowerarm_r", "hand_r"),
           ("thigh_l", "calf_l"), ("calf_l", "foot_l"), ("foot_l", "ball_l"),
           ("thigh_r", "calf_r"), ("calf_r", "foot_r"), ("foot_r", "ball_r")]
SEG_NAME = ["spine_low", "spine_up", "neck", "head",
            "arm_l1", "arm_l2", "arm_l3", "arm_r1", "arm_r2", "arm_r3",
            "leg_l1", "leg_l2", "leg_l3", "leg_r1", "leg_r2", "leg_r3"]
GROUP = {"spine_low": "spine", "spine_up": "spine", "neck": "spine", "head": "spine",
         "arm_l1": "arm_l", "arm_l2": "arm_l", "arm_l3": "arm_l",
         "arm_r1": "arm_r", "arm_r2": "arm_r", "arm_r3": "arm_r",
         "leg_l1": "leg", "leg_l2": "leg", "leg_l3": "leg",
         "leg_r1": "leg", "leg_r2": "leg", "leg_r3": "leg"}


def rot3(mat):
    return mat.to_quaternion().to_matrix()


def head_w(arm, name):
    return arm.matrix_world @ arm.data.bones[name].head_local


def head_pose(arm, name):
    return arm.matrix_world @ arm.pose.bones[name].head


def segdir(arm, a, b, pose):
    f = head_pose if pose else head_w
    v = f(arm, b) - f(arm, a)
    return v.normalized() if v.length > 1e-9 else Vector((0, 0, 1))


def body_frame(arm, lbone, rbone):
    """用 rest 的髋轴 + 世界 Z 建该角色自己的体坐标系（右, 前, 上）。

    两套骨架在世界里朝向相反（源面向 −Y、目标面向 +Y），
    所以比较姿态必须**各自换算到自己的体坐标系**，否则量到的是 180° 的朝向差而不是误差。
    """
    v = head_w(arm, rbone) - head_w(arm, lbone)
    v.z = 0.0
    right = v.normalized() if v.length > 1e-6 else Vector((1, 0, 0))
    up = Vector((0, 0, 1))
    fwd = right.cross(up)
    return right, fwd, up


def to_body(v, frame):
    r, f, u = frame
    return Vector((v.dot(r), v.dot(f), v.dot(u)))


def ang(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, a.dot(b)))))


# ------------------------------------------------------------------ 导入
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
bpy.ops.import_scene.gltf(filepath=GLB)
sarm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
act = bpy.data.actions.get(CLIP)
if act is None:
    raise SystemExit("找不到动作 %s；候选=%s" % (CLIP, [a.name for a in bpy.data.actions if CLIP in a.name]))
if not sarm.animation_data:
    sarm.animation_data_create()
sarm.animation_data.action = act
f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
_before = {o for o in bpy.data.objects if o.type == "MESH"}
bpy.ops.import_scene.fbx(filepath=TGT_FBX)
tarm = [o for o in bpy.data.objects if o.type == "ARMATURE" and o is not sarm][0]
# ★ 目标自带网格 = 导入后新增的网格。导出时只能留这些，否则会把 GLB 的源网格
#   （190 单位高）一起导出，在目标场景里变成一坨巨球（实测踩过）。
TGT_MESHES = {o for o in bpy.data.objects if o.type == "MESH"} - _before
P("源 %s(%d 骨) | 动作 %s 帧 %d..%d | 目标 %s(%d 骨) 自带网格=%d（源网格 %d 个已排除）" % (
    sarm.name, len(sarm.data.bones), act.name, f0, f1, tarm.name,
    len(tarm.data.bones), len(TGT_MESHES), len(_before)))

pairs = [(s, t, False) for s, t in MAP.items()] + [(s, t, True) for s, t in SPINE]
pairs = [(s, t, sp) for (s, t, sp) in pairs if s in sarm.data.bones and t in tarm.data.bones]
P("映射命中 %d 骨（含 weapon_jnt）" % len(pairs))

SR = {s: rot3(sarm.matrix_world @ sarm.data.bones[s].matrix_local) for (s, t, sp) in pairs}
TR = {t: rot3(tarm.matrix_world @ tarm.data.bones[t].matrix_local) for (s, t, sp) in pairs}
# spine_02 不在 pairs 里（它由 spine_01/spine_03 的中点补），但反解局部时要它的 rest
TR["spine_02"] = rot3(tarm.matrix_world @ tarm.data.bones["spine_02"].matrix_local)

# 各自体坐标系（rest 定死）—— 所有姿态比较都在体坐标系里做
SF = body_frame(sarm, "L_Hip", "R_Hip")
TF = body_frame(tarm, "thigh_l", "thigh_r")
P("源 体坐标系 右=%s 前=%s 上=%s" % tuple(tuple(round(c, 3) for c in a) for a in SF))
P("目标 体坐标系 右=%s 前=%s 上=%s" % tuple(tuple(round(c, 3) for c in a) for a in TF))


def _height(arm, hd, ft):
    h = arm.matrix_world @ arm.data.bones[hd].head_local
    f = arm.matrix_world @ arm.data.bones[ft].head_local
    return abs(h.z - f.z)


SRC_H = _height(sarm, "Head", "L_Foot")
TGT_H = _height(tarm, "head", "foot_l")
SCALE = TGT_H / SRC_H if SRC_H > 1e-6 else 1.0
P("源身高 %.2f（cm） 目标身高 %.2f（m） => 平移缩放 SCALE = %.6f" % (SRC_H, TGT_H, SCALE))

# ------------------------------------------------------------------ 静止帧诊断
sc.frame_set(f0)
bpy.context.view_layer.update()
P("=" * 74)
P("### 静止帧诊断（**各自体坐标系**下的关节连线方向：右/前/上）")
P("%-10s %-26s %-26s %-26s %s" % ("段", "源 rest", "源 f%d" % f0, "目标 rest", "rest间夹角"))
for nm, (sa, sb), (ta, tb) in zip(SEG_NAME, SEG_SRC, SEG_TGT):
    ds_r = to_body(segdir(sarm, sa, sb, False), SF)
    ds_0 = to_body(segdir(sarm, sa, sb, True), SF)
    dt_r = to_body(segdir(tarm, ta, tb, False), TF)
    P("%-10s (%6.2f,%6.2f,%6.2f) (%6.2f,%6.2f,%6.2f) (%6.2f,%6.2f,%6.2f) %7.1f°" % (
        nm, ds_r.x, ds_r.y, ds_r.z, ds_0.x, ds_0.y, ds_0.z,
        dt_r.x, dt_r.y, dt_r.z, ang(ds_r, dt_r)))

ORDER = sorted(pairs, key=lambda p: len(tarm.data.bones[p[1]].parent_recursive))


def bake(Gx, key=False):
    for pb in tarm.pose.bones:
        pb.rotation_mode = "QUATERNION"
    res = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        W = {}
        for s, t, sp in ORDER:
            Ws_cur = rot3(sarm.matrix_world @ sarm.pose.bones[s].matrix)
            if sp and t == "spine_02":
                continue                     # 稍后由 spine_01/spine_03 中点补
            M_des = Gx @ (TR[t] @ SR[s].inverted()) @ Ws_cur
            tb = tarm.data.bones[t]
            par = tb.parent
            Wpc = W[par.name] if (par and par.name in W) else \
                (rot3(tarm.matrix_world @ par.matrix_local) if par else rot3(tarm.matrix_world))
            Wpr = rot3(tarm.matrix_world @ par.matrix_local) if par else rot3(tarm.matrix_world)
            basis = (Wpc @ (Wpr.inverted() @ TR[t])).inverted() @ M_des
            pb = tarm.pose.bones[t]
            if t == "pelvis":
                # ★ 骨盆平移也要搬：源在攻击中骨盆下沉 53cm、前冲 72cm，
                #   不搬的话目标骨盆停在 rest 高度 ⇒ 腿「蜷在空中」离地（实测踩过）。
                src_d = (sarm.matrix_world @ sarm.pose.bones["Pelvis"].head) - \
                        (sarm.matrix_world @ sarm.data.bones["Pelvis"].head_local)
                db = to_body(src_d, SF) * SCALE
                d_world = db.x * TF[0] + db.y * TF[1] + db.z * TF[2]
                tgt_w = (tarm.matrix_world @ tarm.data.bones["pelvis"].head_local) + d_world
                m4 = M_des.to_4x4()
                m4.translation = tarm.matrix_world.inverted() @ tgt_w
                pb.matrix = m4
                if key:
                    pb.keyframe_insert(data_path="location", frame=f)
                    pb.keyframe_insert(data_path="rotation_quaternion", frame=f)
            else:
                pb.rotation_quaternion = basis.to_quaternion()
                if key:
                    pb.keyframe_insert(data_path="rotation_quaternion", frame=f)
            W[t] = M_des
        # spine_02 = spine_01 与 spine_03 的中点
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
            if key:
                pb.keyframe_insert(data_path="rotation_quaternion", frame=f)
            W[t] = M_des
        bpy.context.view_layer.update()
        res[f] = {nm: ang(to_body(segdir(sarm, sa, sb, True), SF),
                          to_body(segdir(tarm, ta, tb, True), TF))
                  for nm, (sa, sb), (ta, tb) in zip(SEG_NAME, SEG_SRC, SEG_TGT)}
    return res


def summarize(res, label):
    out = {}
    P("%-16s %-8s %6s %8s %8s %8s" % ("候选", "组", "n", "均值", "P90", "最大"))
    for g in ("spine", "arm_l", "arm_r", "leg", "ALL"):
        vals = sorted(v for f in res for nm, v in res[f].items()
                      if g == "ALL" or GROUP[nm] == g)
        if not vals:
            continue
        st = {"n": len(vals), "mean": round(sum(vals) / len(vals), 2),
              "p90": round(vals[int(len(vals) * 0.9)], 2), "max": round(vals[-1], 2)}
        out[g] = st
        P("%-16s %-8s %6d %8.2f %8.2f %8.2f" % (label, g, st["n"], st["mean"], st["p90"], st["max"]))
    return out


if SWEEP:
    P("=" * 74)
    P("### 全局附加旋转扫描（每骨 G_bone 已含静止对齐，这里只试残余整体差）")
    best = None
    for yaw in (0.0, 90.0, -90.0, 180.0, -180.0):
        Gx = Matrix.Rotation(math.radians(yaw), 3, "Z")
        st = summarize(bake(Gx), "extra_yaw=%.0f" % yaw)
        score = st.get("ALL", {}).get("mean", 999)
        if best is None or score < best[0]:
            best = (score, yaw)
    P("=> 最佳 extra_yaw = %.0f （ALL 均值 %.2f°）" % (best[1], best[0]))
    sys.exit(0)

# ------------------------------------------------------------------ 正式
Gx = (Matrix.Rotation(math.radians(EXTRA[0]), 3, "Z")
      @ Matrix.Rotation(math.radians(EXTRA[1]), 3, "Y")
      @ Matrix.Rotation(math.radians(EXTRA[2]), 3, "X"))
P("=" * 74)
P("### 正式烘焙  extra=(yaw %.1f, pitch %.1f, roll %.1f)" % tuple(EXTRA))
# ⚠️ 打键必须在 bake 循环**内部**：bake 之后再 frame_set + keyframe_insert，
#    存下来的会是「最后一帧的 pose」被重复 74 次（实测踩过：整段动画被冻成一帧）。
sc.frame_start, sc.frame_end = f0, f1
if not tarm.animation_data:
    tarm.animation_data_create()
oact = bpy.data.actions.new(name="A_Darius_Attack1_LOL_UB")
tarm.animation_data.action = oact
report = bake(Gx, key=True)
oact.use_fake_user = True
P("关键帧已写:", oact.name, " 帧数 =", f1 - f0 + 1)
stats = summarize(report, "final")

if "diag" in argv:
    P("=" * 74)
    P("### 逐骨诊断（相对各自骨盆的位移，各自体坐标系；源单位 cm / 目标单位 m）")
    for f in (f0, f0 + 11, f0 + 40):
        f = min(f, f1)
        sc.frame_set(f)
        bpy.context.view_layer.update()
        sp_pel = sarm.matrix_world @ sarm.pose.bones["Pelvis"].head
        tp_pel = tarm.matrix_world @ tarm.pose.bones["pelvis"].head
        P("--- frame %d ---" % f)
        for s, t, sp in ORDER:
            ps = to_body((sarm.matrix_world @ sarm.pose.bones[s].head) - sp_pel, SF)
            pt = to_body((tarm.matrix_world @ tarm.pose.bones[t].head) - tp_pel, TF)
            # 源是 cm、目标是 m：把源除以 100 再比
            P("   %-14s 源(%6.2f,%6.2f,%6.2f)  目标(%6.2f,%6.2f,%6.2f)  Δ=%6.2f" % (
                t, ps.x / 100, ps.y / 100, ps.z / 100, pt.x, pt.y, pt.z,
                (Vector((ps.x / 100, ps.y / 100, ps.z / 100)) - pt).length))
        for tag, arm, bn in (("源", sarm, "Pelvis"), ("目标", tarm, "pelvis")):
            pb = arm.pose.bones[bn]
            P("   %s %s scale=%s loc=%s" % (tag, bn,
              tuple(round(x, 4) for x in pb.scale), tuple(round(x, 4) for x in pb.location)))
    sys.exit(0)

os.makedirs(os.path.dirname(OUT_FBX), exist_ok=True)
# ★ 必须在导出前再钉一次 fps：`bpy.ops.import_scene.fbx` 会把场景 fps 改成 FBX 自己的
#   （实测目标 FBX 是 24fps），结果导出的 FBX 时间基变成 24fps —— UE 按 24 解，
#   73 帧就成了 3.04s 而不是 2.43s，播放慢 25%（实测踩过）。
sc.render.fps = 30
sc.render.fps_base = 1.0
P("导出前 scene fps = %s / base = %s（必须 30 / 1.0）" % (sc.render.fps, sc.render.fps_base))
# 只留目标骨架 + 网格，删掉源骨架（否则源会被一起导出）
keep = {tarm} | TGT_MESHES
for o in list(bpy.data.objects):
    if o not in keep:
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except Exception:
            pass
bpy.ops.object.select_all(action="DESELECT")
tarm.select_set(True)
bpy.context.view_layer.objects.active = tarm
# ★ 导出参数照抄项目已验证的 anim_80（多一个 apply_unit_scale 就够致命）
bpy.ops.export_scene.fbx(
    filepath=OUT_FBX, use_selection=False,
    bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
    bake_anim_force_startend_keying=True, add_leaf_bones=False,
    apply_unit_scale=True, global_scale=1.0,
)
P("已导出 FBX:", OUT_FBX)

with open(OUT_JSON, "w", encoding="utf-8") as fh:
    json.dump({"clip": CLIP, "f0": f0, "f1": f1, "extra": EXTRA,
               "stats": stats, "per_frame": {str(f): report[f] for f in report}},
              fh, indent=1, ensure_ascii=False)
with open(os.path.splitext(OUT_JSON)[0] + ".log.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(LOG))
P("已导出 JSON:", OUT_JSON)
