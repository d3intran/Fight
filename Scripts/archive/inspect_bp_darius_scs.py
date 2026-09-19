import unreal

eal = unreal.EditorAssetLibrary
bp = eal.load_asset("/Game/Character/Darius/Blueprints/BP_DariusCharacter")

unreal.log(f"Inspecting BP: {bp}")

# Gather all components in SimpleConstructionScript
scs = bp.get_editor_property("simple_construction_script")
if scs:
    nodes = scs.get_editor_property("all_nodes")
    for n in nodes:
        comp_class = n.get_editor_property("component_class")
        var_name = n.get_editor_property("variable_name")
        attach_to = n.get_editor_property("attach_to_name")
        parent_name = n.get_editor_property("parent_component_or_variable_name")
        unreal.log(f"SCS Node: VarName={var_name}, Class={comp_class.get_name() if comp_class else 'None'}, AttachTo={attach_to}, Parent={parent_name}")
        comp_template = n.get_editor_property("component_template")
        if comp_template:
            unreal.log(f"  Template: {comp_template}")
            if isinstance(comp_template, unreal.StaticMeshComponent):
                unreal.log(f"  Template StaticMesh: {comp_template.get_editor_property('static_mesh')}")

# Also check GeneratedClass default object
cdos = unreal.get_default_object(bp.generated_class())
unreal.log(f"CDO: {cdos}")
for c in cdos.get_components_by_class(unreal.ActorComponent):
    unreal.log(f"  CDO Comp: {c.get_name()} ({c.get_class().get_name()})")
