# -*- coding: utf-8 -*-
"""回退：把 ABP 的 Idle 状态从攻击动画换回待机，并把 rate_scale 复位。"""
import unreal

ATTACK = "/Game/Character/Darius/Anims/A_Darius_Attack1_UB"
ABP_PATH = "/Game/Character/Darius/Blueprints/ABP_Darius_Test"
IDLE_ORIG = "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered"

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary
L = unreal.log

att = eal.load_asset(ATTACK)
if att:
    att.set_editor_property("rate_scale", 1.0)
    L("rate_scale -> 1.0, save -> %s" % eal.save_asset(ATTACK))

abp = eal.load_asset(ABP_PATH)
idle = eal.load_asset(IDLE_ORIG)
changed = 0
for g in AL.get_animation_graphs(abp):
    for n in g.get_graph_nodes_of_class(unreal.AnimGraphNode_SequencePlayer):
        nd = n.get_editor_property("node")
        sq = nd.get_editor_property("sequence")
        if sq and sq.get_path_name().split(".")[0] == ATTACK:
            nd.set_editor_property("sequence", idle)
            n.set_editor_property("node", nd)
            changed += 1
            L("图 %s: %s -> %s" % (g.get_name(), sq.get_name(), "A_Darius_AxeIdle_Layered"))
L("回退 %d 个节点" % changed)
unreal.BlueprintEditorLibrary.compile_blueprint(abp)
L("compile + save -> %s" % eal.save_asset(ABP_PATH))

abp2 = eal.load_asset(ABP_PATH)
L("=== 复核 ===")
for g in AL.get_animation_graphs(abp2):
    for cls, prop in ((unreal.AnimGraphNode_SequencePlayer, "sequence"),
                      (unreal.AnimGraphNode_BlendSpacePlayer, "blend_space")):
        for n in g.get_graph_nodes_of_class(cls):
            nd = n.get_editor_property("node")
            a = nd.get_editor_property(prop)
            if a:
                L("   %-16s %-18s -> %s" % (g.get_name(), cls.__name__[15:], a.get_name()))
