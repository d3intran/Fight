import unreal

print("=== 插件探测 ===")
try:
    plugins = unreal.Plugins.get_enabled_plugin_names()
    for p in plugins:
        lp = p.lower()
        if "gltf" in lp or "interchange" in lp or "ikrig" in lp or "retarget" in lp or "controlrig" in lp:
            print("  enabled:", p)
except Exception as e:
    print("  err:", e)

print()
print("=== API 探测 ===")
for api in ["InterchangeManager", "IKRigDefinition", "IKRetargeter", "IKRetargetBatchOperation",
            "IKRigController", "IKRetargeterController", "SkeletalMeshEditorSubsystem",
            "AnimationLibrary", "AnimationBlueprintLibrary", "AssetTools"]:
    print(f"  unreal.{api}:", hasattr(unreal, api))

print()
try:
    print("InterchangeManager funcs:", [f for f in dir(unreal.InterchangeManager) if not f.startswith("_")][:40])
except Exception as e:
    print("IM err:", e)

print()
print("=== 已有资产搜索 ===")
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for cls in ["IKRigDefinition", "IKRetargeter", "AnimSequence", "Skeleton"]:
    try:
        f = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath("/Script/Engine", cls)] if False else None)
    except Exception:
        pass
try:
    assets = ar.get_assets_by_path("/Game/Character", recursive=True)
    print("Character 下资产:", [str(a.package_name) for a in assets])
except Exception as e:
    print("ar err:", e)
print("=== DONE ===")
