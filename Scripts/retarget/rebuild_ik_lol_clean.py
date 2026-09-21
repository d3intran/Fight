# -*- coding: utf-8 -*-
import unreal

eal = unreal.EditorAssetLibrary
IK_LOL_PATH = "/Game/Character/Darius/IK/IK_LOL_Darius"
ik_lol = unreal.load_object(None, IK_LOL_PATH)
c_lol = unreal.IKRigController.get_controller(ik_lol)

# 1. 彻底清除所有旧链
unreal.log("Purging all old chains in IK_LOL_Darius...")
for ch in list(c_lol.get_retarget_chains()):
    c_lol.remove_retarget_chain(ch.chain_name)

# 2. 添加精准 20 链
LOL_CHAINS = [
    ("Spine", "Spine1", "Spine2"),
    ("Neck", "Neck", "Neck"),
    ("Head", "Head", "Head"),
    ("LeftLeg", "L_Hip", "L_Foot"),
    ("LeftFoot", "L_Toe", "L_Toe"),
    ("RightLeg", "R_Hip", "R_Foot"),
    ("RightFoot", "R_Toe", "R_Toe"),
    ("LeftClavicle", "L_Clavicle", "L_Clavicle"),
    ("LeftArm", "L_Shoulder", "L_Hand"),
    ("RightClavicle", "R_Clavicle", "R_Clavicle"),
    ("RightArm", "R_Shoulder", "R_Hand"),
    ("LeftThumb", "L_Thumb1", "L_Thumb2"),
    ("LeftIndex", "L_Index1", "L_Index2"),
    ("LeftRing", "L_Ring1", "L_Ring2"),
    ("LeftPinky", "L_Pinky1", "L_Pinky2"),
    ("RightThumb", "R_Thumb1", "R_Thumb2"),
    ("RightIndex", "R_Index1", "R_Index2"),
    ("RightRing", "R_Ring1", "R_Ring2"),
    ("RightPinky", "R_Pinky1", "R_Pinky2"),
    ("Weapon", "Weapon", "Weapon"),
]

for ch_name, s_bone, e_bone in LOL_CHAINS:
    c_lol.add_retarget_chain(unreal.Name(ch_name), unreal.Name(s_bone), unreal.Name(e_bone), unreal.Name("None"))
    unreal.log(f"  Added chain: {ch_name} -> {s_bone} .. {e_bone}")

c_lol.set_retarget_root(unreal.Name("Pelvis"))
ik_lol.modify()
eal.save_asset(IK_LOL_PATH, only_if_is_dirty=False)
unreal.log(f"IK_LOL_Darius successfully rebuilt with {len(LOL_CHAINS)} chains!")
