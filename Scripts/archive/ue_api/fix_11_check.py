import unreal
ar = unreal.AssetRegistryHelpers.get_asset_registry()
print("=== /Game/Character/Darius 根目录资产 ===")
for a in ar.get_assets_by_path("/Game/Character/Darius", recursive=False):
    print("  ", a.package_name, "|", a.asset_class_path.asset_name)
print()
print("=== 全库 SkeletalMesh ===")
for a in ar.get_assets_by_path("/Game", recursive=True):
    if "SkeletalMesh" in str(a.asset_class_path.asset_name):
        print("  ", a.package_name)
print()
print("=== 尝试加载 NoAxe ===")
for p in ["/Game/Character/Darius/SK_Darius_GodKing_NoAxe",
          "/Game/Character/Darius/SK_Darius_GodKing_NoAxe.SK_Darius_GodKing_NoAxe"]:
    print(p, "->", unreal.load_asset(p))
print("=== DONE ===")
