# -*- coding: utf-8 -*-
import unreal

rtg_path = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, rtg_path)
c = unreal.IKRetargeterController.get_controller(rtg)

unreal.log("=== IKRetargeterController chain mapping methods ===")
for attr in dir(c):
    if "chain" in attr.lower() or "map" in attr.lower():
        unreal.log(f"c.{attr}")
