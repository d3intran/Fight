# -*- coding: utf-8 -*-
import unreal

ik_mixamo = unreal.load_object(None, "/Game/Character/Darius/IK/IK_Mixamo")
if ik_mixamo:
    c = unreal.IKRigController.get_controller(ik_mixamo)
    unreal.log(f"IK_Mixamo Retarget Root: {c.get_retarget_root()}")
