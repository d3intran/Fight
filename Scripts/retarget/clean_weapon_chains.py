# -*- coding: utf-8 -*-
import unreal

eal = unreal.EditorAssetLibrary
ik_tgt = unreal.load_object(None, "/Game/Character/Darius/IK/IK_Darius")
c_tgt = unreal.IKRigController.get_controller(ik_tgt)

# Remove extra Weapon chains
for ch in list(c_tgt.get_retarget_chains()):
    if ch.chain_name in [unreal.Name("Weapon_0"), unreal.Name("Weapon_1"), unreal.Name("Weapon")]:
        c_tgt.remove_retarget_chain(ch.chain_name)
        unreal.log(f"Removed chain: {ch.chain_name}")

# Add single clean Weapon chain
c_tgt.add_retarget_chain(unreal.Name("Weapon"), unreal.Name("weapon_jnt"), unreal.Name("weapon_jnt"), unreal.Name("None"))
unreal.log("Added clean Weapon chain")

ik_tgt.modify()
eal.save_asset("/Game/Character/Darius/IK/IK_Darius", only_if_is_dirty=False)

# Map in RTG
rtg = unreal.load_object(None, "/Game/Character/Darius/IK/RTG_LOL_To_Darius")
c_rtg = unreal.IKRetargeterController.get_controller(rtg)
ok = c_rtg.set_source_chain(unreal.Name("Weapon"), unreal.Name("Weapon"))
unreal.log(f"Mapped Weapon chain: {ok}")
rtg.modify()
eal.save_asset("/Game/Character/Darius/IK/RTG_LOL_To_Darius", only_if_is_dirty=False)
