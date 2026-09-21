# -*- coding: utf-8 -*-
"""rtg_12_probe_rootsettings —— 只读：TargetRootSettings / RetargetGlobalSettings 的字段名与当前值"""

import unreal

L = unreal.log
LW = unreal.log_warning

rtg = unreal.load_object(None, "/Game/Character/Darius/IK/RTG_LOL_To_Darius")
c = unreal.IKRetargeterController.get_controller(rtg)

for cls_name in ("TargetRootSettings", "RetargetGlobalSettings", "RetargetRootSettings"):
    cls = getattr(unreal, cls_name, None)
    if cls is None:
        L(f"[RS] {cls_name} 不存在")
        continue
    try:
        obj = cls()
        fields = [m for m in dir(obj) if not m.startswith("_")]
        L(f"[RS] {cls_name} fields = {fields}")
        for f in fields:
            try:
                L(f"[RS]   {cls_name}.{f} = {getattr(obj, f)}")
            except Exception:
                pass
    except Exception as ex:
        LW(f"[RS] {cls_name} err {ex}")

try:
    rs = c.get_root_settings()
    L(f"[RS] 当前 get_root_settings() = {rs}")
    for f in [m for m in dir(rs) if not m.startswith("_")]:
        try:
            L(f"[RS]   current.{f} = {getattr(rs, f)}")
        except Exception:
            pass
except Exception as ex:
    LW(f"[RS] get_root_settings err {ex}")

try:
    gs = c.get_global_settings()
    L(f"[RS] 当前 get_global_settings() = {gs}")
    for f in [m for m in dir(gs) if not m.startswith("_")]:
        try:
            L(f"[RS]   global.{f} = {getattr(gs, f)}")
        except Exception:
            pass
except Exception as ex:
    LW(f"[RS] get_global_settings err {ex}")

L("RS_DONE")
