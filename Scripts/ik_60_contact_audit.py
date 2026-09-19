# -*- coding: utf-8 -*-
"""接触与落点审计器（G8-lite）——回答「交叉腿第一次出现在哪一层」。

## 为什么要有它
现有判据（朝向 + twist）**只比方向**，不比位置。方向全对也可能夹腿/交叉：
脚的位置同时取决于髋间距、大腿与小腿长度、各段方向。本项目已记录
**目标髋宽比源窄约 22%**，照搬源动画的内收方向到更窄的髋，脚可能靠拢甚至交叉。
⇒ 必须有一组**只看三维位置**的判据，否则「腿方向 0.01°」会被误读成「腿没问题」。

## 本脚本量什么（全部在**身体坐标系**下，且按各自身高归一化 ⇒ 跨骨架可比）
1. **髋间距**：左右髋关节横向距离 / 身高
2. **双脚横向次序与间距**：左右脚的横向坐标；`lat_L − lat_R` 的**符号变号** = 交叉
3. **腿段最近距离**：左右腿链（髋→膝→踝）两条折线之间的最小距离 / 身高
4. **支撑脚漂移**：每帧较低的脚视为支撑脚，量它相邻帧的水平位移（滑步代理指标）
5. **脚底朝向**：脚踝→脚尖方向与身体 up 的夹角（脚掌是否平放）
6. **循环接缝**：首帧与末帧各关节位置的最大差 / 身高（接缝跳变）

## 用法（经网关跑，注意脚本 docstring 里别写自己的文件名，会被 UE 误判成路径）
    uv run --no-project python Scripts/ue_remote.py Scripts/<本脚本>

输出两组（源 / 产物）的逐帧表 + 汇总，**并排给出判定**：
源就交叉 ⇒ 问题在转换层；源干净而产物交叉 ⇒ 问题在重定向层。
"""
import json
import math
import os
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary

CFG = "E:/UE/Fight/Saved/retarget_cycle.json"
TGT_DIR = "/Game/Character/Darius/Anims_TP_v2"
if os.path.isfile(CFG):
    try:
        with open(CFG, encoding="utf-8") as fh:
            TGT_DIR = json.load(fh).get("out_dir") or TGT_DIR
    except Exception as ex:
        LW("读 %s 失败: %s" % (CFG, ex))


def qmat(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def mv(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def norm(v):
    m = dot(v, v) ** 0.5
    return (v[0] / m, v[1] / m, v[2] / m) if m > 1e-9 else (0.0, 0.0, 0.0)


def dist(a, b):
    return dot(sub(a, b), sub(a, b)) ** 0.5


def seg_seg_dist(p1, q1, p2, q2):
    """两条线段之间的最短距离（标准 closest-point-between-segments 算法）。"""
    d1, d2 = sub(q1, p1), sub(q2, p2)
    r = sub(p1, p2)
    a, e, f = dot(d1, d1), dot(d2, d2), dot(d2, r)
    c, b = dot(d1, r), dot(d1, d2)
    denom = a * e - b * b
    s = 0.0 if denom <= 1e-12 else max(0.0, min(1.0, (b * f - c * e) / denom))
    t = (b * s + f) / e if e > 1e-12 else 0.0
    t = max(0.0, min(1.0, t))
    s = 0.0 if denom <= 1e-12 else max(0.0, min(1.0, (b * t - c) / a)) if a > 1e-12 else 0.0
    return dist(add(p1, mul(d1, s)), add(p2, mul(d2, t)))


# 骨名对应：源（LOL 净化版） / 目标（2XKO）
BONES = {
    "src": {"root": "Root", "hip_l": "L_Hip", "hip_r": "R_Hip",
            "knee_l": "L_KneeLower", "knee_r": "R_KneeLower",
            "foot_l": "L_Foot", "foot_r": "R_Foot",
            "toe_l": "L_Toe", "toe_r": "R_Toe",
            "spine": "Spine2", "head": "Head"},
    "tgt": {"root": "root", "hip_l": "thigh_l", "hip_r": "thigh_r",
            "knee_l": "calf_l", "knee_r": "calf_r",
            "foot_l": "foot_l", "foot_r": "foot_r",
            "toe_l": "ball_l", "toe_r": "ball_r",
            "spine": "spine_03", "head": "head"},
}

PAIRS = [
    ("idle1",
     "/Game/Character/Darius/LOL_Source/SK_LOL_Dariusskinned_mesh_darius_skin15_idle1",
     TGT_DIR + "/A_Darius_idle1"),
    ("run",
     "/Game/Character/Darius/LOL_Source/SK_LOL_Dariusskinned_mesh_darius_skin15_run",
     TGT_DIR + "/A_Darius_run"),
]


class Sampler:
    """一次性取完局部变换，FK 全在 Python 里算（沿用 ik_37 的防崩写法）。"""

    def __init__(self, anim, tag, bone_map):
        self.tag = tag
        self.bm = bone_map
        self.path = {}
        need = set(bone_map.values())
        for b in need:
            try:
                self.path[b] = [str(x) for x in AL.find_bone_path_to_root(anim, b)][::-1]
            except Exception as ex:
                LW("   [%s] 路径失败 %s: %s" % (tag, b, str(ex)[:60]))
                self.path[b] = []
        bones = set()
        for p in self.path.values():
            bones.update(p)
        self.bones = sorted(bones)
        n = int(AL.get_num_frames(anim))
        self.frames = list(range(n))          # 全帧：接缝与逐帧异常都要看
        self.local = {}
        for f in self.frames:
            d = {}
            for b in self.bones:
                try:
                    t = AL.get_bone_pose_for_frame(anim, b, f, False)
                    d[b] = ((t.translation.x, t.translation.y, t.translation.z),
                            (t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w),
                            (t.scale3d.x, t.scale3d.y, t.scale3d.z))
                except Exception:
                    d[b] = None
            self.local[f] = d
        self.n_frames = n

    def pos(self, bone, frame):
        chain = self.path.get(bone) or []
        p, q, s = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0)
        for bn in chain:
            tr = self.local[frame].get(bn)
            if tr is None:
                continue
            t, bq, bs = tr
            off = mv(qmat(q), (t[0] * s[0], t[1] * s[1], t[2] * s[2]))
            p = (p[0] + off[0], p[1] + off[1], p[2] + off[2])
            q = qmul(q, bq)
            s = (s[0] * bs[0], s[1] * bs[1], s[2] * bs[2])
        return p

    # ---------------------------------------------------------------- 身体坐标系
    def frame_axes(self, frame):
        bm = self.bm
        hl, hr = self.pos(bm["hip_l"], frame), self.pos(bm["hip_r"], frame)
        origin = mul(add(hl, hr), 0.5)
        right = norm(sub(hr, hl))                       # 左 → 右
        up = norm(sub(self.pos(bm["spine"], frame), origin))
        fwd = norm(cross(up, right))
        right = norm(cross(fwd, up))                    # 正交化
        up = norm(cross(right, fwd))
        return origin, right, up, fwd

    def lat(self, p, frame):
        """点在身体坐标系下的横向坐标（+ = 右侧）。"""
        o, r, u, f = self.frame_axes(frame)
        return dot(sub(p, o), r)

    def height_scale(self, frame):
        """归一化标尺：**平均腿长** = |髋→膝| + |膝→踝|（左右取平均）。

        ⚠️ 不用 `root→head`：源骨架的 `Root` 在髋部附近、目标的 `root` 在原点，
        **语义不同**（名字像 ≠ 同义，评审明确警告过），拿它归一化会得出
        「源髋间距 0.41 / 目标 0.11」这种不可比的数。腿长两侧定义一致，可跨骨架比。
        """
        bm = self.bm
        a = dist(self.pos(bm["hip_l"], frame), self.pos(bm["knee_l"], frame)) \
            + dist(self.pos(bm["knee_l"], frame), self.pos(bm["foot_l"], frame))
        b = dist(self.pos(bm["hip_r"], frame), self.pos(bm["knee_r"], frame)) \
            + dist(self.pos(bm["knee_r"], frame), self.pos(bm["foot_r"], frame))
        return max(1e-6, (a + b) * 0.5)


def audit(anim, tag, bone_map):
    s = Sampler(anim, tag, bone_map)
    bm = bone_map
    rows = []
    for f in s.frames:
        o, r, u, fw = s.frame_axes(f)
        H = s.height_scale(f)
        hl, hr = s.pos(bm["hip_l"], f), s.pos(bm["hip_r"], f)
        kl, kr = s.pos(bm["knee_l"], f), s.pos(bm["knee_r"], f)
        fl, fr_ = s.pos(bm["foot_l"], f), s.pos(bm["foot_r"], f)
        tl, tr = s.pos(bm["toe_l"], f), s.pos(bm["toe_r"], f)
        # 1 髋间距
        hip_w = dist(hl, hr) / H
        # 2 双脚横向次序与间距（+ = 右脚在右，正常；<=0 ⇒ 次序反转）
        lat_l, lat_r = s.lat(fl, f), s.lat(fr_, f)
        foot_gap = (lat_r - lat_l) / H       # 正常应为正（右脚在右）
        # 膝一级同样测一次：区分「膝盖以下真交叉」与「整条链镜像/映射错位」
        knee_gap = (s.lat(kr, f) - s.lat(kl, f)) / H
        hip_gap = (s.lat(hr, f) - s.lat(hl, f)) / H
        # 3 腿段最近距离
        leg_min = min(seg_seg_dist(hl, kl, hr, kr), seg_seg_dist(kl, fl, kr, fr_)) / H
        # 4 支撑脚（较低的脚）与漂移（上一帧比）
        sup_is_l = dot(sub(fl, o), u) <= dot(sub(fr_, o), u)
        sup = fl if sup_is_l else fr_
        rows.append(dict(f=f, hip_w=hip_w, foot_gap=foot_gap, knee_gap=knee_gap,
                         hip_gap=hip_gap, leg_min=leg_min,
                         sup=sup, lat_l=lat_l / H, lat_r=lat_r / H,
                         ankle_l=dot(sub(fl, o), u) / H, ankle_r=dot(sub(fr_, o), u) / H,
                         toe_l=tl, toe_r=tr, H=H))
    # 支撑脚漂移（水平位移，按身高归一）
    drifts = []
    for i in range(1, len(rows)):
        a, b = rows[i - 1]["sup"], rows[i]["sup"]
        d = dist((a[0], a[1], 0.0), (b[0], b[1], 0.0))       # 世界水平面 XY
        drifts.append(d / rows[i]["H"])
    # 脚底朝向：脚踝→脚尖 与 身体 up 的夹角（90° ≈ 平放，越小 = 越竖直/脚尖朝下）
    foot_tilt = []
    for row in rows:
        f = row["f"]
        o, r, u, fw = s.frame_axes(f)
        for ankle, toe in ((bm["foot_l"], bm["toe_l"]), (bm["foot_r"], bm["toe_r"])):
            d = norm(sub(s.pos(toe, f), s.pos(ankle, f)))
            foot_tilt.append(math.degrees(math.acos(max(-1.0, min(1.0, dot(d, u))))) - 90.0)
    # 循环接缝：首末帧所有关节位置差
    seam = 0.0
    if len(s.frames) > 1:
        f0, f1 = s.frames[0], s.frames[-1]
        for b in s.bones:
            seam = max(seam, dist(s.pos(b, f0), s.pos(b, f1)))
    return dict(
        tag=tag, n=s.n_frames,
        hip_w=(min(x["hip_w"] for x in rows), sum(x["hip_w"] for x in rows) / len(rows)),
        hip_gap_mean=sum(x["hip_gap"] for x in rows) / len(rows),
        knee_gap_mean=sum(x["knee_gap"] for x in rows) / len(rows),
        foot_gap_min=min(x["foot_gap"] for x in rows),
        foot_gap_mean=sum(x["foot_gap"] for x in rows) / len(rows),
        cross_frames=[x["f"] for x in rows if x["foot_gap"] <= 0.0],
        leg_min=min(x["leg_min"] for x in rows),
        drift_max=max(drifts) if drifts else 0.0,
        drift_mean=sum(drifts) / len(drifts) if drifts else 0.0,
        tilt_max=max(abs(t) for t in foot_tilt),
        seam=seam / rows[0]["H"],
        rows=rows,
    )


L("=== 接触 / 落点审计（身体坐标系，按各自身高归一化；比例无量纲）===")
L("    判读：foot_gap<=0 ⇒ 双脚左右次序反了（交叉）；leg_min 极小 ⇒ 两腿贴死；")
L("          drift = 支撑脚相邻帧水平位移（滑步代理）；tilt = 脚掌相对身体 up 的偏差；seam = 首末帧跳变")
for tag, src_p, tgt_p in PAIRS:
    sa = eal.load_asset(src_p)
    ta = eal.load_asset(tgt_p)
    if sa is None or ta is None:
        LW("  %s 加载失败" % tag)
        continue
    A = audit(sa, "源", BONES["src"])
    B = audit(ta, "产物", BONES["tgt"])
    L("")
    L("################ %s（源 %d 帧 / 产物 %d 帧）" % (tag, A["n"], B["n"]))
    L("    %-14s %10s %10s" % ("指标", "源", "产物"))
    L("    %-14s %10.4f %10.4f" % ("髋间距/腿长", A["hip_w"][1], B["hip_w"][1]))
    L("    %-14s %10.4f %10.4f" % ("髋 次序差", A["hip_gap_mean"], B["hip_gap_mean"]))
    L("    %-14s %10.4f %10.4f" % ("膝 次序差", A["knee_gap_mean"], B["knee_gap_mean"]))
    L("    %-14s %10.4f %10.4f" % ("脚 次序差min", A["foot_gap_min"], B["foot_gap_min"]))
    L("    %-14s %10.4f %10.4f" % ("脚 次序差均值", A["foot_gap_mean"], B["foot_gap_mean"]))
    L("    %-14s %10s %10s" % ("交叉帧数",
                               len(A["cross_frames"]), len(B["cross_frames"])))
    L("    %-14s %10.4f %10.4f" % ("腿段最小距离", A["leg_min"], B["leg_min"]))
    L("    %-14s %10.4f %10.4f" % ("支撑脚漂移max", A["drift_max"], B["drift_max"]))
    L("    %-14s %10.4f %10.4f" % ("脚掌倾斜max", A["tilt_max"], B["tilt_max"]))
    L("    %-14s %10.4f %10.4f" % ("循环接缝", A["seam"], B["seam"]))
    # 逐帧（只打脚间距，够定位）
    L("    ---- 逐帧 脚横向间距（负 = 交叉）----")
    n = min(len(A["rows"]), len(B["rows"]))
    for i in range(n):
        L("    f%-3d 源 %8.4f   产物 %8.4f %s"
          % (A["rows"][i]["f"], A["rows"][i]["foot_gap"], B["rows"][i]["foot_gap"],
             "  <<< 产物交叉" if B["rows"][i]["foot_gap"] <= 0.0 else ""))
    # 判定
    def verdict(X):
        if X["foot_gap_min"] <= 0 and X["knee_gap_mean"] > 0:
            return "膝盖以下交叉（膝序正常、脚序反了）"
        if X["foot_gap_min"] <= 0 and X["knee_gap_mean"] <= 0:
            return "整条腿次序反了 ⇒ 疑似**左右映射错位/镜像**，不是姿态问题"
        if X["foot_gap_mean"] < 0.15:
            return "次序正常但脚间距过小 ⇒ 夹腿（髋窄 22% 是首要嫌疑）"
        return "次序与间距都正常"
    L("    ★ 源  ：%s" % verdict(A))
    L("    ★ 产物：%s" % verdict(B))
    if (not A["cross_frames"]) and B["cross_frames"]:
        L("    ⇒ 源干净、产物坏 ⇒ 问题出在**重定向/姿势层**，不在源与转换")
L("=== DONE ===")
