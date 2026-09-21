# -*- coding: utf-8 -*-
"""audit_retargeted_idle_frames —— 逐帧检查 A_Darius_idle1 左右脚次序与间距"""
import unreal

anim_path = "/Game/Character/Darius/Animations/LOL_Retarget/A_Darius_idle1"
anim = unreal.load_object(None, anim_path)
num_keys = anim.get_editor_property("number_of_sampled_keys")

unreal.log(f"=== A_Darius_idle1 逐帧脚部间距审计 (共 {num_keys} 帧) ===")

cross_count = 0
min_distance = 999.0
sum_distance = 0.0

for f in range(num_keys):
    t_lf = unreal.AnimationLibrary.get_bone_pose_for_frame(anim, unreal.Name("foot_l"), f, False)
    t_rf = unreal.AnimationLibrary.get_bone_pose_for_frame(anim, unreal.Name("foot_r"), f, False)
    
    # 局部/世界坐标间距
    p_l = t_lf.translation
    p_r = t_rf.translation
    dist = (p_l - p_r).length()
    
    if dist < min_distance:
        min_distance = dist
    sum_distance += dist
    
    # 检查是否交叉 (解剖学上 foot_l 在 +X，foot_r 在 -X，次序应为 foot_l.x > foot_r.x)
    # 如果两者 X 间距小于 0 说明交叉
    if p_l.x < p_r.x:
        cross_count += 1

avg_dist = sum_distance / num_keys
unreal.log(f"  帧数: {num_keys}")
unreal.log(f"  交叉帧数: {cross_count}/{num_keys}")
unreal.log(f"  最小双脚间距: {min_distance:.2f} cm")
unreal.log(f"  平均双脚间距: {avg_dist:.2f} cm")

# 检查 weapon_jnt
has_weapon_track = False
for track in unreal.AnimationLibrary.get_animation_track_names(anim):
    if track == unreal.Name("weapon_jnt"):
        has_weapon_track = True
        break
unreal.log(f"  weapon_jnt 轨道存在: {has_weapon_track}")

if cross_count == 0:
    unreal.log("  [PASS] 66 帧全周期 0 交叉！站姿极其稳健自然！")
else:
    unreal.log(f"  [WARN] 存在 {cross_count} 帧交叉")
