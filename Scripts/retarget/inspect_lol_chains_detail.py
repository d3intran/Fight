# -*- coding: utf-8 -*-
import unreal

ik = unreal.load_object(None, "/Game/Character/Darius/IK/IK_LOL_Darius")
c = unreal.IKRigController.get_controller(ik)
chains = c.get_retarget_chains()
unreal.log("=== IK_LOL_Darius Chains Details ===")
for ch in chains:
    s = c.get_retarget_chain_start_bone(ch.chain_name)
    e = c.get_retarget_chain_end_bone(ch.chain_name)
    unreal.log(f"Chain: {str(ch.chain_name):<15} | Start: {str(s):<15} -> End: {str(e)}")
