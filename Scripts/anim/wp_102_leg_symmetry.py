# -*- coding: utf-8 -*-
"""wp_102_leg_symmetry.py —— 只读：量「左右腿对称性」，定位「深一脚浅一脚」

现象：走路时左右步幅/抬腿高度不一致 ⇒ 观感「深一脚浅一脚」。

判据
----
同一根脚骨（ball / toe / foot）左右两侧的 **Z 摆幅之比**：
    源 A_LOL_Darius_run 实测 0.92（≈1 即对称）
    A_Darius_run 实测     1.44 ~ 1.77（左腿比右腿多迈 50~77%）

本脚本把 LOL_Retarget 下所有 run 系产物 + M1 基准都测一遍，
顺便给出 pelvis 峰峰（跳动感）与支撑脚中位（浮空），一张表看全，
用来挑「哪条素材最适合当走路」。

跑法：
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_102_leg_symmetry.py
"""
import json
import statistics

import unreal

APE = unreal.AnimPoseExtensions
AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary
L = unreal.log
OPTS = unreal.AnimPoseEvaluationOptions()
OUT = "E:/UE/Fight/Saved/Attack/wp102_symmetry.json"

TGT_DIR = "/Game/Character/Darius/Animations/LOL_Retarget"
PREFIX = "A_Darius_run"
BASE = [
    ("★基准 AxeWalk(M1)", "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Layered"),
    ("★基准 Walk(M1)", "/Game/Character/Darius/Anims/A_Darius_Walk_Layered"),
]
PAIRS = (("ball_l", "ball_r"), ("toe_l", "toe_r"), ("foot_l", "foot_r"))
FEET = ("ball_l", "ball_r", "toe_l", "toe_r", "foot_l", "foot_r")


def z(pose, b):
    return APE.get_bone_pose(pose, unreal.Name(b), unreal.AnimPoseSpaces.WORLD).translation.z


def measure(path, tag):
    a = unreal.load_object(None, path)
    if a is None:
        return None
    nf = AL.get_num_frames(a)
    cols = {b: [] for b in FEET}
    pel, sup = [], []
    for f in range(nf + 1):
        try:
            p = APE.get_anim_pose_at_frame(a, f, OPTS)
        except Exception:
            continue
        row = {}
        for b in FEET:
            try:
                v = z(p, b)
                cols[b].append(v)
                row[b] = v
            except Exception:
                pass
        try:
            pel.append(z(p, "pelvis"))
        except Exception:
            pass
        if row:
            sup.append(min(row.values()))
    if not sup:
        return None
    sym = {}
    for l, r in PAIRS:
        vl, vr = cols.get(l), cols.get(r)
        if not vl or not vr:
            continue
        rl = max(vl) - min(vl)
        rr = max(vr) - min(vr)
        sym[l[:-2]] = {"left": round(rl, 2), "right": round(rr, 2),
                       "ratio": round(rl / rr, 3) if rr > 0.01 else None}
    rec = {"tag": tag, "asset": path.rsplit("/", 1)[-1], "frames": nf,
           "symmetry": sym,
           "pelvis_p2p": round(max(pel) - min(pel), 2) if pel else None,
           "support_med": round(statistics.median(sup), 2),
           "support_min": round(min(sup), 2), "support_max": round(max(sup), 2)}
    return rec


R = {"cases": []}
L("=" * 108)
L("=== 左右腿对称性 / 跳动 / 浮空   （ratio 越接近 1 越对称；源 run 实测 0.92）===")
L("=" * 108)
L("%-24s %6s %10s %10s %10s %8s %8s %8s" % (
    "动画", "帧", "ball 左/右", "toe 左/右", "foot 左/右", "pelvis峰峰", "支撑脚中位", "支撑脚范围"))

for tag, path in BASE:
    r = measure(path, tag)
    if r:
        R["cases"].append(r)
for p in sorted(eal.list_assets(TGT_DIR, recursive=False, include_folder=False)):
    a = unreal.load_object(None, p)
    if not isinstance(a, unreal.AnimSequence) or not a.get_name().startswith(PREFIX):
        continue
    r = measure(p, a.get_name())
    if r:
        R["cases"].append(r)

for r in R["cases"]:
    s = r["symmetry"]
    def fmt(k):
        d = s.get(k)
        return "%5.1f/%5.1f(%.2f)" % (d["left"], d["right"], d["ratio"]) if d else "      -     "
    L("%-24s %6d %-10s %-10s %-10s %8.2f %8.2f %4.1f~%.1f" % (
        r["tag"], r["frames"], fmt("ball"), fmt("toe"), fmt("foot"),
        r["pelvis_p2p"], r["support_med"], r["support_min"], r["support_max"]))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(R, f, ensure_ascii=False, indent=1)
L("")
L("已写 %s" % OUT)
L("WP102_DONE")
