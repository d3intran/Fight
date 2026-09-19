# -*- coding: utf-8 -*-
"""关掉 IK Retargeter 里那个错误的 Root Motion op。

背景（2026-09-18 实测）：
  `add_default_ops()` 会加 5 个 op，其中 "Root Motion" 默认启用，且
  `root_motion_source = COPY_FROM_SOURCE_ROOT`。它把**源骨架的根骨位移**灌进目标骨架。
  但源骨架的"根"被它认成了 Blender 导出的最外层 NULL 节点 `skinned_mesh`
  （不是我们真正的 `Root`），于是目标 pelvis 的局部平移被放大 **134.6 倍**：

      骨名        旧产物|T|     本轮|T|     比值
      pelvis      1.0967      147.6323    134.61   <-- 只有这一根错
      spine_01    0.1083        0.1083      1.00
      ...（另外 21 根全部 1.00）

  后果：整条骨架被推到离原点约 147 米处 ⇒ Persona 预览里**什么都看不见**，
  内容浏览器缩略图渲染成空棋盘格。

对策：按定稿计划「源本就是 in-place，不做 root motion 提取」⇒ 直接停用该 op。
本脚本幂等，可反复跑。
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"
OP_NAME = "Root Motion"

rtg = eal.load_asset(RTG)
ctrl = unreal.IKRetargeterController.get_controller(rtg)

L("=== 修改前 ===")
n = ctrl.get_num_retarget_ops()
for i in range(n):
    L("  [%d] %-20s enabled=%s" % (i, ctrl.get_op_name(i), ctrl.get_retarget_op_enabled(i)))

try:
    idx = ctrl.get_index_of_op_by_name(OP_NAME)
except Exception as ex:
    LW("get_index_of_op_by_name 失败: %s" % str(ex)[:120])
    raise SystemExit(1)

L("")
L("%s 的索引 = %s" % (OP_NAME, idx))
if idx is None or idx < 0:
    LW("找不到该 op，可能名字变了。")
    raise SystemExit(1)

r = ctrl.set_retarget_op_enabled(idx, False)
L("set_retarget_op_enabled(%s, False) -> %s" % (idx, r))
try:
    ctrl.run_op_initial_setup(idx)
except Exception as ex:
    LW("run_op_initial_setup: %s" % str(ex)[:100])

L("")
L("=== 修改后 ===")
for i in range(ctrl.get_num_retarget_ops()):
    L("  [%d] %-20s enabled=%s" % (i, ctrl.get_op_name(i), ctrl.get_retarget_op_enabled(i)))

L("")
L("存盘 -> %s" % eal.save_asset(RTG, only_if_is_dirty=False))
L("=== DONE ===")
