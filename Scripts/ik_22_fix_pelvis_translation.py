# -*- coding: utf-8 -*-
"""把 Pelvis Motion op 的平移关掉，让 pelvis 保持目标骨架自己的 rest 高度。

证据（2026-09-18 实测，权威基线 = 骨架 rest pose）：
    rest pelvis 局部平移模长 = 1.0967
    旧动画 A_Darius_Idle1_TP  = 1.0967   <- 正确
    本轮产物 A_Darius_idle1   = 147.6323 <- 放大 134.6 倍
  其余 21 根骨与旧动画完全一致（比值 1.00）⇒ 只有 pelvis 这一根被写坏。
  结果：整条骨架被推到离原点 ~147 米处，Persona 预览与缩略图全是空的。

  先试过停用 "Root Motion" op —— **无效**，数值一字未变 ⇒ 写入方是 Pelvis Motion op。

对策：`translation_alpha = 0.0`。
  依据定稿计划「源本就是 in-place，不做 root motion 提取」；
  且源骨架 pelvis 的局部平移逐帧几乎恒定，关掉平移不会丢失有效信息。
  旋转不动（pelvis 的旋转本来就靠这个 op 传，不能停用整个 op）。
本脚本幂等。
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"
OP_NAME = "Pelvis Motion"

rtg = eal.load_asset(RTG)
ctrl = unreal.IKRetargeterController.get_controller(rtg)
idx = ctrl.get_index_of_op_by_name(OP_NAME)
L("%s 索引 = %s" % (OP_NAME, idx))
if idx is None or idx < 0:
    LW("找不到该 op")
    raise SystemExit(1)

oc = ctrl.get_op_controller(idx)
s = oc.get_settings()

L("")
L("=== 修改前 ===")
for p in ("translation_alpha", "rotation_alpha", "blend_to_source_translation",
          "scale_horizontal", "scale_vertical", "affect_ik_horizontal", "affect_ik_vertical"):
    try:
        L("  %-32s = %s" % (p, s.get_editor_property(p)))
    except Exception:
        pass

for p, v in (("translation_alpha", 0.0),
             ("blend_to_source_translation", 0.0),
             ("scale_horizontal", 1.0),
             ("scale_vertical", 1.0)):
    try:
        s.set_editor_property(p, v)
        L("  set %-30s <- %s" % (p, v))
    except Exception as ex:
        LW("  set %s 失败: %s" % (p, str(ex)[:80]))

oc.set_settings(s)
try:
    ctrl.run_op_initial_setup(idx)
except Exception as ex:
    LW("run_op_initial_setup: %s" % str(ex)[:90])

s2 = oc.get_settings()
L("")
L("=== 修改后 ===")
for p in ("translation_alpha", "rotation_alpha", "blend_to_source_translation"):
    try:
        L("  %-32s = %s" % (p, s2.get_editor_property(p)))
    except Exception:
        pass

L("")
L("存盘 -> %s" % eal.save_asset(RTG, only_if_is_dirty=False))
L("=== DONE ===")
