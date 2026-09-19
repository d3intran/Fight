import unreal

bp = unreal.load_object(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter")

# SimpleConstructionScript
scs = bp.get_editor_property("simple_construction_script")
unreal.log(f"SCS: {scs}")
if scs:
    nodes = scs.get_editor_property("all_nodes")
    unreal.log(f"Num SCS Nodes: {len(nodes)}")
    for i, n in enumerate(nodes):
        var_name = n.get_editor_property("variable_name")
        comp_class = n.get_editor_property("component_class")
        template = n.get_editor_property("component_template")
        attach_name = n.get_editor_property("attach_to_name")
        parent_name = n.get_editor_property("parent_component_or_variable_name")
        unreal.log(f"  Node {i}: VarName={var_name}, Class={comp_class.get_name() if comp_class else 'None'}, AttachTo={attach_name}, Parent={parent_name}, Template={template}")
        if template and isinstance(template, unreal.StaticMeshComponent):
            unreal.log(f"    StaticMesh: {template.get_editor_property('static_mesh')}")
