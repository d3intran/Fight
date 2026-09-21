# -*- coding: utf-8 -*-
"""rtg_10_world_audit —— 世界空间姿态审计（AnimPose 路线，不生成 Actor）

要点：
1. 先把内存里的重定向产物落盘（此前它只存在于 Autosave，一崩就没）。
2. 用 AnimPoseExtensions 直接对片段求值，量脚/手/斧头的世界坐标与相对参考姿态的增量。
3. 同一套指标同时跑在源片段上，作为「动作到底有没有传过来」的基线。
"""

import unreal

L = unreal.log
LW = unreal.log_warning
APE = unreal.AnimPoseExtensions

CLIP = "/Game/Character/Darius/Animations/LOL_Retarget/A_Darius_idle1"
SRC_CLIP = "/Game/Character/Darius/LOL_Source/A_LOL_Darius_idle1"
SRC_CLIP_RUN = "/Game/Character/Darius/LOL_Source/A_LOL_Darius_run"

# ============================================================ 1. 保护交付物：落盘
anim = unreal.load_object(None, CLIP)
if not anim:
    LW(f"[FAIL] 内存里找不到 {CLIP}（编辑器可能已重启，产物已丢）")
    raise SystemExit(1)

try:
    pkg = anim.get_outermost().get_name()
    L(f"[SAVE] 目标包 = {pkg}")
    ok = unreal.EditorAssetLibrary.save_asset(CLIP, only_if_is_dirty=False)
    L(f"[SAVE] save_asset({CLIP}) = {ok}")
except Exception as ex:
    LW(f"[SAVE] err {ex}")

n_keys = anim.get_editor_property("number_of_sampled_keys")
length = anim.get_editor_property("sequence_length")
L(f"[CLIP] keys={n_keys} length={length:.3f}s")

# ============================================================ 2. 采样函数
TGT_BONES = ["pelvis", "spine_01", "head", "thigh_l", "calf_l", "foot_l", "ball_l",
             "thigh_r", "calf_r", "foot_r", "ball_r", "hand_l", "hand_r", "weapon_jnt"]
SRC_BONES = ["Pelvis", "Spine1", "Head", "L_Hip", "L_KneeLower", "L_Foot", "L_Toe",
             "R_Hip", "R_KneeLower", "R_Foot", "R_Toe", "L_Hand", "R_Hand", "Weapon"]


def _eval_opts():
    for fn in ("AnimPoseEvaluationOptions",):
        cls = getattr(unreal, fn, None)
        if cls is None:
            continue
        try:
            return cls()
        except Exception:
            try:
                return cls(unreal.AnimPoseEvaluationOptions())
            except Exception as ex:
                LW(f"[SAMPLE] opts err {ex}")
    return None


def sample(anim_asset, bones, n=9):
    """返回 {frame: {bone: Vector}}，世界(=组件)空间"""
    opts = _eval_opts()
    keys = anim_asset.get_editor_property("number_of_sampled_keys")
    frames = sorted(set(int(round(i * (keys - 1) / (n - 1))) for i in range(n)))
    out = {}
    for f in frames:
        row = {}
        for attempt in ("with_opts", "two_arg"):
            try:
                if attempt == "with_opts":
                    pose = APE.get_anim_pose_at_frame(anim_asset, f, opts)
                else:
                    pose = APE.get_anim_pose_at_frame(anim_asset, f)
            except Exception as ex:
                if attempt == "two_arg":
                    LW(f"[SAMPLE] get_anim_pose_at_frame({f}) err {ex}")
                continue
            for b in bones:
                try:
                    tr = APE.get_bone_pose(pose, unreal.Name(b), unreal.AnimPoseSpaces.WORLD)
                    row[b] = tr.translation
                except Exception as ex:
                    row[b] = str(ex)
            break
        out[f] = row
    return frames, out


def report(tag, keys_count, frames, rows, pairs, weapon_pair=None):
    L(f"=== {tag} 采样 ({len(frames)} 帧) ===")
    for f in frames:
        d = rows.get(f) or {}
        def g(b):
            v = d.get(b)
            return None if v is None or isinstance(v, str) else v
        a, b = pairs[0], pairs[1]
        va, vb = g(a), g(b)
        if va and vb:
            L(f"[{tag} F{f:03d}] {a}={va.x:7.2f},{va.y:7.2f},{va.z:7.2f} | "
              f"{b}={vb.x:7.2f},{vb.y:7.2f},{vb.z:7.2f} | 间距={(va - vb).length():6.2f} | dx={va.x - vb.x:+7.2f} | dz={va.z - vb.z:+7.2f}")
    for b in pairs:
        pts = []
        for f in frames:
            v = (rows.get(f) or {}).get(b)
            if v is not None and not isinstance(v, str):
                pts.append(v)
        if len(pts) >= 2:
            span = max((p - pts[0]).length() for p in pts)
            L(f"[MOTION {tag}] {b:<12} 相对首帧最大位移 = {span:6.2f} cm")

    # 中段帧的全身姿态快照 + 朝向向量
    mid = frames[len(frames) // 2]
    d0 = rows.get(mid) or {}
    L(f"[POSE {tag} F{mid:03d}] 全身快照:")
    for b in ("pelvis", "spine_01", "head", "thigh_l", "calf_l", "ball_l", "hand_l", "hand_r",
              "Pelvis", "Spine1", "Head", "L_Hip", "L_KneeLower", "L_Toe", "R_Toe", "L_Hand"):
        v = d0.get(b)
        if v is not None and not isinstance(v, str):
            L(f"[POSE {tag} F{mid:03d}]   {b:<12} = {v.x:8.3f},{v.y:8.3f},{v.z:8.3f}")
    for a, b in (("foot_l", "ball_l"), ("foot_r", "ball_r"), ("L_Foot", "L_Toe"), ("R_Foot", "R_Toe")):
        va, vb = d0.get(a), d0.get(b)
        if va is not None and vb is not None and not isinstance(va, str) and not isinstance(vb, str):
            L(f"[POSE {tag} F{mid:03d}]   朝向 {a}->{b} = ({vb.x - va.x:+7.3f},{vb.y - va.y:+7.3f},{vb.z - va.z:+7.3f})")

    if weapon_pair:
        wb, hb = weapon_pair
        for f in frames:
            d = rows.get(f) or {}
            vw, vh = d.get(wb), d.get(hb)
            if vw is not None and vh is not None and not isinstance(vw, str) and not isinstance(vh, str):
                L(f"[AXE {tag} F{f:03d}] {wb}={vw.x:7.2f},{vw.y:7.2f},{vw.z:7.2f}  距{wb}↔{hb}={(vw - vh).length():6.2f} cm")


# ---- 目标片段
frames, rows = sample(anim, TGT_BONES)
report("TGT", n_keys, frames, rows, ("foot_l", "foot_r"), ("weapon_jnt", "hand_r"))

# ---- 源片段（基线）
for path in (SRC_CLIP, SRC_CLIP_RUN):
    sa = unreal.load_object(None, path)
    if not sa:
        LW(f"[SRC] 找不到 {path}")
        continue
    sf, sr = sample(sa, SRC_BONES)
    report("SRC", sa.get_editor_property("number_of_sampled_keys"), sf, sr, ("L_Foot", "R_Foot"), ("Weapon", "R_Hand"))

L("WORLD_AUDIT_DONE")
