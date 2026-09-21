# -*- coding: utf-8 -*-
import unreal

rtg_path = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, rtg_path)
c = unreal.IKRetargeterController.get_controller(rtg)

unreal.log("=== RTG_LOL_To_Darius Op Stack & Chains ===")
unreal.log(f"Ops count: {c.get_num_retarget_ops()}")

# Check all ops
for i in range(c.get_num_retarget_ops()):
    unreal.log(f"Op {i}: {c.get_target_ik_rig_for_op(i)}")

# Check chains mapping
ik_src = c.get_ik_rig(unreal.RetargetSourceOrTarget.SOURCE)
ik_tgt = c.get_ik_rig(unreal.RetargetSourceOrTarget.TARGET)
c_src = unreal.IKRigController.get_controller(ik_src)
c_tgt = unreal.IKRigController.get_controller(ik_tgt)

src_chains = [ch.chain_name for ch in c_src.get_retarget_chains()]
tgt_chains = [ch.chain_name for ch in c_tgt.get_retarget_chains()]

unreal.log(f"Source Chains ({len(src_chains)}): {src_chains}")
unreal.log(f"Target Chains ({len(tgt_chains)}): {tgt_chains}")

for tc in tgt_chains:
    sc = c.get_source_chain(tc)
    unreal.log(f"  Target Chain '{tc}' -> Source Chain '{sc}'")
