import unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
gw = ues.get_game_world()
for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
    if "BP_DariusCharacter" in a.get_name():
        mesh = a.get_component_by_class(unreal.SkeletalMeshComponent)
        sk = mesh.get_editor_property("skeletal_mesh_asset")
        sock = sk.find_socket(unreal.Name("hand_rSocket"))
        print("Socket on asset:", sock)
        if sock:
            print("  RelativeScale:", sock.get_editor_property("relative_scale"))
            print("  RelativeRotation:", sock.get_editor_property("relative_rotation"))
            print("  RelativeLocation:", sock.get_editor_property("relative_location"))
