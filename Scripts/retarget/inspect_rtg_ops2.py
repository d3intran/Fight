# -*- coding: utf-8 -*-
import unreal

rtg_old = unreal.load_object(None, "/Game/Character/Darius/IK/RTG_Darius")
c_old = unreal.IKRetargeterController.get_controller(rtg_old)
unreal.log("=== RTG_Darius Ops ===")
for i in range(c_old.get_num_retarget_ops()):
    # check properties of op
    op = rtg_old.get_editor_property("retarget_ops")[i]
    unreal.log(f"Op {i}: class={op.get_class().get_name()}")
