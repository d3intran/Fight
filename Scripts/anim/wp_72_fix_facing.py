# -*- coding: utf-8 -*-
"""wp_72 —— 把 LoL 线产物的整体朝向转回目标骨架的「前方」，修「背对玩家」。

诊断（`wp_71_axis_facing.py` 实测，pelvis 局部 X 轴在世界空间的方向）
--------------------------------------------------------------------
    目标骨架正常前方（原生 jump/walk 系 + Mixamo 线）  X轴 ≈ (0.00, -0.99, +0.12)  三者完全一致
    LoL 线产物（idle1 / run / attack1）                 X轴 ≈ (+0.5, +0.8, ...)     朝 +Y

⇒ 重定向把源的 +X 转成了 +Y（本应转 -Y），**整体多转了 180°**。
根因 = `mirror` 配方里给源 Root 施加的「世界空间 yaw180」在解决左右镜像的同时把整体朝向转反了。

修法
----
给产物的 `root` 骨写一条恒定的「绕世界 Z 转 180°」旋转轨（局部化到 root 的父坐标系）：

    q_new = Q_outer_rest⁻¹ ∘ Rz180 ∘ Q_outer_rest ∘ q_root_old

- `root` 的父是最外层骨（rest 位置 0）⇒ **绕脚下转**，脚不离地；
- root 的位置/缩放原样保留（若存在逐帧位移轨，逐帧读回）。
- `weapon_jnt_l` 的烘焙轨是相对 `hand_l` 的**相对量**，不受整体转向影响。

默认 dry-run；要写资产把 `Saved/Attack/wp72_mode.txt` 写成 apply。

跑法：
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_72_fix_facing.py
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

MODE_FILE = "E:/UE/Fight/Saved/Attack/wp72_mode.txt"
TGT_DIR = "/Game/Character/Darius/Animations/LOL_Retarget"
OUTER = "darius_godking_mesh_LOD0_Skeleton"
ROOT = "root"
REPORT = "E:/UE/Fight/Saved/Attack/wp72_facing_fix.json"
RZ180 = (0.0, 0.0, 1.0, 0.0)


def mode():
    try:
        with open(MODE_FILE, encoding="utf-8") as f:
            return f.read().strip().lower()
    except Exception:
        return "dry"


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)


def qconj(q):
    return (-q[0], -q[1], -q[2], q[3])


def qnorm(q):
    n = math.sqrt(sum(c * c for c in q))
    return tuple(c / n for c in q) if n > 1e-12 else (0.0, 0.0, 0.0, 1.0)


def qrot(q, v):
    x, y, z, w = q
    m = ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
         (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
         (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def quat_of(r):
    return qnorm((r.x, r.y, r.z, r.w))


def flat(v):
    n = math.sqrt(v[0] ** 2 + v[1] ** 2)
    return (v[0] / n, v[1] / n, 0.0) if n > 1e-6 else (1.0, 0.0, 0.0)


L("=" * 88)
L("=== wp_72 修 LoL 线产物整体朝向   mode=%s ===" % mode())
L("=" * 88)

asset_paths = sorted(str(x).split(".")[0] for x in
                     eal.list_assets(TGT_DIR, recursive=False, include_folder=False))
if not asset_paths:
    LW("!! %s 下没有资产" % TGT_DIR)
    raise SystemExit(1)

# 先确认最外层骨的 rest 世界旋转（无父，局部即世界）
probe = eal.load_asset(asset_paths[0])
qo = quat_of(AL.get_bone_pose_for_frame(probe, unreal.Name(OUTER), 0, False).rotation)
off = qmul(qconj(qo), qmul(RZ180, qo))          # 要叠加到 root 局部上的旋转
L("   最外层骨 rest 四元数 Q_outer = (%.4f, %.4f, %.4f, %.4f)" % qo)
L("   叠加到 root 的局部旋转 off    = (%.4f, %.4f, %.4f, %.4f)" % off)
L("   预计 root 的 X 轴由 %s 转为 %s" % (
    tuple(round(c, 3) for c in flat(qrot(qo, (1.0, 0.0, 0.0)))),
    tuple(round(c, 3) for c in flat(qrot(qmul(qo, off), (1.0, 0.0, 0.0))))))

report = {"mode": mode(), "count": 0, "items": []}
applied = 0
for p in asset_paths:
    a = eal.load_asset(p)
    if a is None:
        continue
    tag = p.rsplit("/", 1)[-1]
    nf = AL.get_num_frames(a)
    locs, rots, scls = [], [], []
    for f in range(nf + 1):
        try:
            t = AL.get_bone_pose_for_frame(a, unreal.Name(ROOT), f, False)
        except Exception:
            break
        locs.append((t.translation.x, t.translation.y, t.translation.z))
        scls.append((t.scale3d.x, t.scale3d.y, t.scale3d.z))
        rots.append(qnorm(qmul(off, quat_of(t.rotation))))
    if not locs:
        LW("   %s 读 root 失败，跳过" % tag)
        continue
    report["count"] += 1
    report["items"].append({"asset": tag, "keys": len(locs),
                            "root_rot_before_f0": [round(c, 5) for c in quat_of(
                                AL.get_bone_pose_for_frame(a, unreal.Name(ROOT), 0, False).rotation)],
                            "root_rot_after_f0": [round(c, 5) for c in rots[0]]})
    if mode() != "apply":
        continue
    ctrl = a.get_editor_property("controller")
    try:
        names = [str(x) for x in
                 a.get_editor_property("data_model_interface").get_bone_track_names()]
        if ROOT not in names:
            ctrl.add_bone_track(ROOT, False)
    except Exception as ex:
        LW("   %s add_bone_track 警告: %s" % (tag, str(ex)[:60]))
    ok = ctrl.set_bone_track_keys(
        ROOT,
        [unreal.Vector(*v) for v in locs],
        [unreal.Quat(v[0], v[1], v[2], v[3]) for v in rots],
        [unreal.Vector(*v) for v in scls],
        False)
    if ok:
        eal.save_asset(p, only_if_is_dirty=False)
        applied += 1

L("")
L("   待处理 %d 条；已写入 %d 条" % (report["count"], applied))
if mode() != "apply":
    L("==> DRY-RUN，未写资产。确认上面 off 与预期朝向后再把 %s 写成 apply。" % MODE_FILE)
else:
    L("==> 已写入。复验：ue_remote.py Scripts/anim/wp_71_axis_facing.py（LoL 线 X 轴应变成 ~(0,-1,0)）")

with open(REPORT, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=1, ensure_ascii=False, default=str)
L("已写 %s" % REPORT)
L("WP72_DONE")
