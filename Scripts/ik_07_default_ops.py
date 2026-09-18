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

L("=== 当前 Op Stack ===")


def dump_ops():
    try:
        n = ctrl.get_num_retarget_ops()
    except Exception as ex:
        L("   get_num_retarget_ops : %s" % ex)
        return 0
    L("   op 数 = %d" % n)
    for i in range(n):
        try:
            L("      [%d] %s" % (i, ctrl.get_op_name(i)))
        except Exception as ex:
            L("      [%d] <err %s>" % (i, ex))
    return n


n = dump_ops()

if n == 0:
    L("")
    L("=== add_default_ops() ===")
    for label, args in (("add_default_ops()", ()),):
        try:
            r = ctrl.add_default_ops(*args)
            L("   %s -> %s" % (label, r))
        except Exception as ex:
            LW("   %s : %s" % (label, ex))
    dump_ops()

    L("")
    L("=== assign_ik_rig_to_all_ops() ===")
    try:
        r = ctrl.assign_ik_rig_to_all_ops()
        L("   -> %s" % r)
    except Exception as ex:
        LW("   : %s" % ex)

    L("")
    L("=== run_op_initial_setup() ===")
    try:
        r = ctrl.run_op_initial_setup()
        L("   -> %s" % r)
    except Exception as ex:
        LW("   : %s" % ex)

L("")
L("=== auto_map_chains（EXACT / FUZZY）===")
for m in ("EXACT", "FUZZY"):
    try:
        ctrl.auto_map_chains(getattr(T, m), True)
        L("   %s 已执行" % m)
    except Exception as ex:
        LW("   %s : %s" % (m, ex))

L("")
L("=== 映射验证（多种 get_source_chain 签名）===")
TARGET_CHAINS = ("Spine", "Neck", "Head", "LeftLeg", "RightLeg",
                 "LeftClavicle", "RightClavicle", "LeftArm", "RightArm")
ok = 0
for cn in TARGET_CHAINS:
    got = None
    for desc, fn in (
        ("(name)", lambda c=cn: ctrl.get_source_chain(c)),
        ("(TARGET,name)", lambda c=cn: ctrl.get_source_chain(E.TARGET, c)),
        ("(name,TARGET)", lambda c=cn: ctrl.get_source_chain(c, E.TARGET)),
    ):
        try:
            got = fn()
            if got not in (None, "", "None"):
                L("   %-16s <- %-16s   [via %s]" % (cn, got, desc))
                ok += 1
                break
        except Exception:
            continue
    else:
        L("   %-16s <- None            <== 未映射" % cn)
L("   已映射 %d / %d" % (ok, len(TARGET_CHAINS)))

if ok == 0:
    L("")
    L("=== 尝试手动配对 set_source_chain ===")
    for cn in TARGET_CHAINS:
        for desc, args in (("(tgt,src)", (cn, cn)), ("(src,tgt)", (cn, cn))):
            try:
                r = ctrl.set_source_chain(*args)
                L("   set_source_chain%s %s -> %s" % (desc, cn, r))
                break
            except Exception as ex:
                last = ex
        else:
            LW("   %-16s 失败: %s" % (cn, last))
    L("")
    for cn in TARGET_CHAINS[:4]:
        try:
            L("   复查 %-16s <- %s" % (cn, ctrl.get_source_chain(cn)))
        except Exception as ex:
            L("   复查 %-16s : %s" % (cn, ex))

eal.save_asset(RTG_PATH, only_if_is_dirty=False)
L("")
L("saved")
L("=== DONE ===")
