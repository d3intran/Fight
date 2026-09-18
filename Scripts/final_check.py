import unreal
ar = unreal.AssetRegistryHelpers.get_asset_registry()
print("=== Darius 相关资产 ===")
for a in ar.get_assets_by_path("/Game/Character/Darius", recursive=True):
    print("  ", a.package_name, "|", a.asset_class_path.asset_name)
seq = unreal.load_asset("/Game/Character/Darius/Anims/A_Darius_LOL_Run_TP")
if seq:
    print("AnimSequence:", seq.get_name(), "len:", round(seq.get_editor_property("sequence_length"),3), "s",
          "frames:", seq.get_editor_property("number_of_sampled_frames"))
sk = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
s = sk.find_socket(unreal.Name("hand_rSocket"))
print("hand_rSocket relScale:", s.get_editor_property("relative_scale"))
print("=== DONE ===")
