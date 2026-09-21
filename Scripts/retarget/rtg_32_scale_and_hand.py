# -*- coding: utf-8 -*-
"""rtg_32_scale_and_hand —— 只读两件事：
1) 量重定向产物的「最外层骨 scale」是否被写坏（已知坑：外层骨 scale=100 被写成 1 ⇒ 角色缩到 1.85cm、披风爆炸）。
2) 扫全部源片段，量斧头 Weapon 骨离 R_Hand / L_Hand 哪个更近 ⇒ 判定「有些是左手」的真伪。
"""

import unreal
import math

L = unreal.log
LW = unreal.log_warning
APE = unreal.AnimPoseExtensions

TGT_TEST = "/Game/Character/Darius/Animations/LOL_Retarget_Test/A_Darius_run"
TGT_TEST2 = "/Game/Character/Darius/Animations/LOL_Retarget_Test/A_Darius_idle1"
TGT_GOOD = "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered"
SRC = "/Game/Character/Darius/LOL_Source/A_LOL_Darius_run"
SRC_DIR = "/Game/Character/Darius/LOL_Source"

# ---------------------------------------------------------------- 1. 骨骼 scale 对比
L("=== 骨骼局部 scale 对比（frame 0 与中段）===")
for path, tag in ((TGT_TEST, "TGT_retargetRun"), (TGT_TEST2, "TGT_retargetIdle"),
                  (TGT_GOOD, "TGT_好样本AxeIdle"), (SRC, "SRC_run")):
    a = unreal.load_object(None, path)
    if not a:
        LW(f"[SCALE] 缺 {path}")
        continue
    keys = a.get_editor_property("number_of_sampled_keys")
    fps_frames = [0, int((keys - 1) / 2), keys - 1]
    for f in fps_frames:
        parts = []
        for b in ("root", "Root", "pelvis", "Pelvis", "spine_01", "foot_l", "hand_r", "weapon_jnt", "Weapon"):
            try:
                t = unreal.AnimationLibrary.get_bone_pose_for_frame(a, unreal.Name(b), f, False)
                s = t.scale3d
                if abs(s.x - 1.0) > 1e-3 or abs(s.x - 100.0) > 1e-3 or b in ("root", "Root", "pelvis", "Pelvis"):
                    parts.append(f"{b}=({s.x:.3f},{s.y:.3f},{s.z:.3f})")
            except Exception:
                pass
        L(f"[SCALE] {tag:<20} f{f:03d}: " + "  ".join(parts))

# ---------------------------------------------------------------- 2. 斧头在哪只手
L("=== 源片段：斧头 Weapon 离哪只手更近 ===")
eal = unreal.EditorAssetLibrary
assets = eal.list_assets(SRC_DIR, recursive=False, include_folder=False)
clips = sorted({str(a).split(".")[0] for a in assets if "A_LOL_Darius_" in str(a) and "BindPose" not in str(a)})
opts = unreal.AnimPoseEvaluationOptions()
left, right, mid = [], [], []
for p in clips:
    a = unreal.load_object(None, p)
    if not a:
        continue
    try:
        keys = a.get_editor_property("number_of_sampled_keys")
        if keys is None or keys < 2:
            continue
        frames = sorted({int(round(i * (keys - 1) / 4.0)) for i in range(5)})
        f = frames[len(frames) // 2]
        pose = APE.get_anim_pose_at_frame(a, f, opts)
        tw = APE.get_bone_pose(pose, unreal.Name("Weapon"), unreal.AnimPoseSpaces.WORLD).translation
        tr = APE.get_bone_pose(pose, unreal.Name("R_Hand"), unreal.AnimPoseSpaces.WORLD).translation
        tl = APE.get_bone_pose(pose, unreal.Name("L_Hand"), unreal.AnimPoseSpaces.WORLD).translation
        dr = math.sqrt((tw.x - tr.x) ** 2 + (tw.y - tr.y) ** 2 + (tw.z - tr.z) ** 2)
        dl = math.sqrt((tw.x - tl.x) ** 2 + (tw.y - tl.y) ** 2 + (tw.z - tl.z) ** 2)
        name = p.split("/")[-1]
        if dl < dr * 0.8:
            left.append((name, round(dl, 1), round(dr, 1)))
        elif dr < dl * 0.8:
            right.append((name, round(dl, 1), round(dr, 1)))
        else:
            mid.append((name, round(dl, 1), round(dr, 1)))
    except Exception as ex:
        LW(f"[HAND] {p} err {ex}")

L(f"[HAND] 更近左手（可疑）{len(left)} 条：")
for r in left:
    L(f"[HAND]   左手 {r[0]:<34} dL={r[1]}cm dR={r[2]}cm")
L(f"[HAND] 更近右手 {len(right)} 条（前 8 个）：")
for r in right[:8]:
    L(f"[HAND]   右手 {r[0]:<34} dL={r[1]}cm dR={r[2]}cm")
L(f"[HAND] 差不多近 {len(mid)} 条：")
for r in mid:
    L(f"[HAND]   居中 {r[0]:<34} dL={r[1]}cm dR={r[2]}cm")
L("SCALE_HAND_DONE")
