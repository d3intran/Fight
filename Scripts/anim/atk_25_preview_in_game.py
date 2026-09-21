# -*- coding: utf-8 -*-
"""让攻击动画能在游戏里直接看见 —— 临时把 ABP 的 Idle 状态指向它。

⚠️ 这是**临时预览**，不是最终接线（最终要加 IA_Attack + 攻击状态 + montage）。
回退：把 IDLE_ORIG 换回即可（脚本末尾会打印回退用的常量）。

另外顺手修 fps：Blender 导出的 FBX 被 UE 按 24fps 解（73 帧 = 3.04s），
源是 30fps（73 帧 = 2.43s），所以设 rate_scale = 1.25 补偿。
"""
import unreal

ATTACK = "/Game/Character/Darius/Anims/A_Darius_Attack1_UB"
ABP_PATH = "/Game/Character/Darius/Blueprints/ABP_Darius_Test"
IDLE_ORIG = "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered"

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary
L = unreal.log

# ---------- 1) fps 补偿 ----------
att = eal.load_asset(ATTACK)
nf = AL.get_num_frames(att)
before = att.get_editor_property("sequence_length")
rs = att.get_editor_property("rate_scale")
L("攻击序列: 帧数=%d  长度=%.4f s  rate_scale=%s" % (nf, before, rs))
if abs(before - nf / 30.0) > 0.05:
    att.set_editor_property("rate_scale", nf / 30.0 / before)
    L("   → 设 rate_scale = %.4f（目标长度 %.4f s）" % (
        att.get_editor_property("rate_scale"), nf / 30.0))
    L("   save -> %s" % eal.save_asset(ATTACK))
else:
    L("   → 长度已正确，不动")

# ---------- 2) 临时把 Idle 状态指向攻击 ----------
abp = eal.load_asset(ABP_PATH)
L("=== 改前 ===")
for g in AL.get_animation_graphs(abp):
    for cls, prop in ((unreal.AnimGraphNode_SequencePlayer, "sequence"),
                      (unreal.AnimGraphNode_BlendSpacePlayer, "blend_space")):
        for n in g.get_graph_nodes_of_class(cls):
            nd = n.get_editor_property("node")
            a = nd.get_editor_property(prop)
            if a:
                L("   %-16s %-18s -> %s" % (g.get_name(), cls.__name__[15:], a.get_name()))

changed = 0
for g in AL.get_animation_graphs(abp):
    for n in g.get_graph_nodes_of_class(unreal.AnimGraphNode_SequencePlayer):
        nd = n.get_editor_property("node")
        sq = nd.get_editor_property("sequence")
        if sq and sq.get_path_name().split(".")[0] == IDLE_ORIG:
            nd.set_editor_property("sequence", att)
            n.set_editor_property("node", nd)
            changed += 1
            L("图 %s 的 SequencePlayer: %s -> %s" % (g.get_name(), sq.get_name(), "A_Darius_Attack1_UB"))
L("替换 %d 个节点" % changed)
unreal.BlueprintEditorLibrary.compile_blueprint(abp)
L("compile + save -> %s" % eal.save_asset(ABP_PATH))

L("=== 改后 ===")
abp2 = eal.load_asset(ABP_PATH)
for g in AL.get_animation_graphs(abp2):
    for cls, prop in ((unreal.AnimGraphNode_SequencePlayer, "sequence"),
                      (unreal.AnimGraphNode_BlendSpacePlayer, "blend_space")):
        for n in g.get_graph_nodes_of_class(cls):
            nd = n.get_editor_property("node")
            a = nd.get_editor_property(prop)
            if a:
                L("   %-16s %-18s -> %s" % (g.get_name(), cls.__name__[15:], a.get_name()))

L("### 回退方法：把上面的 %s 改回 %s，重跑本脚本的同款逻辑即可" % (ATTACK, IDLE_ORIG))
