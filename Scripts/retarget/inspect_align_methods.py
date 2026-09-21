# -*- coding: utf-8 -*-
import unreal

rtg = unreal.load_object(None, "/Game/Character/Darius/IK/RTG_LOL_To_Darius")
c = unreal.IKRetargeterController.get_controller(rtg)
unreal.log("=== auto align methods on IKRetargeterController ===")
for attr in dir(c):
    if "align" in attr.lower():
        unreal.log(f"c.{attr}")
