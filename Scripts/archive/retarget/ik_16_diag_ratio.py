# -*- coding: utf-8 -*-
"""诊断 v4：逐骨比对「局部平移模长」，判断新产物是统一放大还是逐骨错乱。"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary

BONES = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head",
         "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l",
         "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r",
         "thigh_l", "calf_l", "foot_l", "ball_l",
         "thigh_r", "calf_r", "foot_r", "ball_r"]

NEW = "/Game/Character/Darius/Anims_TP/A_Darius_idle1"
OLD = "/Game/Character/Darius/Anims/A_Darius_Idle1_TP"


def mag(v):
    return (v.x * v.x + v.y * v.y + v.z * v.z) ** 0.5


def locals_of(pkg, frame=0):
    a = eal.load_asset(pkg)
    out = {}
    for b in BONES:
        try:
            if not AL.does_bone_name_exist(a, b):
                out[b] = None
                continue
            t = AL.get_bone_pose_for_frame(a, b, frame, False)
            out[b] = mag(t.translation)
        except Exception as ex:
            out[b] = "ERR:%s" % str(ex)[:30]
    return out


n = locals_of(NEW)
o = locals_of(OLD)

L("  %-14s %12s %12s %10s" % ("bone", "旧|T|", "新|T|", "新/旧"))
ratios = []
for b in BONES:
    a1, a2 = o.get(b), n.get(b)
    if isinstance(a1, float) and isinstance(a2, float):
        r = a2 / a1 if a1 > 1e-9 else float("inf")
        ratios.append(r)
        L("  %-14s %12.4f %12.4f %10.2f" % (b, a1, a2, r))
    else:
        L("  %-14s %12s %12s %10s" % (b, a1, a2, "-"))

if ratios:
    rs = sorted(ratios)
    L("")
    L("  比值：最小 %.2f  中位 %.2f  最大 %.2f  （若为常数 ⇒ 统一比例错误）"
      % (rs[0], rs[len(rs) // 2], rs[-1]))

L("")
L("=== 骨骼 rest pose 的本地平移（真值基线）===")
sk = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")
if sk is not None:
    for fn in ("get_reference_pose", "get_reference_pose_for_bone"):
        f = getattr(sk, fn, None)
        L("   Skeleton.%s : %s" % (fn, "存在" if f else "不存在"))
    try:
        rp = sk.get_reference_pose()
        L("   reference_pose 返回类型 = %s" % type(rp))
        if isinstance(rp, (list, tuple)) or hasattr(rp, "__len__"):
            for item in list(rp)[:8]:
                L("      %s" % item)
    except Exception as ex:
        L("   get_reference_pose 失败: %s" % str(ex)[:120])
L("=== DONE ===")
