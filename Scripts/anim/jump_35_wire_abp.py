import unreal

AL = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary

ABP_PATH = "/Game/Character/Darius/Blueprints/ABP_Darius_Test"
REPLACEMENTS = {
    "MM_Jump": "/Game/Character/Darius/Anims/A_Darius_AxeJump_Start",
    "MM_Fall_Loop": "/Game/Character/Darius/Anims/A_Darius_AxeJump_Loop",
    "MM_Land": "/Game/Character/Darius/Anims/A_Darius_AxeJump_Land",
}

abp = eal.load_asset(ABP_PATH)
changed = 0

for g in AL.get_animation_graphs(abp):
    for n in g.get_graph_nodes_of_class(unreal.AnimGraphNode_SequencePlayer):
        nd = n.get_editor_property("node")
        sq = nd.get_editor_property("sequence")
        if sq:
            sq_name = sq.get_name()
            for old_key, new_path in REPLACEMENTS.items():
                if old_key in sq_name:
                    new_asset = eal.load_asset(new_path)
                    nd.set_editor_property("sequence", new_asset)
                    n.set_editor_property("node", nd)
                    changed += 1
                    unreal.log(f"Graph '{g.get_name()}' [{n.get_name()}]: {sq_name} -> {new_asset.get_name()}")

unreal.log(f"Total nodes replaced: {changed}")

# Compile and save
unreal.BlueprintEditorLibrary.compile_blueprint(abp)
saved = eal.save_asset(ABP_PATH)
unreal.log(f"Compiled and saved ABP_Darius_Test: {saved}")

# Verify
unreal.log("=== Verification ===")
abp_verify = eal.load_asset(ABP_PATH)
for g in AL.get_animation_graphs(abp_verify):
    for n in g.get_graph_nodes_of_class(unreal.AnimGraphNode_SequencePlayer):
        nd = n.get_editor_property("node")
        sq = nd.get_editor_property("sequence")
        if sq:
            unreal.log(f"  Graph '{g.get_name()}': {sq.get_path_name()}")
