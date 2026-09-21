# -*- coding: utf-8 -*-
import unreal

ik = unreal.load_object(None, "/Game/Character/Darius/IK/IK_LOL_Darius")
c = unreal.IKRigController.get_controller(ik)
unreal.log("=== IKRigController methods ===")
for attr in dir(c):
    if "chain" in attr.lower():
        unreal.log(f"c.{attr}")
