# -*- coding: utf-8 -*-
"""探针：Retarget Pose 相关接口有没有暴露给 Python。"""
import unreal
L = unreal.log
eal = unreal.EditorAssetLibrary

rtg = eal.load_asset("/Game/Character/Darius/Retarget/RTG_LOL_to_Darius")
ctrl = unreal.IKRetargeterController.get_controller(rtg)

ALL = sorted([x for x in dir(ctrl) if not x.startswith("_")])
L("=== IKRetargeterController 全部 %d 个接口 ===" % len(ALL))
L("  " + ", ".join(ALL))

for kw in ("pose", "align", "bone", "retarget_root", "offset", "reset"):
    L("")
    L("  含 %-14s: %s" % (kw, ", ".join([x for x in ALL if kw in x.lower()])))

L("")
L("=== 目录里与 Retarget Pose 相关的类 ===")
for kw in ("RetargetPose", "RetargetPoses", "Retargeter", "Retarget"):
    L("  %-18s: %s" % (kw, ", ".join(sorted([x for x in dir(unreal) if kw in x]))[:500]))

L("")
L("=== 尝试读取 retarget pose ===")
E = unreal.RetargetSourceOrTarget
for tag, side in (("SOURCE", E.SOURCE), ("TARGET", E.TARGET)):
    for fn in ("get_retarget_pose", "get_current_retarget_pose", "get_retarget_pose_name"):
        f = getattr(ctrl, fn, None)
        if f is None:
            continue
        try:
            L("  %s.%s() -> %s" % (tag, fn, f(side)))
        except Exception as ex:
            L("  %s.%s() : %s" % (tag, fn, str(ex)[:100]))
for fn in ("get_retarget_pose_names", "get_all_retarget_pose_names", "get_retarget_pose_name"):
    f = getattr(ctrl, fn, None)
    if f is None:
        continue
    for side in (E.SOURCE, E.TARGET):
        try:
            r = f(side)
            L("  %s(%s) -> %s" % (fn, side, r))
        except Exception as ex:
            L("  %s(%s) : %s" % (fn, side, str(ex)[:90]))
L("=== DONE ===")
