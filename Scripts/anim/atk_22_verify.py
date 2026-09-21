# -*- coding: utf-8 -*-
"""校验刚导入的攻击动画：帧数 / 采样率 / 骨骼轨道覆盖 / 关键骨是否在动。"""
import unreal

FULL = "/Game/Character/Darius/Anims/A_Darius_Attack1_UB"
DEST = "/Game/Character/Darius/Anims"
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary
L = unreal.log

a = eal.load_asset(FULL)
L("资产 = %s  类型=%s" % (FULL, type(a).__name__))
L("骨架 = %s" % a.get_editor_property("skeleton").get_name())

nf = AL.get_num_frames(a)
L("帧数 = %d" % nf)
for prop in ("sequence_length", "sampling_frame_rate", "number_of_frames", "rate_scale"):
    try:
        L("   %-22s = %s" % (prop, a.get_editor_property(prop)))
    except Exception as ex:
        L("   %-22s (读不到: %s)" % (prop, str(ex)[:60]))

names = [str(n) for n in a.controller.get_model_interface().get_bone_track_names()]
L("骨骼轨道数 = %d" % len(names))

CHECK = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head",
         "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r",
         "lowerarm_l", "lowerarm_r", "hand_l", "hand_r",
         "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r", "weapon_jnt"]
L("--- 关键骨轨道 ---")
for b in CHECK:
    L("   %-12s %s" % (b, "有" if b in names else "!! 无"))

# 逐帧取 pelvis / hand_r 的世界位置，确认动画真的在动
L("--- 抽样：pelvis 与 hand_r 的 component-space 位置（应有明显变化）---")
BONES = [unreal.Name("pelvis"), unreal.Name("hand_r")]
for f in (0, nf // 4, nf // 2, nf * 3 // 4, nf):
    ps = AL.get_bone_poses_for_frame(a, BONES, f, True)
    L("   f%-3d pelvis=(%7.2f,%7.2f,%7.2f)  hand_r=(%7.2f,%7.2f,%7.2f)" % (
        f, ps[0].translation.x, ps[0].translation.y, ps[0].translation.z,
        ps[1].translation.x, ps[1].translation.y, ps[1].translation.z))

L("--- 目录现状（找误建的 SkeletalMesh）---")
for p in eal.list_assets(DEST, recursive=False, include_folder=False):
    try:
        c = eal.find_asset_data(p).asset_class_path.asset_name
    except Exception:
        c = "?"
    if "Attack1" in p or c != "AnimSequence":
        L("   %-58s %s" % (p, c))
