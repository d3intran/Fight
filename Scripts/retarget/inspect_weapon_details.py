# -*- coding: utf-8 -*-
import unreal

rtg = unreal.load_object(None, "/Game/Character/Darius/IK/RTG_LOL_To_Darius")
c = unreal.IKRetargeterController.get_controller(rtg)

ik_tgt = c.get_ik_rig(unreal.RetargetSourceOrTarget.TARGET)
c_tgt = unreal.IKRigController.get_controller(ik_tgt)

for ch in c_tgt.get_retarget_chains():
    if "weapon" in str(ch.chain_name).lower():
        start = c_tgt.get_retarget_chain_start_bone(ch.chain_name)
        end = c_tgt.get_retarget_chain_end_bone(ch.chain_name)
        unreal.log(f"Target chain: '{ch.chain_name}' ({type(ch.chain_name)}), start='{start}', end='{end}'")

ik_src = c.get_ik_rig(unreal.RetargetSourceOrTarget.SOURCE)
c_src = unreal.IKRigController.get_controller(ik_src)
for ch in c_src.get_retarget_chains():
    if "weapon" in str(ch.chain_name).lower():
        start = c_src.get_retarget_chain_start_bone(ch.chain_name)
        end = c_src.get_retarget_chain_end_bone(ch.chain_name)
        unreal.log(f"Source chain: '{ch.chain_name}' ({type(ch.chain_name)}), start='{start}', end='{end}'")
