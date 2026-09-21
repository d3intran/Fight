# -*- coding: utf-8 -*-
import unreal

RTG_PATH = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, RTG_PATH)
c = unreal.IKRetargeterController.get_controller(rtg)

unreal.log(f"Num ops: {c.get_num_retarget_ops()}")
for i in range(c.get_num_retarget_ops()):
    op_name = c.get_op_name(i)
    unreal.log(f"  Op {i}: {op_name}")
