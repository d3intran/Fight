# -*- coding: utf-8 -*-
"""rtg_50_finger_audit —— 只读：对比源/目标手指骨骼与链映射，并量出哪些手指在重定向后「没动」"""

import unreal
import math

L = unreal.log
LW = unreal.log_warning
AL = unreal.AnimationLibrary
APE = unreal.AnimPoseExtensions

SRC_CLIP = "/Game/Character/Darius/LOL_Source/A_LOL_Darius_idle1"
TGT_CLIP = "/Game/Character/Darius/Animations/LOL_Retarget_Test/A_Darius_idle1"
SRC_RIG = "/Game/Character/Darius/IK/IK_LOL_Darius"
TGT_RIG = "/Game/Character/Darius/IK/IK_Darius"
RTG = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"

KEY = ("thumb", "index", "middle", "ring", "pinky", "metacarpal")

# ---------------------------------------------------------------- 1. 骨骼清单
for tag, clip in (("SRC", SRC_CLIP), ("TGT", TGT_CLIP)):
    a = unreal.load_object(None, clip)
    if not a:
        LW(f"[FINGER] 缺 {clip}")
        continue
    names = [str(t) for t in AL.get_animation_track_names(a)]
    fingers = [n for n in names if any(k in n.lower() for k in KEY)]
    L(f"[FINGER] {tag} 轨总数={len(names)}  手指相关={len(fingers)}")
    L(f"[FINGER] {tag} 手指骨：{fingers}")

# ---------------------------------------------------------------- 2. 链定义 + 映射
c = unreal.IKRetargeterController.get_controller(unreal.load_object(None, RTG))
for path, tag in ((SRC_RIG, "SRC"), (TGT_RIG, "TGT")):
    rc = unreal.IKRigController.get_controller(unreal.load_object(None, path))
    L(f"[FINGER] --- {tag} rig 链（手指类）---")
    for ch in rc.get_retarget_chains():
        try:
            nm = str(ch.chain_name)
            if not any(k in nm.lower() for k in KEY):
                continue
            sb = str(getattr(ch, "start_bone", "?"))
            eb = str(getattr(ch, "end_bone", "?"))
            extra = ""
            if tag == "TGT":
                try:
                    extra = "  srcChain=" + str(c.get_source_chain(ch.chain_name))
                except Exception:
                    extra = "  srcChain=ERR"
            L(f"[FINGER]   {tag} {nm} | {sb} -> {eb}{extra}")
        except Exception as ex:
            LW(f"[FINGER]   链打印失败: {str(ex)[:80]}")

# ---------------------------------------------------------------- 3. 手指「有没有在动」
def qang(a, b):
    d = abs(a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3])
    d = min(1.0, max(-1.0, d))
    return math.degrees(2.0 * math.acos(d))


def motion(tag, clip, bones, n=6):
    a = unreal.load_object(None, clip)
    if not a:
        return
    keys = a.get_editor_property("number_of_sampled_keys")
    frames = sorted({int(round(i * (keys - 1) / (n - 1.0))) for i in range(n)})
    opts = unreal.AnimPoseEvaluationOptions()
    L(f"[FINGER] --- {tag} 手指活动量（相对参考姿态的最大旋转差）---")
    res = {}
    for b in bones:
        mx = 0.0
        for f in frames:
            try:
                pose = APE.get_anim_pose_at_frame(a, f, opts)
                qa = APE.get_bone_pose(pose, unreal.Name(b), unreal.AnimPoseSpaces.WORLD).rotation
                qr = APE.get_ref_bone_pose(pose, unreal.Name(b), unreal.AnimPoseSpaces.WORLD).rotation
                v = (qa.x, qa.y, qa.z, qa.w)
                w = (qr.x, qr.y, qr.z, qr.w)
                mx = max(mx, qang(v, w))
            except Exception:
                pass
        res[b] = round(mx, 2)
    for b, v in res.items():
        L(f"[FINGER]   {tag} {b:<22} 最大旋转差 = {v:7.2f}°")


SRC_F = ["L_Thumb1", "L_Thumb2", "L_Index1", "L_Index2", "L_Middle1", "L_Middle2",
         "L_Ring1", "L_Ring2", "L_Pinky1", "L_Pinky2",
         "R_Index1", "R_Index2", "R_Middle1", "R_Middle2"]
TGT_F = ["thumb_01_l", "thumb_02_l", "thumb_03_l", "index_metacarpal_l", "index_01_l", "index_02_l", "index_03_l",
         "middle_metacarpal_l", "middle_01_l", "middle_02_l", "middle_03_l",
         "ring_metacarpal_l", "ring_01_l", "ring_02_l", "ring_03_l",
         "pinky_metacarpal_l", "pinky_01_l", "pinky_02_l", "pinky_03_l",
         "index_01_r", "index_03_r", "middle_01_r", "middle_03_r"]

motion("SRC", SRC_CLIP, SRC_F)
motion("TGT", TGT_CLIP, TGT_F)
L("FINGER_AUDIT_DONE")
