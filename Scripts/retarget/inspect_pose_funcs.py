# -*- coding: utf-8 -*-
import unreal

rtg_path = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, rtg_path)
c = unreal.IKRetargeterController.get_controller(rtg)

unreal.log("=== Pose Editing Functions ===")
for attr in dir(c):
    if "pose" in attr.lower():
        unreal.log(f"c.{attr}")
