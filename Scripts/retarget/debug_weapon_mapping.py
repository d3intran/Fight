# -*- coding: utf-8 -*-
import unreal

RTG_PATH = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, RTG_PATH)
c = unreal.IKRetargeterController.get_controller(rtg)

ok = c.set_source_chain(unreal.Name("Weapon"), unreal.Name("Weapon"), op_name=unreal.Name("FK Chains"))
unreal.log(f"set_source_chain('Weapon', 'Weapon', op_name='FK Chains'): {ok}")
unreal.log(f"Current source chain for Weapon: {c.get_source_chain(unreal.Name('Weapon'))}")
