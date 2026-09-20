# -*- coding: utf-8 -*-
"""读当前 retarget pose 的旋转偏移（目标侧 + 源侧），用来判断标定到底存没存住。

`ik_36` 改过 retarget pose 并 `save_asset` 过，但随后编辑器崩过一次 ——
本脚本是「重启后回读」的验证，避免在错误前提上继续。

同时把每条链的**链尾骨**（无子骨 ⇒ `Direction` 方法定不出朝向）单独列出来，
这些正是 `Retarget_Pose_Guide.md` 说必须手工处理的那几根。
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"
E = unreal.RetargetSourceOrTarget

# 目标侧：10 条链的骨（链尾用 ★ 标出）
TGT = [
    "root", "pelvis",
    "spine_01", "spine_02", "spine_03",
    "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l", "★hand_l",
    "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r", "★hand_r",
    "thigh_l", "calf_l", "foot_l", "★foot_l",
    "thigh_r", "calf_r", "foot_r", "★foot_r",
    "neck_01", "head", "★head",
]
SRC = ["Root", "Hips", "Spine1", "Spine2", "L_Clavicle", "L_Shoulder", "L_Elbow", "L_Hand",
       "R_Clavicle", "R_Shoulder", "R_Elbow", "R_Hand", "L_Hip", "L_KneeLower", "L_Foot",
       "R_Hip", "R_KneeLower", "R_Foot", "Neck", "Head"]

rtg = eal.load_asset(RTG)
if rtg is None:
    LW("!! 找不到 %s" % RTG)
    raise SystemExit(1)
ctrl = unreal.IKRetargeterController.get_controller(rtg)
L("retargeter = %s" % rtg.get_name())

# ---------------------------------------------------------------- 当前 pose 名
L("")
L("################ 当前 retarget pose 名")
for tag, side in (("SOURCE", E.SOURCE), ("TARGET", E.TARGET)):
    for fn in ("get_current_retarget_pose_name",):
        f = getattr(ctrl, fn, None)
        if f is None:
            L("   %s.%s 不存在" % (tag, fn))
            continue
        for args in ((side,), ()):
            try:
                L("   %-6s %s(%s) -> %s" % (tag, fn, args, f(*args)))
                break
            except Exception as ex:
                if not args:
                    LW("   %s %s: %s" % (tag, fn, str(ex)[:90]))

# ---------------------------------------------------------------- 偏移
identity_deg = 0.0


def offset_deg(bone, side):
    for args in ((bone, side), (side, bone)):
        try:
            q = ctrl.get_rotation_offset_for_retarget_pose_bone(*args)
            break
        except Exception:
            q = None
    if q is None:
        return None
    try:
        r = q.rotator()
        return (r.roll, r.pitch, r.yaw)
    except Exception:
        return ("?", "?", "?")


def mag(d):
    if d is None or d[0] == "?":
        return None
    return max(abs(x) for x in d)


L("")
L("################ 目标侧 retarget pose 旋转偏移")
L("   %-14s %12s %12s %12s   %s" % ("骨", "roll", "pitch", "yaw", "最大分量"))
n_nonzero = 0
for b in TGT:
    b2 = b.lstrip("★")
    d = offset_deg(b2, E.TARGET)
    if d is None:
        L("   %-14s <读不到>" % b2)
        continue
    m = mag(d)
    if m is not None and m > 0.05:
        n_nonzero += 1
    L("   %-14s %12.2f %12.2f %12.2f   %s" % (b2, d[0], d[1], d[2],
                                              "%.2f" % m if m is not None else "?"))
L("   ⇒ 非零偏移骨数 = %d / %d" % (n_nonzero, len(set(b.lstrip('★') for b in TGT))))

L("")
L("################ 源侧 retarget pose 旋转偏移（应为 0 = 用源自身 rest pose）")
for b in SRC:
    d = offset_deg(b, E.SOURCE)
    if d is None:
        L("   %-14s <读不到>" % b)
        continue
    L("   %-14s %12.2f %12.2f %12.2f" % (b, d[0], d[1], d[2]))

L("")
L("################ 对齐方法枚举")
M = unreal.RetargetAutoAlignMethod
for v in ("CHAIN_TO_CHAIN", "LOCAL_ROTATION_AXES", "GLOBAL_ROTATION_AXES", "MESH_TO_MESH"):
    L("   %-24s %s" % (v, getattr(M, v, "不存在")))
L("=== DONE ===")
