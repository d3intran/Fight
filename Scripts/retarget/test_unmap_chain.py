# -*- coding: utf-8 -*-
import unreal

RTG_PATH = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, RTG_PATH)
c = unreal.IKRetargeterController.get_controller(rtg)

# Correct order: source_chain_name, target_chain_name
ok = c.set_source_chain(unreal.Name("None"), unreal.Name("Pelvis"))
unreal.log(f"Unmapped Pelvis ok={ok}, new val={c.get_source_chain(unreal.Name('Pelvis'))}")
