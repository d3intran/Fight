# -*- coding: utf-8 -*-
"""朝向验收器（G1-lite）：逐关节对比源动画与重定向产物的**骨骼方向**。
这是此前一直缺失的判据 —— 之前只量了平移与缩放，所以「手脚扭曲」没被发现。

判据只用**关节坐标**：方向向量 = normalize(子关节位置 − 本关节位置)，
与骨骼朝向矩阵、局部轴约定全部无关（符合 AGENTS.md §0.3）。

--------------------------------------------------------------------
🔴 2026-09-19 崩溃修复（重要）
旧版把 `find_bone_path_to_root()` 写在**内层循环**里，一次验收要调它
`13 段 × 13 帧 × 2 骨 × 2 动画 = 676 次`，每次都新建一个 `TArray<FName>`。
实测第 5 次验收时编辑器 **EXCEPTION_ACCESS_VIOLATION**（崩溃地址
`0x00000200_65736f68` 低 32 位是字符串片段 `"hose"`，典型的悬空字符串引用），
调用栈 `python311 ×12 → PythonScriptPlugin`。
⇒ 修法：**每个 (动画, 骨) 只取一次路径**，立刻转成纯 Python `str` 列表并丢弃原数组；
  再把所有需要的局部变换一次性取完，FK 用纯 Python 算。抽样帧数也从 13 降到 7。
"""
import json
import math
import os
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary

# 🔁 目标目录可被 Saved/retarget_cycle.json 覆盖（实验回路每轮写新目录）
CFG = "E:/UE/Fight/Saved/retarget_cycle.json"
TGT_DIR = "/Game/Character/Darius/Anims_TP"
if os.path.isfile(CFG):
    try:
        with open(CFG, encoding="utf-8") as fh:
            TGT_DIR = json.load(fh).get("out_dir") or TGT_DIR
    except Exception as ex:
        LW("读 %s 失败: %s" % (CFG, ex))

N_SAMPLES = 7


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


def norm(v):
    m = (v[0] ** 2 + v[1] ** 2 + v[2] ** 2) ** 0.5
    return (v[0] / m, v[1] / m, v[2] / m) if m > 1e-9 else (0.0, 0.0, 0.0)


def angle(u, v):
    d = max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1] + u[2] * v[2]))
    return math.degrees(math.acos(d))


# 关节对应（源骨, 目标骨）；一条「段」= 本关节 → 子关节
SEGMENTS = [
    ("大腿L",   ("L_Hip", "L_KneeLower"),      ("thigh_l", "calf_l")),
    ("小腿L",   ("L_KneeLower", "L_Foot"),     ("calf_l", "foot_l")),
    ("大腿R",   ("R_Hip", "R_KneeLower"),      ("thigh_r", "calf_r")),
    ("小腿R",   ("R_KneeLower", "R_Foot"),     ("calf_r", "foot_r")),
    ("大臂L",   ("L_Shoulder", "L_Elbow"),     ("upperarm_l", "lowerarm_l")),
    ("小臂L",   ("L_Elbow", "L_Hand"),         ("lowerarm_l", "hand_l")),
    ("大臂R",   ("R_Shoulder", "R_Elbow"),     ("upperarm_r", "lowerarm_r")),
    ("小臂R",   ("R_Elbow", "R_Hand"),         ("lowerarm_r", "hand_r")),
    ("锁骨L",   ("Spine2", "L_Clavicle"),      ("spine_03", "clavicle_l")),
    ("锁骨R",   ("Spine2", "R_Clavicle"),      ("spine_03", "clavicle_r")),
    ("躯干",    ("Spine1", "Spine2"),          ("spine_01", "spine_02")),
    ("颈",      ("Spine2", "Neck"),            ("spine_03", "neck_01")),
    ("头",      ("Neck", "Head"),              ("neck_01", "head")),
]

PAIRS = [
    ("idle1",
     "/Game/Character/Darius/LOL_Source/SK_LOL_Dariusskinned_mesh_darius_skin15_idle1",
     TGT_DIR + "/A_Darius_idle1"),
    ("run",
     "/Game/Character/Darius/LOL_Source/SK_LOL_Dariusskinned_mesh_darius_skin15_run",
     TGT_DIR + "/A_Darius_run"),
]

# ==================================================================== twist 判据
# 🔴 为什么必须另加这一组：`dir(父→子)` **对「绕骨轴自转」天生免疫**
#    （子骨沿父骨轴偏移，绕该轴转它不动）。实测两组 `thigh_l` 偏移差 30° 却都给出 0.01°。
#    而用户抱怨的正是「手脚**拧**」⇒ 原判据看不见主诉。
#
# 两条互补的、**只用关节坐标**的 twist 观测量（符合 AGENTS.md §0.3）：
#
#  A. **关节面法线**（3 骨 p→m→c）：`n = normalize(cross(dir(p→m), dir(m→c)))`
#     绕 m 的骨轴自转不改 `dir(p→m)`，但会转动 `dir(m→c)` ⇒ `n` 跟着转。
#     ⇒ 直接捕捉**中间那根骨**的自转。
#     ⚠️ 两段共线时（直腿/直臂）`n` 退化，用 `|sin|` 判有效性并跳过。
#
#  B. **末梢方向**（2 骨）：脚掌/手掌的朝向本身垂直于上游骨轴 ⇒
#     上游整条链的自转都会体现在它身上，且**不会退化**。
TWIST_PLANE = [
    ("膝面L", ("L_Hip", "L_KneeLower", "L_Foot"),      ("thigh_l", "calf_l", "foot_l")),
    ("膝面R", ("R_Hip", "R_KneeLower", "R_Foot"),      ("thigh_r", "calf_r", "foot_r")),
    ("肘面L", ("L_Shoulder", "L_Elbow", "L_Hand"),     ("upperarm_l", "lowerarm_l", "hand_l")),
    ("肘面R", ("R_Shoulder", "R_Elbow", "R_Hand"),     ("upperarm_r", "lowerarm_r", "hand_r")),
    ("颈面",  ("Spine2", "Neck", "Head"),              ("spine_03", "neck_01", "head")),
]
TWIST_DIR = [
    ("脚L", ("L_Foot", "L_Toe"),      ("foot_l", "ball_l")),
    ("脚R", ("R_Foot", "R_Toe"),      ("foot_r", "ball_r")),
    ("手L", ("L_Hand", "L_Middle1"),  ("hand_l", "middle_01_l")),
    ("手R", ("R_Hand", "R_Middle1"),  ("hand_r", "middle_01_r")),
]
# 退化门限：两段夹角的正弦小于此值就认为法线不可信（≈ 2.9°）
DEGEN_SIN = 0.05


class Sampler:
    """把一条动画的局部变换**一次性取完**，之后 FK 全在 Python 里算。

    关键：`find_bone_path_to_root` 只调一次/骨，并立刻 `str()` 化，避免长期持有
    资产内部的 FName 数组（那是崩溃根因）。
    """

    def __init__(self, anim, tag):
        self.anim = anim
        self.tag = tag
        self.path = {}
        self.local = {}
        need = set()
        for _, (sp, sc), (tp, tc) in SEGMENTS:
            need.add(sp)
            need.add(sc)
            need.add(tp)
            need.add(tc)
        for _, (sp, sm, sc), (tp, tm, tc) in TWIST_PLANE:
            need.update((sp, sm, sc, tp, tm, tc))
        for _, (sp, sc), (tp, tc) in TWIST_DIR:
            need.update((sp, sc, tp, tc))
        self.need = need
        # 路径：一次性
        for b in need:
            try:
                self.path[b] = [str(x) for x in AL.find_bone_path_to_root(anim, b)][::-1]
            except Exception as ex:
                LW("   [%s] 取 %s 路径失败: %s" % (tag, b, str(ex)[:80]))
                self.path[b] = []
        # 需要的骨 = 所有路径的并集
        bones = set()
        for p in self.path.values():
            bones.update(p)
        self.bones = sorted(bones)
        n = int(AL.get_num_frames(anim))
        step = max(1, n // N_SAMPLES)
        self.frames = list(range(0, n, step))
        # 局部变换：一次性
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
        self.n_bones = len(self.bones)

    def pos(self, bone, frame):
        """含缩放逐级复合，返回该骨在组件空间的坐标（cm）。纯 Python。"""
        chain = self.path.get(bone) or []
        p, q, s = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0)
        for bn in chain:
            tr = self.local[frame].get(bn)
            if tr is None:
                continue
            t, bq, bs = tr
            sc = (t[0] * s[0], t[1] * s[1], t[2] * s[2])
            off = mv(qmat(q), sc)
            p = (p[0] + off[0], p[1] + off[1], p[2] + off[2])
            q = qmul(q, bq)
            s = (s[0] * bs[0], s[1] * bs[1], s[2] * bs[2])
        return p

    def dir_of(self, parent, child, frame):
        return norm(sub(self.pos(child, frame), self.pos(parent, frame)))

    def plane(self, a, b, c, frame):
        """关节面法线 + 有效性。返回 (单位法线, |sin|)。|sin| 小 ⇒ 退化不可信。"""
        u = self.dir_of(a, b, frame)
        v = self.dir_of(b, c, frame)
        cr = (u[1] * v[2] - u[2] * v[1],
              u[2] * v[0] - u[0] * v[2],
              u[0] * v[1] - u[1] * v[0])
        mag = (cr[0] ** 2 + cr[1] ** 2 + cr[2] ** 2) ** 0.5
        return norm(cr), mag


L("=== 判据：同一时刻，源与目标的「关节连线方向」夹角（度）===")
L("    G1 门限：均值 < 8° ，P90 < 20° ，max < 35°")
for tag, src_p, tgt_p in PAIRS:
    sa = eal.load_asset(src_p)
    ta = eal.load_asset(tgt_p)
    if sa is None or ta is None:
        LW("  %s 加载失败（%s / %s）" % (tag, src_p.split("/")[-1], tgt_p.split("/")[-1]))
        continue
    ss = Sampler(sa, "src")
    ts = Sampler(ta, "tgt")
    n = min(ss.n_frames, ts.n_frames)
    frames = [f for f in ss.frames if f < n]
    L("")
    L("################ %s（源 %d 帧 / 目标 %d 帧，抽样 %d 帧，源骨 %d / 目标骨 %d）"
      % (tag, ss.n_frames, ts.n_frames, len(frames), ss.n_bones, ts.n_bones))
    L("    %-10s %8s %8s %8s" % ("段", "均值", "最大", "P90"))
    worst = []
    for name, (sp, sc), (tp, tc) in SEGMENTS:
        vals = []
        for f in frames:
            try:
                vals.append(angle(ss.dir_of(sp, sc, f), ts.dir_of(tp, tc, f)))
            except Exception:
                pass
        if not vals:
            L("    %-10s <采样失败>" % name)
            continue
        vals.sort()
        mean = sum(vals) / len(vals)
        p90 = vals[min(len(vals) - 1, int(len(vals) * 0.9))]
        mx = vals[-1]
        flag = "  <<< 超门限" if (mean > 8.0 or mx > 35.0) else ""
        L("    %-10s %8.2f %8.2f %8.2f%s" % (name, mean, mx, p90, flag))
        worst.append((mean, name))
    if worst:
        worst.sort(reverse=True)
        L("    → 最差三段：%s" % ", ".join("%s %.1f°" % (nm, m) for m, nm in worst[:3]))

    # ---------------------------------------------------------- twist 组
    L("")
    L("    ---- twist 判据（原判据对「绕骨轴自转」免疫，见本文件注释）----")
    L("    %-8s %8s %8s %8s  %s" % ("量", "均值", "最大", "P90", "有效帧"))
    for name, (sp, sm, sc), (tp, tm, tc) in TWIST_PLANE:
        vals, n_valid, n_all = [], 0, 0
        for f in frames:
            n_all += 1
            try:
                ns, ms = ss.plane(sp, sm, sc, f)
                nt, mt = ts.plane(tp, tm, tc, f)
            except Exception:
                continue
            if ms < DEGEN_SIN or mt < DEGEN_SIN:
                continue
            n_valid += 1
            vals.append(angle(ns, nt))
        if not vals:
            L("    %-8s %8s  （全部退化，法线不可信）" % (name, "-"))
            continue
        vals.sort()
        mean = sum(vals) / len(vals)
        p90 = vals[min(len(vals) - 1, int(len(vals) * 0.9))]
        flag = "  <<< 超门限" if (mean > 8.0 or vals[-1] > 35.0) else ""
        L("    %-8s %8.2f %8.2f %8.2f  %d/%d%s"
          % (name, mean, vals[-1], p90, n_valid, n_all, flag))
    for name, (sp, sc), (tp, tc) in TWIST_DIR:
        vals = []
        for f in frames:
            try:
                vals.append(angle(ss.dir_of(sp, sc, f), ts.dir_of(tp, tc, f)))
            except Exception:
                pass
        if not vals:
            L("    %-8s <采样失败>" % name)
            continue
        vals.sort()
        mean = sum(vals) / len(vals)
        p90 = vals[min(len(vals) - 1, int(len(vals) * 0.9))]
        flag = "  <<< 超门限" if (mean > 8.0 or vals[-1] > 35.0) else ""
        L("    %-8s %8.2f %8.2f %8.2f  %d/%d%s"
          % (name, mean, vals[-1], p90, len(vals), len(frames), flag))
L("=== DONE ===")
