# -*- coding: utf-8 -*-
"""rtg_06_probe_preview —— 只读：查 RTG 两侧的 preview mesh 绑定（预览看不见模型的头号嫌疑）"""

import unreal

L = unreal.log
LW = unreal.log_warning

RTG = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, RTG)
c = unreal.IKRetargeterController.get_controller(rtg)

for side, tag in ((unreal.RetargetSourceOrTarget.TARGET, "TARGET"), (unreal.RetargetSourceOrTarget.SOURCE, "SOURCE")):
    for fn in ("get_preview_mesh", "get_skeletal_mesh"):
        f = getattr(c, fn, None)
        if f is None:
            L(f"[PROBE] {tag}.{fn} 不存在")
            continue
        try:
            arg = side if fn == "get_preview_mesh" else side
            v = f(arg)
            L(f"[PROBE] {tag}.{fn} = {v.get_path_name() if v else None}")
        except Exception as ex:
            try:
                v = f()
                L(f"[PROBE] {tag}.{fn}() = {v.get_path_name() if v else None}  (no-side)")
            except Exception as ex2:
                LW(f"[PROBE] {tag}.{fn} err {ex} / {ex2}")

L(f"[PROBE] ctrl API = {[m for m in dir(c) if not m.startswith('_')]}")
L("PROBE_DONE")
