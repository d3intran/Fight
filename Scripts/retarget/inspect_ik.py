# -*- coding: utf-8 -*-
import unreal

eal = unreal.EditorAssetLibrary

unreal.log("=== IK Rigs ===")
for p in ["/Game/Character/Darius/IK/IK_Darius", "/Game/Character/Darius/Retarget/IK_Darius_Target", "/Game/Character/Darius/IK/RTG_Darius"]:
    o = unreal.load_object(None, p)
    if o:
        unreal.log(f"Loaded: {p} ({o.get_class().get_name()})")
        if isinstance(o, unreal.IKRetargeter):
            c = unreal.IKRetargeterController.get_controller(o)
            src_ik = c.get_ik_rig(unreal.RetargetSourceOrTarget.SOURCE)
            tgt_ik = c.get_ik_rig(unreal.RetargetSourceOrTarget.TARGET)
            unreal.log(f"   RTG Source IK: {src_ik.get_path_name() if src_ik else 'None'}")
            unreal.log(f"   RTG Target IK: {tgt_ik.get_path_name() if tgt_ik else 'None'}")
