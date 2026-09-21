# -*- coding: utf-8 -*-
import unreal

RTG_PATH = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, RTG_PATH)
c = unreal.IKRetargeterController.get_controller(rtg)

unreal.log(f"Num ops: {c.get_num_retarget_ops()}")
for i in range(c.get_num_retarget_ops()):
    op = c.get_retarget_op_at_index(i)
    unreal.log(f"  Op {i}: {op.get_name() if op else 'None'} ({op.get_class().get_name() if op else ''})")
