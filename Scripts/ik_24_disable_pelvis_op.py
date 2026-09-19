# -*- coding: utf-8 -*-
"""隔离实验：直接停用 Pelvis Motion op，看 pelvis 的平移是否回到 rest 值。

已知：
  translation_alpha=0 后 pelvis |T| 从 147.63 变成 109.67 = **rest 值 1.0967 × 100**。
  100 正好是目标根骨 `darius_godking_mesh_LOD0_Skeleton` 的 FBX 米->厘米缩放。
  ⇒ 怀疑该 op 把「目标 pelvis 的组件空间(cm)平移」写进了「骨骼局部(根骨单位)槽位」。
  ⇒ 若停用后 pelvis |T| 回到 1.0967，就确认写入方是这个 op。
代价：pelvis 的旋转也会一起丢（本 op 是唯一传 pelvis 旋转的地方），
      下一步再决定是否给 pelvis 建独立 FK 链把旋转拿回来。
本脚本幂等。
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"
rtg = eal.load_asset(RTG)
ctrl = unreal.IKRetargeterController.get_controller(rtg)

L("=== 修改前 ===")
for i in range(ctrl.get_num_retarget_ops()):
    L("  [%d] %-20s enabled=%s" % (i, ctrl.get_op_name(i), ctrl.get_retarget_op_enabled(i)))

idx = ctrl.get_index_of_op_by_name("Pelvis Motion")
L("")
L("Pelvis Motion 索引 = %s" % idx)
if idx is None or idx < 0:
    raise SystemExit(1)
L("set_retarget_op_enabled(%s, False) -> %s" % (idx, ctrl.set_retarget_op_enabled(idx, False)))
try:
    ctrl.run_op_initial_setup(idx)
except Exception as ex:
    LW("run_op_initial_setup: %s" % str(ex)[:90])

L("")
L("=== 修改后 ===")
for i in range(ctrl.get_num_retarget_ops()):
    L("  [%d] %-20s enabled=%s" % (i, ctrl.get_op_name(i), ctrl.get_retarget_op_enabled(i)))
L("")
L("存盘 -> %s" % eal.save_asset(RTG, only_if_is_dirty=False))
L("=== DONE ===")
