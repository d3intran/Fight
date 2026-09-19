# -*- coding: utf-8 -*-
"""把 op 栈恢复成「已知合理」基线配置，供下一轮修复后直接复用。

基线（2026-09-18 实测确定）：
  [0] Pelvis Motion  enabled=True, translation_alpha=0.0
        —— 保留 pelvis 旋转重定向（这是唯一传 pelvis 旋转的 op，不能停），
           关掉它的平移（源本就是 in-place）。
  [1] FK Chains      enabled=True（默认）  —— 21 根骨的 rotation 走这里，实测正确
  [2] Run IK Rig     enabled=True（默认）
  [3] Root Motion    enabled=False        —— 它的 root_motion_source=COPY_FROM_SOURCE_ROOT
        且把源根骨认成了最外层 NULL 节点 `skinned_mesh`（不是我们真正的 `Root`）。
        定稿计划明确「不做 root motion 提取」，故停用。
  [4] Remap Curves   enabled=True（默认）

⚠️ 遗留未解：目标 pelvis 的**平移**无论怎么配 op 都是 `rest × 100`
   （重定向器把组件空间 cm 值写进了骨骼局部槽位），
   导致角色被推到离原点约 147 米处、预览全空。
   下一步的两个候选修法见 `Docs/Retarget/HANDOFF.md` §4。
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"
rtg = eal.load_asset(RTG)
ctrl = unreal.IKRetargeterController.get_controller(rtg)

WANT_ENABLED = {"Pelvis Motion": True, "FK Chains": True, "Run IK Rig": True,
                "Root Motion": False, "Remap Curves": True}

L("=== 应用基线 ===")
for i in range(ctrl.get_num_retarget_ops()):
    nm = str(ctrl.get_op_name(i))
    want = WANT_ENABLED.get(nm)
    cur = ctrl.get_retarget_op_enabled(i)
    if want is None:
        L("  [%d] %-20s 未在基线表中，保持 enabled=%s" % (i, nm, cur))
        continue
    if cur != want:
        r = ctrl.set_retarget_op_enabled(i, want)
        L("  [%d] %-20s %s -> %s  (%s)" % (i, nm, cur, want, r))
    else:
        L("  [%d] %-20s 已是 %s" % (i, nm, cur))
    try:
        ctrl.run_op_initial_setup(i)
    except Exception:
        pass

# Pelvis Motion 的 translation_alpha 单独确认
idx = ctrl.get_index_of_op_by_name("Pelvis Motion")
if idx is not None and idx >= 0:
    oc = ctrl.get_op_controller(idx)
    s = oc.get_settings()
    if abs(s.get_editor_property("translation_alpha") - 0.0) > 1e-6:
        s.set_editor_property("translation_alpha", 0.0)
        oc.set_settings(s)
        L("  Pelvis Motion.translation_alpha -> 0.0")
    else:
        L("  Pelvis Motion.translation_alpha 已是 0.0")

L("")
L("=== 最终状态 ===")
for i in range(ctrl.get_num_retarget_ops()):
    L("  [%d] %-20s enabled=%s" % (i, ctrl.get_op_name(i), ctrl.get_retarget_op_enabled(i)))
L("")
L("存盘 -> %s" % eal.save_asset(RTG, only_if_is_dirty=False))
L("=== DONE ===")
