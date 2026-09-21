# -*- coding: utf-8 -*-
import unreal

anim_path = "/Game/Character/Darius/Animations/LOL_Retarget/A_Darius_idle1"
anim = unreal.load_object(None, anim_path)

# 检查大腿与手臂骨骼的旋转
unreal.log("=== A_Darius_idle1 关键骨骼旋转抽样 (Frame 0) ===")
for b in ["thigh_l", "thigh_r", "upperarm_l", "upperarm_r", "spine_01", "weapon_jnt"]:
    t = unreal.AnimationLibrary.get_bone_pose_for_frame(anim, unreal.Name(b), 0, False)
    rot = t.rotation.rotator()
    unreal.log(f"  {b:<14} rot=(pitch={rot.pitch:6.2f}, yaw={rot.yaw:6.2f}, roll={rot.roll:6.2f}) loc=({t.translation.x:6.2f}, {t.translation.y:6.2f}, {t.translation.z:6.2f})")
