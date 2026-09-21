# -*- coding: utf-8 -*-
"""rtg_30_weapon_scan —— 只读：扫描全部 LOL 源片段，量 `Weapon` 骨相对 `R_Hand` 是否刚性跟随。

判定「斧头继续挂 hand_rSocket」是否无损：若所有片段里 Weapon 相对 R_Hand 的局部位移/旋转都恒定，
说明源动画的握法本身就是常量，socket 方案即无损。
"""

import unreal
import math

L = unreal.log
LW = unreal.log_warning
APE = unreal.AnimPoseExtensions
DIR = "/Game/Character/Darius/LOL_Source"


def qmul(a, b):
    return (a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1],
            a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0],
            a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3],
            a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2])


def qconj(q):
    return (-q[0], -q[1], -q[2], q[3])


def qrot(q, v):
    qv = qmul(qmul(q, (v[0], v[1], v[2], 0.0)), qconj(q))
    return (qv[0], qv[1], qv[2])


def qang(a, b):
    d = abs(a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3])
    d = min(1.0, max(-1.0, d))
    return math.degrees(2.0 * math.acos(d))


eal = unreal.EditorAssetLibrary
assets = eal.list_assets(DIR, recursive=False, include_folder=False)
clips = sorted({str(a).split(".")[0] for a in assets if "A_LOL_Darius_" in str(a) and "BindPose" not in str(a)})
L(f"[WPN] 待扫片段 {len(clips)} 个")

opts = unreal.AnimPoseEvaluationOptions()
rows = []
for p in clips:
    a = unreal.load_object(None, p)
    if not a:
        continue
    try:
        keys = a.get_editor_property("number_of_sampled_keys")
    except Exception:
        continue
    if keys is None or keys < 2:
        continue
    frames = sorted({int(round(i * (keys - 1) / 5.0)) for i in range(6)})
    base_R = None
    base_T = None
    dpos = 0.0
    dang = 0.0
    dist_min, dist_max = 1e9, -1e9
    for f in frames:
        try:
            pose = APE.get_anim_pose_at_frame(a, f, opts)
            th = APE.get_bone_pose(pose, unreal.Name("R_Hand"), unreal.AnimPoseSpaces.WORLD)
            tw = APE.get_bone_pose(pose, unreal.Name("Weapon"), unreal.AnimPoseSpaces.WORLD)
        except Exception as ex:
            LW(f"[WPN] {p} frame {f} err {ex}")
            continue
        qh = (th.rotation.x, th.rotation.y, th.rotation.z, th.rotation.w)
        qw = (tw.rotation.x, tw.rotation.y, tw.rotation.z, tw.rotation.w)
        dv = (tw.translation.x - th.translation.x,
              tw.translation.y - th.translation.y,
              tw.translation.z - th.translation.z)
        dist = math.sqrt(dv[0] ** 2 + dv[1] ** 2 + dv[2] ** 2)
        dist_min = min(dist_min, dist)
        dist_max = max(dist_max, dist)
        rel_R = qmul(qconj(qh), qw)
        rel_T = qrot(qconj(qh), dv)
        if base_R is None:
            base_R, base_T = rel_R, rel_T
        else:
            dang = max(dang, qang(base_R, rel_R))
            dpos = max(dpos, math.sqrt(sum((rel_T[i] - base_T[i]) ** 2 for i in range(3))))
    if base_R is None:
        continue
    rows.append((p.split("/")[-1], keys, dist_min, dist_max, dpos, dang))
    L(f"[WPN] {p.split('/')[-1]:<34} keys={keys:<4} |W-R|={dist_min:7.2f}~{dist_max:7.2f}cm  "
      f"手内相对位移漂移={dpos:7.3f}cm  相对旋转漂移={dang:7.3f}°")

bad = [r for r in rows if r[4] > 0.5 or r[5] > 0.5]
L(f"[WPN] 扫描完成 {len(rows)} 个片段；相对 R_Hand 漂移 >0.5cm 或 >0.5° 的有 {len(bad)} 个")
for r in bad:
    L(f"[WPN]   [漂移] {r[0]:<34} dpos={r[4]:.3f}cm dang={r[5]:.3f}°")
L("WPN_SCAN_DONE")
