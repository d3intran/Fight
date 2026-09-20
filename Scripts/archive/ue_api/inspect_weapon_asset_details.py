import unreal

eal = unreal.EditorAssetLibrary
axe_asset = eal.load_asset("/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")

unreal.log(f"Axe Asset: {axe_asset}")
if axe_asset:
    unreal.log(f"  Class: {axe_asset.get_class().get_name()}")
    bounds = axe_asset.get_bounds()
    unreal.log(f"  Bounds: Origin={bounds.origin}, Extent={bounds.box_extent}, Radius={bounds.sphere_radius}")
    num_lods = axe_asset.get_num_lods() if hasattr(axe_asset, 'get_num_lods') else 'N/A'
    unreal.log(f"  Num LODs: {num_lods}")
    num_sections = axe_asset.get_num_sections(0) if hasattr(axe_asset, 'get_num_sections') else 'N/A'
    unreal.log(f"  Num Sections LOD 0: {num_sections}")
    mat0 = axe_asset.get_material(0)
    unreal.log(f"  Mat 0: {mat0}")
    if mat0:
        unreal.log(f"    Mat 0 Class: {mat0.get_class().get_name()}")
        unreal.log(f"    Mat 0 Parent: {mat0.get_editor_property('parent') if hasattr(mat0, 'get_editor_property') else 'N/A'}")
        
    # Check if there is an actor in level with this mesh
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    test_actor = actor_sub.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 150))
    if test_actor:
        sm_comp = test_actor.static_mesh_component
        sm_comp.set_static_mesh(axe_asset)
        unreal.log(f"Test StaticMeshActor spawned at {test_actor.get_actor_location()}, comp bounds={sm_comp.get_bounds()}")
        # don't destroy immediately so we can see it or inspect it
