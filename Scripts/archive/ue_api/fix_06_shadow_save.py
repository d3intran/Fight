import unreal, time

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
print("in PIE:", les.is_in_play_in_editor())
if les.is_in_play_in_editor():
    les.editor_request_end_play()
    print("requested end play")
else:
    mat = unreal.load_asset("/Game/Character/Darius/Materials/M_Invisible")
    mat.set_editor_property("cast_dynamic_shadow_as_masked", True)
    print("cast_dynamic_shadow_as_masked ->", mat.get_editor_property("cast_dynamic_shadow_as_masked"))
    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
        print("recompiled")
    except Exception as e:
        print("recompile err:", e)
    print("mark dirty:", unreal.EditorAssetLibrary.save_loaded_asset(mat))
    print("save_asset(path):", unreal.EditorAssetLibrary.save_asset("/Game/Character/Darius/Materials/M_Invisible", only_if_is_dirty=False))
    mat2 = unreal.load_asset("/Game/Character/Darius/Materials/M_Invisible")
    print("复核:", mat2.get_editor_property("cast_dynamic_shadow_as_masked"))
print("=== DONE ===")
