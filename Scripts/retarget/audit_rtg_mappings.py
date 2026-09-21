# -*- coding: utf-8 -*-
import unreal

RTG_PATH = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, RTG_PATH)
c = unreal.IKRetargeterController.get_controller(rtg)

ik_tgt = c.get_ik_rig(unreal.RetargetSourceOrTarget.TARGET)
c_tgt = unreal.IKRigController.get_controller(ik_tgt)

unreal.log("=== RTG Chain Mappings ===")
for ch in c_tgt.get_retarget_chains():
    target_chain = ch.chain_name
    source_chain = c.get_source_chain(target_chain)
    unreal.log(f"  Target: {str(target_chain):<25} -> Source: {str(source_chain):<25}")
