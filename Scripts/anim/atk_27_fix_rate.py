# -*- coding: utf-8 -*-
"""把攻击序列的 rate_scale 修对。

Blender 导出的 FBX 被 UE 按 **24fps** 解（73 帧 → 3.0417 s），
而源是 30fps（73 帧 → 2.4333 s）⇒ 直接播会慢 25%。
UE 的 RateScale 语义：有效时长 = SequenceLength / RateScale，
所以要 3.0417 / 2.4333 = 1.25。
"""
import unreal

ATTACK = "/Game/Character/Darius/Anims/A_Darius_Attack1_UB"
eal = unreal.EditorAssetLibrary
AL = unreal.AnimationLibrary
L = unreal.log

a = eal.load_asset(ATTACK)
nf = AL.get_num_frames(a)
L("帧数=%d  当前 sequence_length=%.4f  rate_scale=%s" % (
    nf, a.get_editor_property("sequence_length"), a.get_editor_property("rate_scale")))

target_len = nf / 30.0
raw = a.get_editor_property("sequence_length")
rs = raw / target_len
a.set_editor_property("rate_scale", rs)
L("目标长度 = %.4f s  ⇒  rate_scale = %.6f" % (target_len, rs))
L("save -> %s" % eal.save_asset(ATTACK))

b = eal.load_asset(ATTACK)
L("复核: sequence_length=%.4f  rate_scale=%.6f  有效时长=%.4f s" % (
    b.get_editor_property("sequence_length"), b.get_editor_property("rate_scale"),
    b.get_editor_property("sequence_length") / b.get_editor_property("rate_scale")))
