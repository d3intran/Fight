# -*- coding: utf-8 -*-
"""读取 IK Retargeter 的 op 栈设置，定位 pelvis 平移被放大的那一项。"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"
rtg = eal.load_asset(RTG)
ctrl = unreal.IKRetargeterController.get_controller(rtg)

L("=== IKRetargeterController 里与 op 有关的接口 ===")
L("  %s" % ", ".join(sorted([x for x in dir(ctrl) if "op" in x.lower()])))

getter = None
for name in ("get_ops", "get_all_ops", "get_op_stack", "get_controller_ops"):
    if hasattr(ctrl, name):
        getter = name
        break
L("  用 getter = %s" % getter)

ops = None
if getter:
    try:
        ops = getattr(ctrl, getter)()
    except Exception as ex:
        LW("  调用失败: %s" % str(ex)[:120])

if ops:
    L("")
    L("=== op 列表（共 %d 个）===" % len(ops))
    for i, op in enumerate(ops):
        try:
            nm = op.get_class().get_name()
        except Exception:
            nm = str(type(op))
        try:
            en = op.get_editor_property("is_enabled")
        except Exception:
            en = "?"
        L("  [%d] %-42s enabled=%s" % (i, nm, en))
        # 打印所有可读的编辑器属性
        props = [x for x in dir(op) if not x.startswith("_")]
        skip = {"acquire_editor_element_handle", "call_method", "cast", "get_class",
                "get_default_object", "get_editor_property", "get_fname", "get_full_name",
                "get_name", "get_outer", "get_outermost", "get_package", "get_path_name",
                "get_typed_outer", "get_world", "modify", "rename", "set_editor_property",
                "static_class", "set_editor_properties", "is_editor_property_overridden",
                "reset_editor_property", "does_property_states_exist", "find_or_add_property_states",
                "is_package_external", "get_support_asset_classes", "scripted_execute_pipeline"}
        for p in sorted(props):
            if p in skip or p.startswith("scripted_"):
                continue
            try:
                v = op.get_editor_property(p)
            except Exception:
                continue
            s = str(v)
            if len(s) > 160:
                s = s[:160] + "…"
            L("        %-40s = %s" % (p, s))
else:
    # 退路：直接从资产上找 op 栈
    L("  改用资产属性探测")
    L("  retargeter attrs: %s" % ", ".join(sorted([x for x in dir(rtg) if "op" in x.lower() or "stack" in x.lower()])))
    for prop in ("op_stack", "ops", "retarget_ops"):
        try:
            L("  %s = %s" % (prop, rtg.get_editor_property(prop)))
        except Exception as ex:
            L("  %s : %s" % (prop, str(ex)[:100]))
L("=== DONE ===")
