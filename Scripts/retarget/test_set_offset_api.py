# -*- coding: utf-8 -*-
import unreal

rtg_path = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
rtg = unreal.load_object(None, rtg_path)
c = unreal.IKRetargeterController.get_controller(rtg)

unreal.log(f"set_root_offset_in_retarget_pose doc: {c.set_root_offset_in_retarget_pose.__doc__}")

for attr in dir(c):
    if "offset" in attr.lower():
        unreal.log(f"c.{attr}")
