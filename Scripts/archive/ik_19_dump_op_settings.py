# -*- coding: utf-8 -*-
"""读取各 op 的 settings 结构，定位 pelvis 平移放大项。"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

rtg = eal.load_asset("/Game/Character/Darius/Retarget/RTG_LOL_to_Darius")
ctrl = unreal.IKRetargeterController.get_controller(rtg)
n = ctrl.get_num_retarget_ops()

for i in range(n):
    nm = str(ctrl.get_op_name(i))
    oc = ctrl.get_op_controller(i)
    L("")
    L("=== [%d] %s ===" % (i, nm))
    oc2 = ctrl.get_op_controller(i)
    for meth, lbl in (("get_source_pelvis_bone", "源 pelvis 骨"),
                      ("get_target_pelvis_bone", "目标 pelvis 骨"),
                      ("get_source_root_bone", "源 root 骨"),
                      ("get_target_root_bone", "目标 root 骨")):
        f = getattr(oc2, meth, None)
        if f is None:
            continue
        try:
            L("   %-16s = %s" % (lbl, f()))
        except Exception as ex:
            L("   %-16s : %s" % (lbl, str(ex)[:80]))
    try:
        s = oc.get_settings()
    except Exception as ex:
        LW("   get_settings 失败: %s" % str(ex)[:100])
        continue
    if s is None:
        LW("   settings = None")
        continue
    try:
        d = s.to_dict()
        L("   settings(%d 项):" % len(d))
        for k in sorted(d):
            v = str(d[k])
            if len(v) > 220:
                v = v[:220] + "…"
            L("      %-44s = %s" % (k, v))
    except Exception:
        L("   settings = %s" % s)
        for p in sorted([x for x in dir(s) if not x.startswith("_")]):
            try:
                v = getattr(s, p)
                if callable(v):
                    continue
                L("      %-44s = %s" % (p, v))
            except Exception:
                pass
L("=== DONE ===")
