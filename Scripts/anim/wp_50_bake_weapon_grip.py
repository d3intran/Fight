# -*- coding: utf-8 -*-
"""wp_50 —— 离线烘焙 `weapon_jnt_l` 的握法轨：绕开 RTG，直接对标源 LoL 动画。

为什么不用 RTG
--------------
RTG 的 FK op 的 `chains_to_retarget` 里**没有** Weapon 链，改链后重跑，
`weapon_jnt_l` 平移与旋转全为 0（完全没被驱动）。与其去找同步 API，不如直接用源数据烘焙。

数学（全部在「目标手局部系」里表达，避免坐标系换算）
----------------------------------------------------
    L_grip(t) = W_R_Hand_src(t)⁻¹ ∘ W_Weapon_src(t)      # 源：斧头在右手系里的位姿（含握法变化）
    K         = W_hand_l_tgt(t₀)⁻¹ ∘ W_R_Hand_src(t₀)      # 手系对齐常量（参考帧 t₀=0）
    L_raw(t)  = K ∘ L_grip(t)                             # 「斧头在目标手系里」的位姿
    D(t)      = L_raw(t₀)⁻¹ ∘ L_raw(t)                     # 相对参考帧的握持增量
    L_jnt(t)  = rest_l ∘ D(t)                             # 写进 weapon_jnt_l 的局部键

⇒ t₀ 时刻 L_jnt = rest_l（锚点停在原始位置，不破坏装配契约），其余帧带上源的握法变化。
⚠️ 单位：WORLD 读数 = cm，骨骼 local = 米 ⇒ D 的平移增量要 ×0.01（实测，见 wp_45 记录）。

配对（帧数逐一相等）
-------------------
    A_LOL_Darius_idle1          <-> Animations/LOL_Retarget_Test/A_Darius_idle1     (65/65)
    A_LOL_Darius_run            <-> Animations/LOL_Retarget_Test/A_Darius_run       (35/35)
    A_LOL_Darius_attack1        <-> Anims/A_Darius_Attack1_LOL                      (73/73)
    A_LOL_Darius_attack1_toidle <-> Anims/A_Darius_Attack1_ToIdle_LOL               (58/58)

跑法：
    uv run --no-project python Scripts/ue_remote.py Scripts/anim/wp_50_bake_weapon_grip.py
    （默认 dry-run；要写资产把 Saved/Attack/wp50_mode.txt 写成 apply）
"""
import json
import math
import os
import shutil
import time

import unreal

APE = unreal.AnimPoseExtensions
AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary
L = unreal.log
LW = unreal.log_warning

MODE_FILE = "E:/UE/Fight/Saved/Attack/wp50_mode.txt"
OUT = "E:/UE/Fight/Saved/Attack/wp50_bake_report.json"
BACKUP_ROOT = "E:/UE/Fight/Saved/Attack"
CONTENT_ROOT = "E:/UE/Fight/Content"
OPTS = unreal.AnimPoseEvaluationOptions()

SRC_HAND, SRC_WEAPON = "R_Hand", "Weapon"
TGT_HAND, TGT_ANCHOR = "hand_l", "weapon_jnt_l"
UNIT_WORLD_TO_LOCAL = 0.01

SRC_DIR = "/Game/Character/Darius/LOL_Source"
TGT_DIR = "/Game/Character/Darius/Animations/LOL_Retarget"
SRC_PREFIX = "A_LOL_Darius_"
TGT_PREFIX = "A_Darius_"


def build_pairs():
    """目标 A_Darius_<x> ← 源 A_LOL_Darius_<x>（自动配对；帧数在循环里逐一核对）"""
    out = []
    try:
        listing = sorted(eal.list_assets(TGT_DIR, recursive=False, include_folder=False))
    except Exception as ex:
        LW("扫描 %s 失败: %s" % (TGT_DIR, ex))
        return []
    for p in listing:
        nm = p.rsplit("/", 1)[-1].split(".")[0]
        if not nm.startswith(TGT_PREFIX):
            continue
        src = "%s/%s%s" % (SRC_DIR, SRC_PREFIX, nm[len(TGT_PREFIX):])
        if eal.does_asset_exist(src):
            out.append((src, p))
        else:
            LW("   无源对应，跳过: %s" % nm)
    return out


PAIRS = build_pairs()


# ---------------- 带缩放的 TRS 复合 ----------------
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


def compose(A, B):
    """A ∘ B（A 为父）。UE 规则：P = P_A + Q_A·(t_B · S_A)；S = S_A · S_B"""
    ra, la, sa = A
    rb, lb, sb = B
    r = qrot(ra, tuple(lb[i] * sa[i] for i in range(3)))
    return (qmul(ra, rb), tuple(la[i] + r[i] for i in range(3)),
            tuple(sa[i] * sb[i] for i in range(3)))


def inverse(A):
    r, l, s = A
    qi = qconj(qnorm(r))
    si = tuple(1.0 / c for c in s)
    return (qi, qrot(qi, tuple(-l[i] * si[i] for i in range(3))), si)


def tq(t):
    return (qnorm((t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w)),
            (t.translation.x, t.translation.y, t.translation.z),
            (t.scale3d.x, t.scale3d.y, t.scale3d.z))


def mag(v):
    return math.sqrt(sum(c * c for c in v))


def qang(a, b):
    d = min(1.0, abs(sum(a[i] * b[i] for i in range(4))))
    return math.degrees(2.0 * math.acos(d))


def mode():
    try:
        with open(MODE_FILE, encoding="utf-8") as f:
            return f.read().strip().lower()
    except Exception:
        return "dry"


L("=" * 78)
L("=== wp_50 烘焙 weapon_jnt_l 握法轨   mode=%s ===" % mode())
L("=" * 78)

local_of = {}
report = {"mode": mode(), "pairs": []}

for src_path, tgt_path in PAIRS:
    src = unreal.load_object(None, src_path)
    tgt = unreal.load_object(None, tgt_path)
    if src is None or tgt is None:
        LW("   !! 载不到 %s 或 %s" % (src_path, tgt_path))
        continue
    nf_s, nf_t = AL.get_num_frames(src), AL.get_num_frames(tgt)
    n = min(nf_s, nf_t)
    tag = tgt.get_name()
    L("")
    L("--- %s  源帧=%d 目标帧=%d 取 %d ---" % (tag, nf_s, nf_t, n))

    # ⚠️ 必须先清掉已有轨道：否则读到的 f0 是上次烘焙值，会复合污染（wp_12 踩过同类坑）
    try:
        c0 = tgt.get_editor_property("controller")
        nm0 = [str(x) for x in c0.get_model_interface().get_bone_track_names()]
        if TGT_ANCHOR in nm0:
            c0.remove_bone_track(TGT_ANCHOR)
            eal.save_asset(tgt_path, only_if_is_dirty=False)
            L("   已清除旧 %s 轨道（避免复合污染）" % TGT_ANCHOR)
    except Exception as ex:
        LW("   清轨失败: %s" % str(ex)[:60])
    # rest 局部（无轨时为真正的 rest）
    rest_l = tq(AL.get_bone_pose_for_frame(tgt, unreal.Name(TGT_ANCHOR), 0, False))
    local_of[TGT_ANCHOR] = rest_l
    L("   rest_l(%s) 平移模长 = %.6f（local 米级）" % (TGT_ANCHOR, mag(rest_l[1])))

    Lraw, Lgrip0 = [], None
    k_stat = []
    for f in range(n + 1):
        try:
            ps = APE.get_anim_pose_at_frame(src, f, OPTS)
            pt = APE.get_anim_pose_at_frame(tgt, f, OPTS)
            Ts = tq(APE.get_bone_pose(ps, unreal.Name(SRC_HAND), unreal.AnimPoseSpaces.WORLD))
            Ws = tq(APE.get_bone_pose(ps, unreal.Name(SRC_WEAPON), unreal.AnimPoseSpaces.WORLD))
            Tt = tq(APE.get_bone_pose(pt, unreal.Name(TGT_HAND), unreal.AnimPoseSpaces.WORLD))
        except Exception as ex:
            LW("      帧 %d 求值失败: %s" % (f, str(ex)[:60]))
            continue
        if f == 0:
            # ⚠️ K 只能用**旋转**做手系对齐，平移必须置零：
            # 两个骨架的绝对世界位置不同，若带平移，K.loc（0.2~1.3 m）会整段灌进锚点
            # （第一版实测 |L_raw(t0)| 飙到 1.28 m，且各动画不一致）。
            K = (qmul(qconj(qnorm(Tt[0])), qnorm(Ts[0])), (0.0, 0.0, 0.0),
                 (UNIT_WORLD_TO_LOCAL,) * 3)
            Krot0 = K[0]
            Lgrip0 = compose(inverse(Ts), Ws)
        Lraw.append((f, compose(K, compose(inverse(Ts), Ws))))
        k_stat.append(qang(qmul(qconj(qnorm(Tt[0])), qnorm(Ts[0])), Krot0))
    if not Lraw:
        LW("   !! 无有效帧")
        continue

    t0 = Lraw[0][1]
    L("   |L_raw(t0)| 平移 = %.3f   |L_grip(t0)| = %.3f   K 平移 = %.3f K 缩放 = %.4f" % (
        mag(t0[1]), mag(Lgrip0[1]), mag(K[1]), K[2][0]))
    L("   K(t) 平移模长 min/max = %.2f / %.2f  （若抖动大说明两手对应不稳）" % (
        min(k_stat), max(k_stat)))

    # D(t) = L_raw(t0)^-1 ∘ L_raw(t)
    inv0 = inverse(t0)
    keys_loc, keys_rot, keys_scl = [], [], []
    dmax_loc, dmax_rot = 0.0, 0.0
    for f, lr in Lraw:
        D = compose(inv0, lr)
        # 方案 B：锚点直接携带「源武器骨在目标手系里的完整位姿」（含离手偏移与握法变化）。
        # F 因此退化为「axe mesh 相对武器骨的固定偏移」——与源完全同构，可逐项对照。
        keys_loc.append(lr[1])
        keys_rot.append(qnorm(lr[0]))
        keys_scl.append(rest_l[2])
        dmax_loc = max(dmax_loc, mag(tuple(D[1][i] * UNIT_WORLD_TO_LOCAL for i in range(3))))
        dmax_rot = max(dmax_rot, qang(D[0], (0.0, 0.0, 0.0, 1.0)))
    L("   写入键 %d 个 | 平移增量 max = %.5f（local 米）| 旋转增量 max = %.2f°" % (
        len(keys_loc), dmax_loc, dmax_rot))
    entry = {"target": tgt_path, "anchor": TGT_ANCHOR, "frames": len(keys_loc),
             "d_loc_max_local": round(dmax_loc, 6), "d_rot_max_deg": round(dmax_rot, 2),
             "rest_loc": list(rest_l[1])}
    report["pairs"].append(entry)

    # 方案 B 下不能因为「相对 t0 没有增量」就跳过：锚点本身还要移到「武器应在的位置」。
    # ⚠️ 但源本身就是空数据的片段（turn0 / turn_l / turn_r，实测 |L_raw(t0)| = 0）必须跳过，
    #    否则锚点被写到原点 ⇒ 斧头飞到脚下。
    if mag(t0[1]) < 0.01:
        LW("   !! |L_raw(t0)| ≈ 0 ⇒ 源是空片段，跳过并清除已有轨")
        try:
            cc = tgt.get_editor_property("controller")
            nms = [str(x) for x in
                   cc.get_editor_property("data_model_interface").get_bone_track_names()]
            if TGT_ANCHOR in nms:
                cc.remove_bone_track(TGT_ANCHOR)
                eal.save_asset(tgt_path, only_if_is_dirty=False)
                L("      已清除 %s 轨道（回落 rest）" % TGT_ANCHOR)
        except Exception as ex:
            LW("      清轨失败: %s" % str(ex)[:60])
        continue
    need = True
    L("   是否需写：%s （|L_raw(t0)| = %.4f m vs rest = %.6f m，朝向差 = %.2f°）" % (
        need, mag(t0[1]), mag(rest_l[1]), qang(t0[0], rest_l[0])))

    if mode() != "apply":
        L("   [DRY] 未写资产")
        continue

    # ---------------- 写轨 ----------------
    ctrl = tgt.get_editor_property("controller")
    names = [str(x) for x in ctrl.get_model_interface().get_bone_track_names()]
    if TGT_ANCHOR not in names:
        try:
            ctrl.add_bone_track(TGT_ANCHOR, False)
            L("   add_bone_track(%s) ok" % TGT_ANCHOR)
        except Exception as ex:
            LW("   add_bone_track 失败: %s" % str(ex)[:70])
    ok = ctrl.set_bone_track_keys(
        TGT_ANCHOR,
        [unreal.Vector(*v) for v in keys_loc],
        [unreal.Quat(v[0], v[1], v[2], v[3]) for v in keys_rot],
        [unreal.Vector(*v) for v in keys_scl],
        False)
    L("   set_bone_track_keys -> %s" % ok)
    entry["written"] = bool(ok)
    if ok:
        L("   save -> %s" % eal.save_asset(tgt_path, only_if_is_dirty=False))

# ---------------- 落盘 ----------------
try:
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=False, default=str)
    L("")
    L("已写 %s" % OUT)
except Exception as ex:
    LW("报告落盘失败: %s" % ex)

L("")
L("=== 下一步 ===")
if mode() != "apply":
    L("   DRY-RUN。确认上面的增量数值合理后，把 %s 写成 apply 重跑。" % MODE_FILE)
else:
    L("   1) 复核：ue_remote.py Scripts/anim/wp_40_weapon_anchor_recon.py（weapon_jnt_l 应被驱动）")
    L("   2) BP 斧头 Parent Socket：hand_rSocket -> weapon_jnt_l（无 Python API，需手点）")
L("WP50_BAKE_DONE")
