# -*- coding: utf-8 -*-
"""rtg_33_scale_hunt —— 只读：找出「角色变小」的元凶——对比重定向产物与好样本里**哪些骨带了非 1 的局部缩放**"""

import unreal

L = unreal.log
LW = unreal.log_warning
AL = unreal.AnimationLibrary

PAIRS = [
    ("TGT_重定向run", "/Game/Character/Darius/Animations/LOL_Retarget_Test/A_Darius_run"),
    ("TGT_好样本", "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered"),
    ("TGT_好样本2", "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Layered"),
    ("SRC_run", "/Game/Character/Darius/LOL_Source/A_LOL_Darius_run"),
]

layers = {}
for tag, path in PAIRS:
    a = unreal.load_object(None, path)
    if not a:
        LW(f"[HUNT] 缺 {path}")
        continue
    try:
        tracks = [str(t) for t in AL.get_animation_track_names(a)]
    except Exception as ex:
        LW(f"[HUNT] {tag} track names err {ex}")
        continue
    keys = a.get_editor_property("number_of_sampled_keys")
    layers[tag] = set(tracks)
    L(f"[HUNT] {tag}: {len(tracks)} 轨  keys={keys}")
    L(f"[HUNT]   前 8 轨名 = {tracks[:8]}")
    # 找出局部 scale 在任意采样帧 != 1 的骨
    bad = {}
    step = max(1, (keys - 1) // 6)
    for b in tracks:
        vals = set()
        for f in range(0, keys, step):
            try:
                s = AL.get_bone_pose_for_frame(a, unreal.Name(b), f, False).scale3d
                vals.add((round(s.x, 4), round(s.y, 4), round(s.z, 4)))
            except Exception:
                pass
        if not vals:
            continue
        if len(vals) > 1 or not all(abs(v[0] - 1.0) < 1e-4 and abs(v[1] - 1.0) < 1e-4 and abs(v[2] - 1.0) < 1e-4 for v in vals):
            bad[b] = sorted(vals)[:3]
    L(f"[HUNT]   ★ 非 1 或跨帧变化的 scale 骨数 = {len(bad)}")
    for b, v in list(bad.items())[:25]:
        L(f"[HUNT]     {b:<28} scale 样本={v}")

tags = list(layers.keys())
if len(tags) >= 2:
    base = layers[tags[1]]
    for t in tags:
        if t == tags[1]:
            continue
        only_here = sorted(layers[t] - base)
        L(f"[HUNT] {t} 比 {tags[1]} 多出的轨({len(only_here)}): {only_here[:12]}")
L("HUNT_DONE")
