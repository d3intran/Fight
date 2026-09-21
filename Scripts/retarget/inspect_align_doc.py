# -*- coding: utf-8 -*-
import unreal

rtg = unreal.load_object(None, "/Game/Character/Darius/IK/RTG_LOL_To_Darius")
c = unreal.IKRetargeterController.get_controller(rtg)
unreal.log(f"auto_align_all_bones doc: {c.auto_align_all_bones.__doc__}")
unreal.log(f"auto_align_bones doc: {c.auto_align_bones.__doc__}")
