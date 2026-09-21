# -*- coding: utf-8 -*-
import unreal

ik_darius = unreal.load_object(None, "/Game/Character/Darius/IK/IK_Darius")
if ik_darius:
    c = unreal.IKRigController.get_controller(ik_darius)
    chains = c.get_retarget_chains()
    unreal.log("=== IK_Darius Retarget Chains ===")
    if chains:
        unreal.log(f"First chain dict: {chains[0].to_dict()}")
        for ch in chains[:5]:
            d = ch.to_dict()
            unreal.log(f"Chain: {d.get('chain_name')} | Start: {d.get('start_bone')} -> End: {d.get('end_bone')}")
    root = c.get_retarget_root()
    unreal.log(f"Retarget Root: {root}")
