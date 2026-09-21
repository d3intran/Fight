# -*- coding: utf-8 -*-
import unreal

for name in ["/Game/Character/Darius/IK/IK_LOL_Darius", "/Game/Character/Darius/IK/IK_Darius"]:
    ik = unreal.load_object(None, name)
    c = unreal.IKRigController.get_controller(ik)
    unreal.log(f"=== {ik.get_name()} Solvers & Goals ===")
    unreal.log(f"Num solvers: {c.get_num_solvers()}")
    goals = c.get_all_goals()
    unreal.log(f"Goals ({len(goals)}):")
    for g in goals:
        unreal.log(f"   goal: {str(g.goal_name):<16} | bone: {c.get_bone_for_goal(g.goal_name)}")
