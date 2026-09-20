import unreal

ABP = "/Game/Character/Darius/Blueprints/ABP_Darius_Test"

props = [m for m in dir(unreal.AnimNode_RigidBody) if not m.startswith("_")]
unreal.log("############ 0. AnimNode_RigidBody 全部可访问名 (%d)" % len(props))
unreal.log("   %s" % props)

abp = unreal.load_object(None, ABP)
for g in unreal.AnimationLibrary.get_animation_graphs(abp):
    nodes = g.get_graph_nodes_of_class(unreal.AnimGraphNode_RigidBody)
    for n in nodes:
        unreal.log("############ 1. %s / %s 全属性" % (g.get_name(), n.get_name()))
        nd = n.get_editor_property("node")
        for pr in props:
            try:
                unreal.log("   %-56s = %s" % (pr, nd.get_editor_property(pr)))
            except Exception:
                pass
        unreal.log("   --- 同时看图节点自身")
        for pr in ("node", "title_desc", "b_override_title"):
            try:
                v = n.get_editor_property(pr)
                unreal.log("   %-56s = %s" % (pr, str(v)[:120]))
            except Exception:
                pass

unreal.log("############ 2. AnimGraph 全部节点类型（确认披风链路）")
AL = unreal.AnimationLibrary
for g in AL.get_animation_graphs(abp):
    try:
        nodes = g.get_graph_nodes_of_class(unreal.AnimGraphNode_Base)
    except Exception:
        continue
    for n in nodes:
        try:
            pins = [str(p.get_pin_name()) for p in n.list_input_pins()]
        except Exception:
            pins = []
        unreal.log("   %-16s %-46s in=%s" % (g.get_name(), n.get_class().get_name().replace("AnimGraphNode_", ""), pins))
unreal.log("############ DONE")
