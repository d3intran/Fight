import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

ABP_PATH = "/Game/Character/Darius/Blueprints/ABP_Darius_Test"
NEW = "/Game/Character/Darius/Anims/A_Darius_AxeIdle_Layered"
OLD = "/Game/Character/Darius/Anims_TP_v2/A_Darius_idle1"

abp = eal.load_asset(ABP_PATH)
new_anim = eal.load_asset(NEW)

changed = 0
for g in AL.get_animation_graphs(abp):
    for n in g.get_graph_nodes_of_class(unreal.AnimGraphNode_SequencePlayer):
        nd = n.get_editor_property("node")
        sq = nd.get_editor_property("sequence")
        if sq and sq.get_path_name().split(".")[0] == OLD:
            nd.set_editor_property("sequence", new_anim)
            n.set_editor_property("node", nd)
            changed += 1
            unreal.log("图 %-14s SequencePlayer: %s -> %s" % (g.get_name(), sq.get_name(), NEW.rsplit("/", 1)[-1]))
unreal.log("替换 %d 个节点" % changed)

unreal.BlueprintEditorLibrary.compile_blueprint(abp)
unreal.log("save_asset -> %s" % eal.save_asset(ABP_PATH))

unreal.log("### 复核")
abp2 = eal.load_asset(ABP_PATH)
for g in AL.get_animation_graphs(abp2):
    for cls, prop in ((unreal.AnimGraphNode_SequencePlayer, "sequence"),
                      (unreal.AnimGraphNode_BlendSpacePlayer, "blend_space")):
        for n in g.get_graph_nodes_of_class(cls):
            nd = n.get_editor_property("node")
            a = nd.get_editor_property(prop)
            if a:
                unreal.log("   %-14s %-18s -> %s" % (g.get_name(), cls.__name__[15:], a.get_name()))
unreal.log("### DONE")
