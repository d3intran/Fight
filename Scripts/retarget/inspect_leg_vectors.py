# -*- coding: utf-8 -*-
import unreal

AL = unreal.AnimationLibrary

rtg = unreal.load_object(None, "/Game/Character/Darius/IK/RTG_LOL_To_Darius")
c = unreal.IKRetargeterController.get_controller(rtg)

src_mesh = c.get_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE)
tgt_mesh = c.get_preview_mesh(unreal.RetargetSourceOrTarget.TARGET)

unreal.log("=== Source Leg Bones in Reference Pose ===")
sk_src = src_mesh.get_editor_property("skeleton")
sk_tgt = tgt_mesh.get_editor_property("skeleton")

for bn in ["Root", "Pelvis", "L_Hip", "L_KneeLower", "L_Foot", "R_Hip", "R_KneeLower", "R_Foot"]:
    loc = src_mesh.get_ref_pose_position(src_mesh.find_bone_index(bn)) if hasattr(src_mesh, "get_ref_pose_position") else None
    unreal.log(f"Source {bn}: {loc}")

# Compare bone directions in component space
skcomp_src = unreal.new_object(unreal.SkeletalMeshComponent)
skcomp_src.set_skeletal_mesh(src_mesh)

skcomp_tgt = unreal.new_object(unreal.SkeletalMeshComponent)
skcomp_tgt.set_skeletal_mesh(tgt_mesh)

for prefix, (b_hip, b_knee, b_foot) in [("L", ("L_Hip", "L_KneeLower", "L_Foot")), ("R", ("R_Hip", "R_KneeLower", "R_Foot"))]:
    p_hip = skcomp_src.get_bone_position_by_name(unreal.Name(b_hip), unreal.BoneSpaces.COMPONENT_SPACE)
    p_knee = skcomp_src.get_bone_position_by_name(unreal.Name(b_knee), unreal.BoneSpaces.COMPONENT_SPACE)
    p_foot = skcomp_src.get_bone_position_by_name(unreal.Name(b_foot), unreal.BoneSpaces.COMPONENT_SPACE)
    unreal.log(f"Source {prefix} Hip: {p_hip}")
    unreal.log(f"Source {prefix} Knee: {p_knee}")
    unreal.log(f"Source {prefix} Foot: {p_foot}")
    v_thigh = p_knee - p_hip
    v_calf = p_foot - p_knee
    unreal.log(f"  v_{prefix}_thigh: {v_thigh} (norm: {v_thigh.normal()})")
    unreal.log(f"  v_{prefix}_calf:  {v_calf} (norm: {v_calf.normal()})")
