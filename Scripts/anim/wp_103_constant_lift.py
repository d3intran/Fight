# -*- coding: utf-8 -*-
"""
wp_103_constant_lift.py —— run 系动画的「恒定」落地抬升（中位数对齐，不破坏对称性）

为什么不用 wp_97 的逐帧吸附
--------------------------
逐帧 root 平移会**同时**移动两只脚：把较低那只压到地面时，较高的那只被抬得更高
⇒ 摆幅被放大、左右对称性被破坏（实测 run toe 从 1.16 恶化到 1.92）。
恒定平移不改变摆幅、不影响对称性；个别帧的穿地/悬空交给后续 Foot IK（思路 C）解决。

逻辑
----
· 首次运行：把当前 root 逐帧局部 Z 存进 baseline（`wp103_baseline.json`），此后幂等。
· 计算 `off = TARGET_MID − median(支撑脚)`，支撑脚 = 每帧两脚中较低者（cm，WORLD）。
· 写 `root.local_z = baseline_z + off × 0.01`（骨骼局部是米，WORLD 是 cm）。

模式：Saved/Attack/wp103_mode.txt → dry（默认）/ apply / reset
TARGET_MID 默认 10.0 cm（M1 基准 AxeWalk 支撑脚中位 14.24、最低 10.45，取 10 略贴地）。

跑法：
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_103_constant_lift.py
"""
import json
import statistics

import unreal

APE = unreal.AnimPoseExtensions
AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary
L = unreal.log
LW = unreal.log_warning
OPTS = unreal.AnimPoseEvaluationOptions()

MODE_FILE = "E:/UE/Fight/Saved/Attack/wp103_mode.txt"
BASELINE = "E:/UE/Fight/Saved/Attack/wp103_baseline.json"
OUT = "E:/UE/Fight/Saved/Attack/wp103_lift.json"
TGT_DIR = "/Game/Character/Darius/Animations/LOL_Retarget"
PREFIX = "A_Darius_run"
ROOT = "root"
FOOT_HINT = ("toe", "ball", "foot")
TARGET_MID = 10.0
UNIT = 0.01


def mode():
    try:
        return open(MODE_FILE, encoding="utf-8").read().strip().lower() or "dry"
    except Exception:
        return "dry"


def wz(pose, b):
    return APE.get_bone_pose(pose, unreal.Name(b), unreal.AnimPoseSpaces.WORLD).translation.z


try:
    with open(BASELINE, encoding="utf-8") as f:
        baseline = json.load(f)
except Exception:
    baseline = {}

ACTION = mode()
L("=" * 96)
L("=== wp_103 恒定抬升（中位数对齐 %.1f cm）  mode=%s ===" % (TARGET_MID, ACTION))
L("=" * 96)

report = {"mode": ACTION, "target_mid": TARGET_MID, "items": []}
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
    feet = [b for b in bones if any(k in b.lower() for k in FOOT_HINT)]
    if not feet:
        LW("   %-30s 无脚骨，跳过" % nm)
        continue
    nf = AL.get_num_frames(a)
    n = nf + 1

    sup, root_z = [], []
    for f in range(n):
        try:
            pose = APE.get_anim_pose_at_frame(a, f, OPTS)
            row = [wz(pose, b) for b in feet if True]
            row = [v for v in row if v is not None]
            sup.append(min(row) if row else 0.0)
            t = AL.get_bone_pose_for_frame(a, unreal.Name(ROOT), f, False)
            root_z.append(t.translation.z)
        except Exception as ex:
            LW("   %s 帧%d 采样失败 %s" % (nm, f, str(ex)[:50]))
            sup = []
            break
    if not sup:
        continue

    if nm not in baseline:
        baseline[nm] = {"root_z": root_z}
        L("   %-30s baseline 已存（%d 帧）" % (nm, n))
    base_z = baseline[nm]["root_z"]
    if len(base_z) != n:
        LW("   %-30s baseline 帧数不符（%d vs %d），跳过" % (nm, len(base_z), n))
        continue

    med = statistics.median(sup)
    off = TARGET_MID - med
    item = {"asset": nm, "frames": n, "support_med": round(med, 2),
            "offset_cm": round(off, 2)}
    L("   %-30s 帧%-4d 支撑脚中位 %7.2f cm  ⇒ 恒定抬升 %+7.2f cm" % (nm, nf, med, off))
    report["items"].append(item)

    if ACTION == "reset":
        off = 0.0
    if ACTION == "dry":
        continue

    locs, rots, scls = [], [], []
    for f in range(n):
        t = AL.get_bone_pose_for_frame(a, unreal.Name(ROOT), f, False)
        locs.append(unreal.Vector(t.translation.x, t.translation.y,
                                  base_z[f] + off * UNIT))
        rots.append(unreal.Quat(t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w))
        scls.append(unreal.Vector(t.scale3d.x, t.scale3d.y, t.scale3d.z))
    ok = a.get_editor_property("controller").set_bone_track_keys(
        ROOT, locs, rots, scls, False)
    if ok:
        eal.save_asset(p, only_if_is_dirty=False)
        applied += 1
        item["written"] = True

with open(BASELINE, "w", encoding="utf-8") as f:
    json.dump(baseline, f, ensure_ascii=False)
L("")
L("   已写入 %d 条" % applied)
if ACTION == "dry":
    L("==> DRY-RUN。把 %s 写成 apply / reset" % MODE_FILE)
L("==> 复验：wp_102（对称度应回到 ~1.1~1.3）+ wp_94（支撑脚中位应 ≈ %.1f）" % TARGET_MID)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, default=str, indent=1)
L("已写 %s" % OUT)
L("WP103_DONE")
