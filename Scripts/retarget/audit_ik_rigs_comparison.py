# -*- coding: utf-8 -*-
"""audit_ik_rigs_comparison —— 全面对比 IK_Darius 与 IK_LOL_Darius 的链结构与骨骼定义"""
import unreal

IK_TGT_PATH = "/Game/Character/Darius/IK/IK_Darius"
IK_SRC_PATH = "/Game/Character/Darius/IK/IK_LOL_Darius"

ik_tgt = unreal.load_object(None, IK_TGT_PATH)
ik_src = unreal.load_object(None, IK_SRC_PATH)

c_tgt = unreal.IKRigController.get_controller(ik_tgt)
c_src = unreal.IKRigController.get_controller(ik_src)

unreal.log("=== IK_Darius (Target) 全部链 ===")
unreal.log(f"Retarget Root: {c_tgt.get_retarget_root()}")
for ch in c_tgt.get_retarget_chains():
    s = c_tgt.get_retarget_chain_start_bone(ch.chain_name)
    e = c_tgt.get_retarget_chain_end_bone(ch.chain_name)
    g = c_tgt.get_retarget_chain_goal(ch.chain_name)
    unreal.log(f"  {str(ch.chain_name):<22} | start={str(s):<18} end={str(e):<18} goal={str(g)}")

unreal.log("\n=== IK_LOL_Darius (Source) 全部链 ===")
unreal.log(f"Retarget Root: {c_src.get_retarget_root()}")
for ch in c_src.get_retarget_chains():
    s = c_src.get_retarget_chain_start_bone(ch.chain_name)
    e = c_src.get_retarget_chain_end_bone(ch.chain_name)
    g = c_src.get_retarget_chain_goal(ch.chain_name)
    unreal.log(f"  {str(ch.chain_name):<22} | start={str(s):<18} end={str(e):<18} goal={str(g)}")
