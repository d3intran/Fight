import unreal
ar = unreal.AssetRegistryHelpers.get_asset_registry()
print("=== Anims 目录 ===")
for a in ar.get_assets_by_path("/Game/Character/Darius/Anims", recursive=True):
    cn = str(a.asset_class_path.asset_name)
    nm = str(a.asset_name)
    if "AnimSequence" in cn:
        seq = unreal.load_asset(str(a.package_name))
        ln = round(seq.get_editor_property("sequence_length"), 3) if seq else "?"
        sk = seq.get_editor_property("skeleton") if seq else None
        print("   %-30s %8ss  skel=%s" % (nm, ln, sk.get_name() if sk else None))
    else:
        print("   %-30s [%s]" % (nm, cn))
print("=== DONE ===")
