# -*- coding: utf-8 -*-
"""rtg_21_probe_ops —— 只读：把 RTG 五个 op 的控制器与设置全量 dump 出来，找「根/骨盆旋转」的开关"""

import unreal

L = unreal.log
LW = unreal.log_warning

rtg = unreal.load_object(None, "/Game/Character/Darius/IK/RTG_LOL_To_Darius")
c = unreal.IKRetargeterController.get_controller(rtg)

n = c.get_num_retarget_ops()
L(f"[OPS] n = {n}")
for i in range(n):
    nm = c.get_op_name(i)
    L(f"[OPS] ---- [{i}] {nm} ----")
    oc = None
    for arg in (i, nm):
        try:
            oc = c.get_op_controller(arg)
            break
        except Exception as ex:
            LW(f"[OPS] get_op_controller({arg!r}) err {ex}")
    if oc is None:
        continue
    L(f"[OPS]   ctrl api = {[m for m in dir(oc) if not m.startswith('_')]}")
    for getter in ("get_settings", "get_op_settings", "settings_as_string", "get_editor_property"):
        f = getattr(oc, getter, None)
        if f is None:
            continue
        try:
            if getter == "get_editor_property":
                s = f("settings")
            else:
                s = f()
            L(f"[OPS]   {getter}() = {s}")
            for sub in [m for m in dir(s) if not m.startswith("_")]:
                try:
                    L(f"[OPS]     .{sub} = {getattr(s, sub)}")
                except Exception:
                    pass
        except Exception as ex:
            LW(f"[OPS]   {getter} err {ex}")

L(f"[OPS] get_all_chain_settings = {c.get_all_chain_settings()}")
L("OPS_PROBE_DONE")
