# -*- coding: utf-8 -*-
import unreal

ik_lol = unreal.load_object(None, "/Game/Character/Darius/IK/IK_LOL_Darius")
c_lol = unreal.IKRigController.get_controller(ik_lol)
unreal.log("IK_LOL_Darius chains:")
for ch in c_lol.get_retarget_chains():
    unreal.log(f"  {ch.chain_name}")
