# -*- coding: utf-8 -*-
import unreal

ik = unreal.load_object(None, "/Game/Character/Darius/IK/IK_LOL_Darius")
c = unreal.IKRigController.get_controller(ik)
unreal.log(f"add_retarget_chain doc: {c.add_retarget_chain.__doc__}")
