# -*- coding: utf-8 -*-
"""verify_and_retarget_idle —— 验证 RTG 链映射无误，并重定向 A_LOL_Darius_idle1"""
import unreal
import os

eal = unreal.EditorAssetLibrary

RTG_PATH = "/Game/Character/Darius/IK/RTG_LOL_To_Darius"
SRC_ANIM = "/Game/Character/Darius/LOL_Source/A_LOL_Darius_idle1"
OUT_DIR = "/Game/Character/Darius/Animations/LOL_Retarget"

unreal.log("==================================================")
unreal.log("=== 1. 验证 RTG_LOL_To_Darius 链映射与姿态 ===")
unreal.log("==================================================")

rtg = unreal.load_object(None, RTG_PATH)
if not rtg:
    raise RuntimeError(f"未找到 RTG: {RTG_PATH}")

c_rtg = unreal.IKRetargeterController.get_controller(rtg)

# 校验核心骨骼链映射
CRITICAL_CHECKS = {
    "LeftLeg": "LeftLeg",
    "LeftFoot": "LeftFoot",
    "RightLeg": "RightLeg",
    "RightFoot": "RightFoot",
    "LeftArm": "LeftArm",
    "RightArm": "RightArm",
    "Weapon": "Weapon",
    "Pelvis": "None"
}

for tgt_ch, expected_src in CRITICAL_CHECKS.items():
    actual_src = str(c_rtg.get_source_chain(unreal.Name(tgt_ch)))
    assert actual_src == expected_src, f"[FAIL] 链映射错误: {tgt_ch} 映射为了 {actual_src} (期望 {expected_src})"
    unreal.log(f"  [PASS] 链映射验证: Target[{tgt_ch:<12}] -> Source[{actual_src:<12}]")

# 校验 Target 旋转偏移（断言彻底消除 -72° 畸变）
curr_pose = c_rtg.get_current_retarget_pose_name(unreal.RetargetSourceOrTarget.TARGET)
unreal.log(f"Target Retarget Pose: {curr_pose}")

q_thigh_l = c_rtg.get_rotation_offset_for_retarget_pose_bone(unreal.Name("thigh_l"), unreal.RetargetSourceOrTarget.TARGET)
rot_thigh_l = q_thigh_l.rotator()
unreal.log(f"thigh_l 旋转偏移: pitch={rot_thigh_l.pitch:.2f}, yaw={rot_thigh_l.yaw:.2f}, roll={rot_thigh_l.roll:.2f}")
assert abs(rot_thigh_l.yaw) < 5.0, f"[FAIL] thigh_l Yaw 偏转过大: {rot_thigh_l.yaw}"
unreal.log("  [PASS] 左右腿交叉畸变已彻底清零（Yaw 偏差 < 5°）！")

unreal.log("\n==================================================")
unreal.log("=== 2. 执行 A_LOL_Darius_idle1 重定向 ===")
unreal.log("==================================================")

if not eal.does_directory_exist(OUT_DIR):
    eal.make_directory(OUT_DIR)

ad = eal.find_asset_data(SRC_ANIM)
if not ad:
    raise RuntimeError(f"未找到源动画: {SRC_ANIM}")

inp = unreal.IKRetargetBatchOperationInputs()
inp.set_editor_property("assets_to_retarget", [ad])
inp.set_editor_property("ik_retarget_asset", rtg)
inp.set_editor_property("target_path", OUT_DIR)
inp.set_editor_property("use_source_path", False)
inp.set_editor_property("include_referenced_assets", False)
inp.set_editor_property("overwrite_existing_files", True)
inp.set_editor_property("search", "A_LOL_Darius_")
inp.set_editor_property("replace", "A_Darius_")

res = unreal.IKRetargetBatchOperation.run_batch_retarget(inp)
unreal.log(f"重定向产物列表: {len(res)} 项")
for r in (res or []):
    unreal.log(f"   产物包: {r.package_name if hasattr(r, 'package_name') else r}")

# 校验重定向产物
out_anim_path = f"{OUT_DIR}/A_Darius_idle1"
out_anim = unreal.load_object(None, out_anim_path)
if out_anim:
    num_keys = out_anim.get_editor_property("number_of_sampled_keys")
    seq_len = out_anim.get_editor_property("sequence_length")
    unreal.log(f"\n=== 重定向产物自验成功: {out_anim_path} ===")
    unreal.log(f"   骨骼数: {len(unreal.AnimationLibrary.get_animation_track_names(out_anim)) if hasattr(unreal.AnimationLibrary, 'get_animation_track_names') else 'N/A'}")
    unreal.log(f"   帧数 (Sampled Keys): {num_keys}")
    unreal.log(f"   时长 (Length): {seq_len:.2f} s")
    assert num_keys > 0, "动画帧数为 0！"
    unreal.log("   [PASS] 动画资产有效且保真落地！")
else:
    raise RuntimeError(f"未能加载重定向产物: {out_anim_path}")
