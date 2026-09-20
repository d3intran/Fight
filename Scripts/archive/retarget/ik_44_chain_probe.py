# -*- coding: utf-8 -*-
"""探针：把 retargeter 的**链设置**逐条打出来（`get_all_chain_settings()` 是无参调用）。

目的：确认哪些目标链**没有源对应**。`auto_align_all_bones(CHAIN_TO_CHAIN)` 只对齐
「在链里、且不是链尾」的骨；链尾与未映射链的骨**偏移会留 0**，而实测正是这几根骨
（`clavicle_*` / `neck_01` / `head` / `hand_*` / `foot_*`）在 `ik_37` 里全部超门限。
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"
E = unreal.RetargetSourceOrTarget

rtg = eal.load_asset(RTG)
ctrl = unreal.IKRetargeterController.get_controller(rtg)


def call(fn, *a):
    try:
        return fn(*a)
    except Exception as ex:
        return "<ERR:%s>" % str(ex)[:90]


L("################ get_all_chain_settings()")
arr = call(ctrl.get_all_chain_settings)
L("   返回类型 %s，长度 %s" % (type(arr), len(arr) if hasattr(arr, "__len__") else "?"))
if isinstance(arr, (list, tuple)) and arr:
    first = arr[0]
    L("   元素类型 %s" % type(first))
    L("   可读字段: %s" % ", ".join(sorted([f for f in dir(first) if not f.startswith("_")])))
    L("")
    L("   %-20s %-20s %s" % ("链名", "源链名", "其余字段"))
    n_unmapped = 0
    for cs in arr:
        try:
            cn = str(cs.chain_name)
            sn = str(cs.source_chain_name)
        except Exception:
            L("   %s" % str(cs)[:110])
            continue
        extra = []
        for f in ("start_bone", "end_bone", "goal_bone", "chain_type", "ik_goal",
                  "settings", "rotation_mode", "translation_mode"):
            try:
                extra.append("%s=%s" % (f, getattr(cs, f)))
            except Exception:
                pass
        if not sn or sn in ("None", "NoneType"):
            n_unmapped += 1
        L("   %-20s %-20s %s" % (cn, sn, " ".join(extra)[:110]))
    L("")
    L("   ⇒ 无源对应的链 = %d / %d" % (n_unmapped, len(arr)))

L("")
L("################ get_source_chain 签名试探")
for args in (("Arm_L", E.TARGET), (E.TARGET, "Arm_L"), ("Arm_L",), ("Arm_L", E.SOURCE)):
    L("   get_source_chain%s -> %s" % (args, call(ctrl.get_source_chain, *args)))

L("")
L("################ 源/目标 IK Rig 的链（直接读资产）")
for tag, p in (("SOURCE", "/Game/Character/Darius/Retarget/IK_LOL_Source"),
               ("TARGET", "/Game/Character/Darius/Retarget/IK_Darius_Target")):
    ik = eal.load_asset(p)
    L("   ---- %s (%s)" % (tag, ik.get_name() if ik else "NOT FOUND"))
    if ik is None:
        continue
    try:
        arr2 = ik.get_editor_property("retarget_chain_settings")
        L("      retarget_chain_settings: %d 条" % len(arr2))
        for i, c in enumerate(arr2):
            try:
                L("        [%2d] %-18s %s -> %s" % (i, c.chain_name, c.start_bone, c.end_bone))
            except Exception:
                L("        [%2d] %s" % (i, str(c)[:90]))
    except Exception as ex:
        LW("      读 retarget_chain_settings 失败: %s" % str(ex)[:110])
L("=== DONE ===")
