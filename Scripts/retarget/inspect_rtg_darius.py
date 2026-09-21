# -*- coding: utf-8 -*-
import unreal

rtg = unreal.load_object(None, "/Game/Character/Darius/IK/RTG_Darius")
if rtg:
    c = unreal.IKRetargeterController.get_controller(rtg)
    unreal.log(f"RTG_Darius Target Root Offset: {c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.TARGET)}")
    unreal.log(f"RTG_Darius Source Root Offset: {c.get_root_offset_in_retarget_pose(unreal.RetargetSourceOrTarget.SOURCE)}")
    unreal.log(f"RTG_Darius target_mesh_offset: {rtg.get_editor_property('target_mesh_offset')}")
