import unreal

print("=== 查找 Skeleton 资产 ===")
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for a in ar.get_assets_by_path("/Game/Character/Darius", recursive=True):
    if "Skeleton" in str(a.asset_class_path.asset_name):
        print("  ", a.package_name, "|", a.asset_class_path.asset_name, "|", a.asset_name)

print()
print("=== Anims 目录现状 ===")
for a in ar.get_assets_by_path("/Game/Character/Darius/Anims", recursive=True):
    print("  ", a.package_name, "|", a.asset_class_path.asset_name)

print()
print("=== 直接加载测试 ===")
for p in ["/Game/Character/Darius/SK_Darius_GodKing_Skeleton",
          "/Game/Character/Darius/SK_Darius_GodKing"]:
    print(p, "-> EditorAssetLibrary:", unreal.EditorAssetLibrary.load_asset(p),
          "| unreal.load_asset:", unreal.load_asset(p))

sk = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")
if sk:
    print("skeleton class:", sk.get_class().get_name())
    try:
        print("  bone count:", sk.get_editor_property("skeleton").get_num())
    except Exception as e:
        print("  bones err:", e)
print("=== DONE ===")
