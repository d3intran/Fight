import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

DIR = "/Game/Character/Darius/Retarget"
RTG_PATH = DIR + "/RTG_LOL_to_Darius"
E = unreal.RetargetSourceOrTarget
T = unreal.AutoMapChainType

rtg = eal.load_asset(RTG_PATH)
ctrl = unreal.IKRetargeterController.get_controller(rtg)
L("rtg = %s" % rtg.get_name())
L("get_ik_rig(SOURCE) = %s" % ctrl.get_ik_rig(E.SOURCE))
L("get_ik_rig(TARGET) = %s" % ctrl.get_ik_rig(E.TARGET))

TARGET_CHAINS = ("Spine", "Neck", "Head", "LeftLeg", "RightLeg",
                 "LeftClavicle", "RightClavicle", "LeftArm", "RightArm")


def dump_map(tag):
    L("")
    L("--- 映射（%s）---" % tag)
    ok = 0
    for cn in TARGET_CHAINS:
        try:
            s = ctrl.get_source_chain(cn)
        except Exception as ex:
            s = "<err %s>" % ex
        good = s not in (None, "", "None") and not str(s).startswith("<err")
        if good:
            ok += 1
        L("   %-16s <- %-16s %s" % (cn, s, "" if good else "  <== 未映射"))
    L("   已映射 %d / %d" % (ok, len(TARGET_CHAINS)))
    return ok


L("")
L("=== 当前状态 ===")
n0 = dump_map("before")

if n0 < len(TARGET_CHAINS):
    L("")
    L("=== 执行 auto_map_chains（只 EXACT 与 FUZZY，不用 CLEAR）===")
    for m in ("EXACT", "FUZZY"):
        v = getattr(T, m)
        try:
            ctrl.auto_map_chains(v, True)
            L("   auto_map_chains(%s, True) 已执行" % m)
        except Exception as ex:
            LW("   auto_map_chains(%s) : %s" % (m, ex))
    dump_map("after auto_map")

L("")
L("=== chain_settings 属性 ===")
for prop in ("chain_settings", "retarget_poses", "global_settings", "root_settings"):
    try:
        v = rtg.get_editor_property(prop)
        L("   %-20s = %s" % (prop, ("%d 项" % len(v)) if hasattr(v, "__len__") else v))
    except Exception as ex:
        L("   %-20s : %s" % (prop, ex))


L("")
L("=== 手动配对的接口探测 ===")
for m in ("get_source_chain", "set_source_chain", "get_retarget_chain_settings",
          "set_retarget_chain_settings", "get_all_chain_settings"):
    f = getattr(ctrl, m, None)
    L("   %-32s %s" % (m, "存在" if f else "不存在"))

L("")
L("=== 用 to_dict 读一条链的完整设置（LeftLeg）===")
try:
    st = ctrl.get_retarget_chain_settings("LeftLeg")
    try:
        L("   %s" % st.to_dict())
    except Exception:
        L("   %s" % st)
    for sub in ("fk", "ik", "speed_planting"):
        try:
            L("   %s = %s" % (sub, st.get_editor_property(sub)))
        except Exception as ex:
            L("   %s : %s" % (sub, ex))
except Exception as ex:
    LW("   %s" % ex)

eal.save_asset(RTG_PATH, only_if_is_dirty=False)
L("")
L("saved")
L("=== DONE ===")
