# -*- coding: utf-8 -*-
import unreal

rtg = unreal.load_object(None, "/Game/Character/Darius/IK/RTG_LOL_To_Darius")
c = unreal.IKRetargeterController.get_controller(rtg)

ik_tgt = unreal.load_object(None, "/Game/Character/Darius/IK/IK_Darius")
ik_src = unreal.load_object(None, "/Game/Character/Darius/IK/IK_LOL_Darius")

# Clean duplicate chains in both rigs
c_tgt = unreal.IKRigController.get_controller(ik_tgt)
for ch in list(c_tgt.get_retarget_chains()):
    if ch.chain_name == unreal.Name("Weapon_0"):
        c_tgt.remove_retarget_chain(ch.chain_name)
ik_tgt.modify()
unreal.EditorAssetLibrary.save_asset("/Game/Character/Darius/IK/IK_Darius", only_if_is_dirty=False)

c_src = unreal.IKRigController.get_controller(ik_src)
for ch in list(c_src.get_retarget_chains()):
    if ch.chain_name == unreal.Name("Weapon_0"):
        c_src.remove_retarget_chain(ch.chain_name)
ik_src.modify()
unreal.EditorAssetLibrary.save_asset("/Game/Character/Darius/IK/IK_LOL_Darius", only_if_is_dirty=False)

# Re-assign rigs to refresh RTG
c.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, ik_tgt)
c.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, ik_src)

# Now map Weapon
ok = c.set_source_chain(unreal.Name("Weapon"), unreal.Name("Weapon"))
unreal.log(f"After refresh, set_source_chain('Weapon', 'Weapon'): {ok}")
unreal.log(f"Weapon source chain is now: {c.get_source_chain(unreal.Name('Weapon'))}")

rtg.modify()
unreal.EditorAssetLibrary.save_asset("/Game/Character/Darius/IK/RTG_LOL_To_Darius", only_if_is_dirty=False)
