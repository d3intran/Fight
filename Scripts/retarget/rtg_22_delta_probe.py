# -*- coding: utf-8 -*-
"""rtg_22_delta_probe —— 只读：同一 AnimPose 内比较「动画姿态」与「参考姿态」的骨骼旋转差，
判定足部旋转到底有没有被重定向动过（不受坐标系换算干扰）。"""

import unreal
import math

L = unreal.log
LW = unreal.log_warning
APE = unreal.AnimPoseExtensions


def deg_between(qa, qb):
    try:
        d = abs(qa.x * qb.x + qa.y * qb.y + qa.z * qb.z + qa.w * qb.w)
    except AttributeError:
        d = abs(qa.get_editor_property("x") * qb.get_editor_property("x") +
                qa.get_editor_property("y") * qb.get_editor_property("y") +
                qa.get_editor_property("z") * qb.get_editor_property("z") +
                qa.get_editor_property("w") * qb.get_editor_property("w"))
    d = min(1.0, max(-1.0, d))
    return math.degrees(2.0 * math.acos(d))


def report(tag, clip, bones, frame_frac=0.5):
    a = unreal.load_object(None, clip)
    if not a:
        LW(f"[DELTA] 缺 {clip}")
        return
    keys = a.get_editor_property("number_of_sampled_keys")
    f = int(round((keys - 1) * frame_frac))
    opts = unreal.AnimPoseEvaluationOptions()
    pose = APE.get_anim_pose_at_frame(a, f, opts)
    L(f"[DELTA] {tag}  keys={keys} frame={f}  clip={clip}")
    try:
        tracks = [str(t) for t in APE.get_bone_names(pose)]
        L(f"[DELTA]   AnimPose 骨骼数 = {len(tracks)}")
    except Exception as ex:
        LW(f"[DELTA]   bone names err {ex}")
    for b in bones:
        try:
            anim_t = APE.get_bone_pose(pose, unreal.Name(b), unreal.AnimPoseSpaces.WORLD)
            ref_t = APE.get_ref_bone_pose(pose, unreal.Name(b), unreal.AnimPoseSpaces.WORLD)
            ang = deg_between(anim_t.rotation, ref_t.rotation)
            dl = (anim_t.translation - ref_t.translation).length()
            L(f"[DELTA]   {b:<12} 旋转差={ang:7.2f}°  位移={dl:8.3f}  anim=({anim_t.translation.x:7.3f},{anim_t.translation.y:7.3f},{anim_t.translation.z:7.3f})")
        except Exception as ex:
            LW(f"[DELTA]   {b} err {ex}")


TGT_BONES = ["thigh_l", "calf_l", "foot_l", "ball_l", "thigh_r", "calf_r", "foot_r", "ball_r", "pelvis", "spine_01", "upperarm_r", "hand_r", "weapon_jnt"]
SRC_BONES = ["L_Hip", "L_KneeLower", "L_Foot", "L_Toe", "R_Hip", "R_Foot", "Pelvis", "Spine1", "R_Shoulder", "R_Hand", "Weapon"]

report("TGT_run", "/Game/Character/Darius/Animations/LOL_Retarget_Test/A_Darius_run", TGT_BONES)
report("TGT_idle", "/Game/Character/Darius/Animations/LOL_Retarget_Test/A_Darius_idle1", TGT_BONES)
report("SRC_run", "/Game/Character/Darius/LOL_Source/A_LOL_Darius_run", SRC_BONES)
report("SRC_idle", "/Game/Character/Darius/LOL_Source/A_LOL_Darius_idle1", SRC_BONES)
L("DELTA_PROBE_DONE")
