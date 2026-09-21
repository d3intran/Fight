# -*- coding: utf-8 -*-
import unreal

c = unreal.IKRigController.get_controller(unreal.load_object(None, "/Game/Character/Darius/IK/IK_LOL_Darius"))

unreal.log("=== 重新导入后 SK_LOL_Darius 参考姿态骨骼坐标 ===")
for b in ["Pelvis", "L_Hip", "R_Hip", "L_KneeLower", "R_KneeLower", "L_Foot", "R_Foot", "L_Toe", "R_Toe", "L_Shoulder", "R_Shoulder", "L_Hand", "R_Hand", "Weapon"]:
    try:
        t = c.get_ref_pose_transform_of_bone(unreal.Name(b))
        unreal.log(f"  {b:<14} loc=({t.translation.x:7.2f}, {t.translation.y:7.2f}, {t.translation.z:7.2f})")
    except Exception as ex:
        unreal.log(f"  {b:<14} error {ex}")

# 检查左右脚 Y 坐标对称性
t_lf = c.get_ref_pose_transform_of_bone(unreal.Name("L_Foot"))
t_rf = c.get_ref_pose_transform_of_bone(unreal.Name("R_Foot"))
delta_y = abs(t_lf.translation.y - t_rf.translation.y)
unreal.log(f"\n双脚前后差 (|L_Foot.y - R_Foot.y|) = {delta_y:.2f} cm")

# 检查脚尖朝向向量
t_lt = c.get_ref_pose_transform_of_bone(unreal.Name("L_Toe"))
v_toe = t_lt.translation - t_lf.translation
unreal.log(f"L_Foot -> L_Toe 向量 = ({v_toe.x:.2f}, {v_toe.y:.2f}, {v_toe.z:.2f})")
