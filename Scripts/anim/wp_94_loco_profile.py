# -*- coding: utf-8 -*-
"""wp_94_loco_profile.py —— 只读：逐帧全采样的「落地 + 起伏」剖面

回答两个问题：
  1. 「浮空」——支撑脚（两脚中较低那只）在整段动画里的高度分布。正常走路应贴近 0~3cm，
     若中位数远高于 0 就是整体被抬过头。
  2. 「跳动」——pelvis Z 的峰峰值 / 标准差，以及双脚同时离地（腾空）的帧占比。

基准对照：`A_Darius_Walk_Layered`（M1 已验收的走路）。

单位：`AnimPoseSpaces.WORLD` 平移读数 = cm。

跑法：
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_94_loco_profile.py
输出：Saved/Attack/wp94_profile.json
"""
import json
import statistics

import unreal

APE = unreal.AnimPoseExtensions
AL = unreal.AnimationLibrary
L = unreal.log
LW = unreal.log_warning
OPTS = unreal.AnimPoseEvaluationOptions()
OUT = "E:/UE/Fight/Saved/Attack/wp94_profile.json"

CASES = [
    ("基准 AxeWalk_Layered(M1)", "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Layered"),
    ("基准 Walk_Layered", "/Game/Character/Darius/Anims/A_Darius_Walk_Layered"),
    ("LoL idle1", "/Game/Character/Darius/Animations/LOL_Retarget/A_Darius_idle1"),
    ("LoL run", "/Game/Character/Darius/Animations/LOL_Retarget/A_Darius_run"),
    ("LoL run_fast", "/Game/Character/Darius/Animations/LOL_Retarget/A_Darius_run_fast"),
    ("LoL run_homeguard", "/Game/Character/Darius/Animations/LOL_Retarget/A_Darius_run_homeguard"),
]
# 只取这几根：脚（支撑判据）+ pelvis（起伏）
WANT = ("ball_l", "ball_r", "toe_l", "toe_r", "foot_l", "foot_r", "pelvis", "root",
        "calf_l", "calf_r", "thigh_l", "thigh_r")


def wpos(pose, b):
    t = APE.get_bone_pose(pose, unreal.Name(b), unreal.AnimPoseSpaces.WORLD)
    return (t.translation.x, t.translation.y, t.translation.z)


def profile(path, tag):
    a = unreal.load_object(None, path)
    if a is None:
        LW("   载不到 %s" % path)
        return None
    nf = AL.get_num_frames(a)
    try:
        bones = [str(x) for x in
                 a.get_editor_property("data_model_interface").get_bone_track_names()]
    except Exception:
        bones = []
    have = [b for b in WANT if b in bones]
    feet = [b for b in have if b.startswith(("ball", "toe", "foot"))]
    rec = {"tag": tag, "asset": path.rsplit("/", 1)[-1], "frames": nf,
           "feet_bones": feet, "rows": []}
    for f in range(nf + 1):
        try:
            pose = APE.get_anim_pose_at_frame(a, f, OPTS)
        except Exception:
            continue
        row = {"f": f}
        for b in have:
            try:
                row[b] = round(wpos(pose, b)[2], 2)
            except Exception:
                pass
        rec["rows"].append(row)

    rows = rec["rows"]
    if not rows:
        LW("   %s 无有效帧" % tag)
        return None

    def col(k):
        return [r[k] for r in rows if k in r]

    # 支撑脚 = 每帧两脚里较低的那只（按骨名成对取）
    sup = []
    for r in rows:
        cand = [r[b] for b in feet if b in r]
        if cand:
            sup.append(min(cand))
    pel = col("pelvis")

    rec["support"] = {
        "min": round(min(sup), 2), "p25": round(statistics.quantiles(sup, n=4)[0], 2),
        "median": round(statistics.median(sup), 2),
        "p75": round(statistics.quantiles(sup, n=4)[2], 2),
        "max": round(max(sup), 2),
        "mean": round(statistics.mean(sup), 2),
    } if len(sup) >= 4 else None
    rec["pelvis"] = {
        "min": round(min(pel), 2), "max": round(max(pel), 2),
        "range": round(max(pel) - min(pel), 2),
        "std": round(statistics.pstdev(pel), 2),
    } if pel else None
    # 腾空：支撑脚 > 5cm 的帧占比
    rec["air_ratio"] = round(sum(1 for v in sup if v > 5.0) / len(sup), 3) if sup else None
    # 单脚离地高度（抬腿幅度）
    for b in feet:
        v = col(b)
        if v:
            rec.setdefault("feet", {})[b] = {"min": round(min(v), 2), "max": round(max(v), 2)}

    L("   %-26s %-22s 帧%-4d 脚骨=%s" % (tag, rec["asset"], nf, feet))
    if rec["support"]:
        s = rec["support"]
        L("        支撑脚 Z : min %7.2f | p25 %7.2f | 中位 %7.2f | p75 %7.2f | max %7.2f cm" % (
            s["min"], s["p25"], s["median"], s["p75"], s["max"]))
    if rec["pelvis"]:
        p = rec["pelvis"]
        L("        pelvis Z : %7.2f ~ %7.2f cm   峰峰 %6.2f cm   标准差 %5.2f" % (
            p["min"], p["max"], p["range"], p["std"]))
    if rec["air_ratio"] is not None:
        L("        腾空占比 : %.1f%%（支撑脚 > 5cm 的帧）" % (rec["air_ratio"] * 100))
    for b, v in (rec.get("feet") or {}).items():
        L("        %-10s : %7.2f ~ %7.2f cm" % (b, v["min"], v["max"]))
    return rec


R = {"cases": []}
L("=" * 92)
L("=== 逐帧落地/起伏剖面（cm；支撑脚 = 每帧两脚中较低者）===")
L("=" * 92)
for tag, path in CASES:
    got = profile(path, tag)
    if got:
        R["cases"].append(got)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(R, f, ensure_ascii=False, default=str)
L("")
L("已写 %s" % OUT)
L("WP94_DONE")
