# -*- coding: utf-8 -*-
"""选项 B：把目标 retarget root 提到与源同层级，并让 pelvis 走普通 FK 链。

假设（可证伪）：
  目标 pelvis 的平移被写成 `rest × 100`，是因为**重定向器写 retarget root 的平移时
  没有把祖先骨的 100× 缩放算进去**。另外 21 根骨走 FK Chains 路径，
  `translation_mode: None` ⇒ 平移精确等于 rest（实测比值 1.00）。

做法：
  1. 目标 IK Rig 的 retarget root：`pelvis` → `root`
     （这样就和源的 `Root` 同层级了：源的 `Root` 上面只有 ×100 的 skinned_mesh，
       目标的 `root` 上面也只有 ×100 的 darius_godking_mesh_LOD0_Skeleton）
  2. 两边各加一条 `Pelvis` 单骨链（目标 `pelvis→pelvis`，源 `Pelvis→Pelvis`）
     ⇒ pelvis 变成普通 FK 骨，走那条已被证明正确的路径
  3. 重映射 + 重建各 op 的内部设置

幂等，可反复跑。
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

RIGDIR = "/Game/Character/Darius/Retarget"
SRC_RIG = RIGDIR + "/IK_LOL_Source"
TGT_RIG = RIGDIR + "/IK_Darius_Target"
RTG = RIGDIR + "/RTG_LOL_to_Darius"

WANT = {
    "IK_LOL_Source": {"root": "Root", "chains": {"Pelvis": ("Pelvis", "Pelvis")}},
    "IK_Darius_Target": {"root": "root", "chains": {"Pelvis": ("pelvis", "pelvis")}},
}

# ---------------------------------------------------------------- 1) 两套 IK Rig
for path, spec in ((SRC_RIG, WANT["IK_LOL_Source"]), (TGT_RIG, WANT["IK_Darius_Target"])):
    rig = eal.load_asset(path)
    L("")
    L("=" * 72)
    L("### %s" % path.split("/")[-1])
    L("=" * 72)
    if rig is None:
        LW("  加载失败")
        raise SystemExit(1)
    ctrl = unreal.IKRigController.get_controller(rig)

    try:
        L("  当前 retarget root = %s" % ctrl.get_retarget_root())
    except Exception as ex:
        L("  读取 root 失败: %s" % str(ex)[:80])

    have = set()
    for c in (ctrl.get_retarget_chains() or []):
        try:
            have.add(str(c.get_editor_property("chain_name")))
        except Exception:
            pass

    L("  现有链 = %d : %s" % (len(have), sorted(have)))

    for nm, (s, e) in spec["chains"].items():
        if nm in have:
            L("  链 %-10s 已存在，跳过" % nm)
            continue
        try:
            r = ctrl.add_retarget_chain(nm, s, e, "")
            L("  add_retarget_chain(%-8s, %s -> %s) -> %s" % (nm, s, e, r))
        except Exception as ex:
            LW("  add 失败: %s" % str(ex)[:120])

    try:
        L("  set_retarget_root(%s) -> %s" % (spec["root"], ctrl.set_retarget_root(spec["root"])))
    except Exception as ex:
        LW("  set_retarget_root 失败: %s" % str(ex)[:120])

    L("  保存 -> %s" % eal.save_asset(path, only_if_is_dirty=False))

# ---------------------------------------------------------------- 2) 重映射
L("")
L("=" * 72)
L("### 重映射链")
L("=" * 72)
rtg = eal.load_asset(RTG)
rctrl = unreal.IKRetargeterController.get_controller(rtg)

L("  op 数 = %d" % rctrl.get_num_retarget_ops())
try:
    rctrl.auto_map_chains(unreal.AutoMapChainType.EXACT, True)
    L("  auto_map_chains(EXACT, force=True) OK")
except Exception as ex:
    LW("  auto_map_chains 失败: %s" % str(ex)[:150])

L("")
L("  各 op 的 run_op_initial_setup：")
for i in range(rctrl.get_num_retarget_ops()):
    try:
        rctrl.run_op_initial_setup(i)
        L("    [%d] %-20s OK" % (i, rctrl.get_op_name(i)))
    except Exception as ex:
        LW("    [%d] %-20s %s" % (i, rctrl.get_op_name(i), str(ex)[:80]))

# ---------------------------------------------------------------- 3) 复核
L("")
L("=" * 72)
L("### 复核：映射 + FK 链设置")
L("=" * 72)
CHECK = ("Spine", "Neck", "Head", "Pelvis", "LeftLeg", "RightLeg",
         "LeftClavicle", "RightClavicle", "LeftArm", "RightArm")
ok = 0
for cn in CHECK:
    try:
        s = rctrl.get_source_chain(cn)
    except Exception as ex:
        s = "<err %s>" % str(ex)[:40]
    good = s not in (None, "", "None") and not str(s).startswith("<err")
    if good:
        ok += 1
    L("   %-16s <- %-16s %s" % (cn, s, "" if good else "  <== 未映射"))
L("   已映射 %d / %d" % (ok, len(CHECK)))

fk_idx = rctrl.get_index_of_op_by_name("FK Chains")
L("")
L("  FK Chains op 索引 = %s" % fk_idx)
if fk_idx is not None and fk_idx >= 0:
    oc = rctrl.get_op_controller(fk_idx)
    s = oc.get_settings()
    try:
        chains = s.get_editor_property("chains_to_retarget")
        for c in chains:
            try:
                nm = c.get_editor_property("target_chain_name")
                tm = c.get_editor_property("translation_mode")
                rm = c.get_editor_property("rotation_mode")
                en = c.get_editor_property("enable_fk")
                L("    %-22s fk=%-6s rot=%-14s trans=%s" % (nm, en, rm, tm))
            except Exception:
                L("    %s" % c)
    except Exception as ex:
        LW("    读 chains_to_retarget 失败: %s" % str(ex)[:110])

L("")
L("  保存 retargeter -> %s" % eal.save_asset(RTG, only_if_is_dirty=False))
L("=== DONE ===")
