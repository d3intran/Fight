# -*- coding: utf-8 -*-
"""
wp_108_foot_ik_bake.py —— 数据侧 Foot IK：绕髋旋转补偿（逐脚独立，只改 thigh 一根骨）

路线演进（都是实测教训）
----------------------
· 逐帧 root 平移：全局的，抬低脚连高脚一起抬，对称度 1.16 → 1.92 ✗
· 骨盆压缩：左右相位不同，压缩比例不同，对称 1.22 → 1.68 ✗
· 两骨 IK（调膝角）：蹬直帧 pole 向量退化，q2 接近 180°，脚被甩到 102cm ✗
· ✓ 本版：绕髋**刚性旋转**整条腿。只改 thigh 的局部旋转（calf/foot 局部旋转在整体
  刚性旋转下数学上不变），膝盖弯曲形状与脚踝朝向原样保留，绝不翻转。
  代价 = 蹬地帧脚的水平位置略移（腿稍微收拢），观感自然。

与上一版旋转补偿的关键差异：预估与写入用**同一份** (signed_axis, theta) 解，
θ 不做平滑（上版预估用平滑 θ、写入重新求解，方向和角度错配导致越修越低）。

数学
----
整条腿绕髋转 R：thigh 世界新 = R∘Q_wt，calf 世界新 = R∘Q_wc
calf 局部新 = (R∘Q_wt)⁻¹∘(R∘Q_wc) = Q_wt⁻¹∘Q_wc = 原局部（不变）
thigh 局部新 = conj(Q_pelvis_w) ∘ R ∘ Q_pelvis_w ∘ q_thigh_old
θ：数值迭代，轴 a = normalize(cross(u, Z))（u = ankle−hip），步进 0.5° 至 30°，
   ball'/toe'（= hip + R·(P−hip)）的 min ≥ FLOOR 即停；+a 不行试 −a。

模式：Saved/Attack/wp108_mode.txt → dry（默认）/ apply / reset
FLOOR = 9.5 cm（目标骨架地面读数，M1 基准 AxeWalk 最低 10.45）。

跑法：
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_108_foot_ik_bake.py
"""
import json
import math

import unreal

APE = unreal.AnimPoseExtensions
AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary
L = unreal.log
LW = unreal.log_warning
OPTS = unreal.AnimPoseEvaluationOptions()

MODE_FILE = "E:/UE/Fight/Saved/Attack/wp108_mode.txt"
BASELINE = "E:/UE/Fight/Saved/Attack/wp108_baseline.json"
OUT = "E:/UE/Fight/Saved/Attack/wp108_footik.json"
TGT_DIR = "/Game/Character/Darius/Animations/LOL_Retarget"
PREFIX = "A_Darius_run"

FLOOR = 9.5
MAX_THETA_DEG = 30.0
STEP_DEG = 0.5

LEGS = {
    "left": {"thigh": "thigh_l", "parent": "pelvis", "ball": "ball_l",
             "toe": "toe_l", "ankle": "foot_l"},
    "right": {"thigh": "thigh_r", "parent": "pelvis", "ball": "ball_r",
              "toe": "toe_r", "ankle": "foot_r"},
}


def mode():
    try:
        return open(MODE_FILE, encoding="utf-8").read().strip().lower() or "dry"
    except Exception:
        return "dry"


def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def scl(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def nrm(v):
    m = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    return (v[0] / m, v[1] / m, v[2] / m) if m > 1e-9 else (0.0, 0.0, 0.0)
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)
def qconj(q): return (-q[0], -q[1], -q[2], q[3])
def qrot(q, v):
    u = (q[0], q[1], q[2]); w = q[3]
    uv = cross(u, v); uuv = cross(u, uv)
    return add(add(v, scl(uv, 2 * w)), scl(uuv, 2))
def qaxis(axis, deg):
    rad = math.radians(deg) / 2
    a = nrm(axis); s = math.sin(rad)
    return (a[0] * s, a[1] * s, a[2] * s, math.cos(rad))


def tw(pose, b):
    t = APE.get_bone_pose(pose, unreal.Name(b), unreal.AnimPoseSpaces.WORLD)
    return ((t.translation.x, t.translation.y, t.translation.z),
            (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w))


def solve(p_th, p_ball, p_toe, p_ank):
    """解绕髋的 (signed_axis, theta)；已达标返回 ((0,0,0), 0)"""
    low = min(p_ball[2], p_toe[2])
    if low >= FLOOR:
        return (0.0, 0.0, 0.0), 0.0
    u = nrm(sub(p_ank, p_th))
    axis = nrm(cross(u, (0.0, 0.0, 1.0)))
    for sgn in (1.0, -1.0):
        ax = scl(axis, sgn)
        th = 0.0
        while th < MAX_THETA_DEG:
            th += STEP_DEG
            rq = qaxis(ax, th)
            nb = add(p_th, qrot(rq, sub(p_ball, p_th)))
            nt = add(p_th, qrot(rq, sub(p_toe, p_th)))
            if min(nb[2], nt[2]) >= FLOOR:
                return ax, th
    return (0.0, 0.0, 0.0), 0.0


try:
    with open(BASELINE, encoding="utf-8") as f:
        baseline = json.load(f)
except Exception:
    baseline = {}

ACTION = mode()
L("=" * 104)
L("=== wp_108 数据侧 Foot IK（绕髋旋转补偿）  mode=%s  FLOOR=%.1f ===" % (ACTION, FLOOR))
L("=" * 104)

report = {"mode": ACTION, "floor": FLOOR, "items": []}
applied = 0

for p in sorted(eal.list_assets(TGT_DIR, recursive=False, include_folder=False)):
    a = unreal.load_object(None, p)
    if not isinstance(a, unreal.AnimSequence) or not a.get_name().startswith(PREFIX):
        continue
    nm = a.get_name()
    try:
        bones = [str(x) for x in
                 a.get_editor_property("data_model_interface").get_bone_track_names()]
    except Exception:
        bones = []
    need = {b for cfg in LEGS.values() for b in
            (cfg["thigh"], cfg["parent"], cfg["ball"], cfg["toe"], cfg["ankle"])}
    if not need.issubset(set(bones)):
        LW("   %-30s 缺骨，跳过" % nm)
        continue
    nf = AL.get_num_frames(a)
    n = nf + 1

    frames = []
    for f in range(n):
        try:
            pose = APE.get_anim_pose_at_frame(a, f, OPTS)
        except Exception as ex:
            LW("   %s 帧%d 求值失败 %s" % (nm, f, str(ex)[:50]))
            frames = []
            break
        row = {"f": f}
        for side, cfg in LEGS.items():
            p_th, r_th = tw(pose, cfg["thigh"])
            p_pa, r_pa = tw(pose, cfg["parent"])
            p_ball, _ = tw(pose, cfg["ball"])
            p_toe, _ = tw(pose, cfg["toe"])
            p_ank, _ = tw(pose, cfg["ankle"])
            row[side] = {"p_th": p_th, "r_th": r_th, "r_pa": r_pa,
                         "p_ball": p_ball, "p_toe": p_toe, "p_ank": p_ank}
        frames.append(row)
    if not frames:
        continue

    # ---------- 求解（一次，预估与写入共用同一份 (axis, θ)） ----------
    sols = []
    lows_before, lows_after = [], []
    ik_count = 0
    theta_max = {"left": 0.0, "right": 0.0}
    for row in frames:
        srow = {}
        lows_b, lows_a = [], []
        for side in ("left", "right"):
            d = row[side]
            ax, th = solve(d["p_th"], d["p_ball"], d["p_toe"], d["p_ank"])
            srow[side] = (ax, th)
            if th > 0.01:
                ik_count += 1
                theta_max[side] = max(theta_max[side], th)
            rq = qaxis(ax, th)
            nb = add(d["p_th"], qrot(rq, sub(d["p_ball"], d["p_th"])))
            nt = add(d["p_th"], qrot(rq, sub(d["p_toe"], d["p_th"])))
            lows_b.append(min(d["p_ball"][2], d["p_toe"][2]))
            lows_a.append(min(nb[2], nt[2]))
        sols.append(srow)
        lows_before.append(min(lows_b))
        lows_after.append(min(lows_a))

    L("   %-30s 帧%-4d 最低点 %7.2f → 预计 %7.2f cm   IK 帧 %d   θmax L%.1f/R%.1f°" % (
        nm, nf, min(lows_before), min(lows_after), ik_count,
        theta_max["left"], theta_max["right"]))
    item = {"asset": nm, "frames": n, "lowest_before": round(min(lows_before), 2),
            "lowest_after_est": round(min(lows_after), 2), "ik_frames": ik_count,
            "theta_max": theta_max}
    report["items"].append(item)

    if ACTION == "dry":
        continue
    if min(lows_after) < FLOOR - 1.0:
        LW("   %-30s 预估仍低于 FLOOR-1，跳过" % nm)
        continue

    # ---------- baseline ----------
    if nm not in baseline:
        bl = {}
        for side, cfg in LEGS.items():
            locs, rots, scls = [], [], []
            for f in range(n):
                t = AL.get_bone_pose_for_frame(a, unreal.Name(cfg["thigh"]), f, False)
                locs.append([t.translation.x, t.translation.y, t.translation.z])
                rots.append([t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w])
                scls.append([t.scale3d.x, t.scale3d.y, t.scale3d.z])
            bl[cfg["thigh"]] = {"locs": locs, "rots": rots, "scls": scls}
        baseline[nm] = bl
        L("      baseline 已存")

    ok_all = True
    for side, cfg in LEGS.items():
        bl = baseline[nm][cfg["thigh"]]
        if len(bl["rots"]) != n:
            LW("      %s baseline 帧数不符" % cfg["thigh"]); ok_all = False; continue
        locs = [unreal.Vector(*v) for v in bl["locs"]]
        scls = [unreal.Vector(*v) for v in bl["scls"]]
        rots = []
        for f in range(n):
            q_old = tuple(bl["rots"][f])
            ax, th = sols[f][side]
            if th > 0.01:
                q_p = frames[f][side]["r_pa"]
                q_new = qmul(qmul(qmul(qconj(q_p), qaxis(ax, th)), q_p), q_old)
            else:
                q_new = q_old
            rots.append(unreal.Quat(*q_new))
        ok = a.get_editor_property("controller").set_bone_track_keys(
            cfg["thigh"], locs, rots, scls, False)
        if not ok:
            LW("      %s 写轨失败" % cfg["thigh"]); ok_all = False
    if ok_all:
        eal.save_asset(p, only_if_is_dirty=False)
        applied += 1
        item["written"] = True

with open(BASELINE, "w", encoding="utf-8") as f:
    json.dump(baseline, f, ensure_ascii=False)
L("")
L("   已写入 %d 条" % applied)
if ACTION == "dry":
    L("==> DRY-RUN。把 %s 写成 apply / reset" % MODE_FILE)
L("==> 复验：wp_102（对称度应保持 ~1.16）+ wp_94（支撑脚最低点应 ≥ ~FLOOR）")
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, default=str, indent=1)
L("已写 %s" % OUT)
L("WP108_DONE")
