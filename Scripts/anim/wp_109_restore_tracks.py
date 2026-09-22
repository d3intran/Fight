# -*- coding: utf-8 -*-
"""wp_109 —— 从 wp108_baseline.json 恢复 thigh/calf 的原始局部轨（清两骨 IK 污染）"""
import json
import unreal
L = unreal.log
eal = unreal.EditorAssetLibrary
BL = json.load(open("E:/UE/Fight/Saved/Attack/wp108_baseline.json", encoding="utf-8"))
for nm, bl in BL.items():
    p = "/Game/Character/Darius/Animations/LOL_Retarget/" + nm
    a = unreal.load_object(None, p)
    if a is None:
        L("[RB] 载不到 %s" % p); continue
    n = len(next(iter(bl.values()))["rots"])
    ok_all = True
    for bn, tr in bl.items():
        if len(tr["rots"]) != n:
            ok_all = False; continue
        locs = [unreal.Vector(*v) for v in tr["locs"]]
        rots = [unreal.Quat(*v) for v in tr["rots"]]
        scls = [unreal.Vector(*v) for v in tr["scls"]]
        if not a.get_editor_property("controller").set_bone_track_keys(bn, locs, rots, scls, False):
            ok_all = False
    if ok_all:
        eal.save_asset(p, only_if_is_dirty=False)
    L("[RB] %-30s %s" % (nm, "restored" if ok_all else "FAILED"))
L("[RB] DONE")
