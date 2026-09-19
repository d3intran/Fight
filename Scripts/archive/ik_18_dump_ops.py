# -*- coding: utf-8 -*-
"""枚举 op 栈，并把 Pelvis Motion op 的全部设置打出来。"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

rtg = eal.load_asset("/Game/Character/Darius/Retarget/RTG_LOL_to_Darius")
ctrl = unreal.IKRetargeterController.get_controller(rtg)

n = ctrl.get_num_retarget_ops()
L("op 数量 = %d" % n)
for i in range(n):
    nm = ctrl.get_op_name(i)
    en = ctrl.get_retarget_op_enabled(i)
    try:
        par = ctrl.get_parent_op_by_name(nm)
    except Exception:
        par = "?"
    L("  [%d] %-40s enabled=%-6s parent=%s" % (i, nm, en, par))

L("")
L("################ 重点：Pelvis / Root / FK 相关 op 的设置")
for i in range(n):
    nm = str(ctrl.get_op_name(i))
    if not any(k in nm.lower() for k in ("pelvis", "root", "fk", "chain")):
        continue
    L("")
    L("=== [%d] %s ===" % (i, nm))
    oc = ctrl.get_op_controller(i)
    if oc is None:
        LW("   get_op_controller 返回 None")
        continue
    props = [x for x in dir(oc) if not x.startswith("_")]
    shown = 0
    for p in sorted(props):
        if p in ("acquire_editor_element_handle", "call_method", "cast", "get_class",
                 "get_default_object", "get_editor_property", "get_fname", "get_full_name",
                 "get_name", "get_outer", "get_outermost", "get_package", "get_path_name",
                 "get_typed_outer", "get_world", "modify", "rename", "set_editor_property",
                 "set_editor_properties", "static_class", "is_editor_property_overridden",
                 "reset_editor_property", "does_property_states_exist",
                 "find_or_add_property_states", "is_package_external",
                 "get_support_asset_classes"):
            continue
        if p.startswith("scripted_"):
            continue
        try:
            v = oc.get_editor_property(p)
        except Exception:
            continue
        s = str(v)
        if len(s) > 200:
            s = s[:200] + "…"
        L("   %-46s = %s" % (p, s))
        shown += 1
    if not shown:
        LW("   没有可读属性；dir = %s" % ", ".join(sorted(props)[:40]))
L("=== DONE ===")
