import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()

DIR = "/Game/Character/Darius/Retarget"

L("=== 与 Retarget source/target 有关的 unreal 名字 ===")
for n in sorted(dir(unreal)):
    if n.startswith("_"):
        continue
    if any(k in n for k in ("RetargetSource", "RetargetTarget", "SourceOrTarget", "RetargetMode")):
        c = getattr(unreal, n)
        try:
            L("   unreal.%-34s %s" % (n, [m for m in dir(c) if not m.startswith("_")][:12]))
        except Exception:
            L("   unreal.%s" % n)

# ---------------------------------------------------------------- 创建 IKRetargeter
name = "RTG_LOL_to_Darius"
path = DIR + "/" + name
rtg = eal.load_asset(path) if eal.does_asset_exist(path) else None
if rtg is None:
    fac = unreal.IKRetargetFactory()
    rtg = at.create_asset(name, DIR, unreal.IKRetargeter, fac)
    L("")
    L("create_asset -> %s" % rtg)
L("rtg = %s (%s)" % (rtg.get_name() if rtg else None, rtg.get_class().get_name() if rtg else None))

if rtg is None:
    raise SystemExit("IKRetargeter 创建失败")

ctrl = unreal.IKRetargeterController.get_controller(rtg)
L("ctrl = %s" % ctrl)
ms = [m for m in dir(ctrl) if not m.startswith("_")]
L("ctrl 成员 %d 个：%s" % (len(ms), ", ".join(ms)))

src = eal.load_asset(DIR + "/IK_LOL_Source")
tgt = eal.load_asset(DIR + "/IK_Darius_Target")
L("")
L("src rig = %s / tgt rig = %s" % (src, tgt))

L("")
L("=== 尝试 set_ik_rig（探测签名）===")
cands = []
enum = getattr(unreal, "RetargetSourceOrTarget", None)
if enum is not None:
    members = [m for m in dir(enum) if not m.startswith("_")]
    L("  RetargetSourceOrTarget 成员: %s" % members)

E = unreal.RetargetSourceOrTarget
# 实测签名：set_ik_rig(source_or_target, ik_rig) —— 枚举在前，IK Rig 在后
# （反过来会报 "Cannot nativize 'IKRigDefinition' as 'SourceOrTarget'"）
for label, sa, rig in (("SOURCE", E.SOURCE, src), ("TARGET", E.TARGET, tgt)):
    try:
        r = ctrl.set_ik_rig(sa, rig)
        L("  set_ik_rig(%s, rig) -> %s" % (label, r))
    except Exception as ex:
        LW("  set_ik_rig(%s) 失败: %s" % (label, ex))

L("  回读 get_ik_rig(SOURCE) = %s" % ctrl.get_ik_rig(E.SOURCE))
L("  回读 get_ik_rig(TARGET) = %s" % ctrl.get_ik_rig(E.TARGET))

L("")
L("=== 查找 AutoMap 链类型枚举 ===")
ams = [n for n in dir(unreal) if "AutoMap" in n]
L("  候选: %s" % ams)
T = getattr(unreal, "AutoMapChainType", None)
if T is not None:
    L("  成员: %s" % [m for m in dir(T) if not m.startswith("_")])

L("")
L("=== auto_map_chains(auto_map_type, force_remap) ===")
if T is not None:
    for m in ("EXACT", "FUZZY", "CLEAR"):
        v = getattr(T, m, None)
        if v is None:
            continue
        try:
            r = ctrl.auto_map_chains(v, True)
            L("  auto_map_chains(%s, True) -> %s" % (m, r))
        except Exception as ex:
            LW("  auto_map_chains(%s, True) : %s" % (m, ex))

L("")
L("=== 链设置（映射结果）===")
for label, args in (("get_all_chain_settings()", ()),
                    ("get_all_chain_settings(SOURCE)", (E.SOURCE,)),
                    ("get_all_chain_settings(TARGET)", (E.TARGET,))):
    try:
        cs = ctrl.get_all_chain_settings(*args)
        n = len(cs) if cs else 0
        L("  %s -> %d 条" % (label, n))
        for c in (cs or [])[:14]:
            L("      %s" % c)
        if n:
            break
    except Exception as ex:
        L("  %s : %s" % (label, ex))

L("")
L("=== 逐链配对检查（源链 -> 目标链）===")
for cn in ("Spine", "Neck", "Head", "LeftLeg", "RightLeg",
           "LeftClavicle", "RightClavicle", "LeftArm", "RightArm"):
    try:
        s = ctrl.get_source_chain(cn) if False else None
    except Exception:
        s = None
    try:
        st = ctrl.get_retarget_chain_settings(cn) if hasattr(ctrl, "get_retarget_chain_settings") else None
        L("  %-16s settings = %s" % (cn, st))
    except Exception as ex:
        L("  %-16s : %s" % (cn, ex))

eal.save_asset(path, only_if_is_dirty=False)
L("")
L("saved: %s" % path)
L("=== DONE ===")
