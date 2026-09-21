# rtg_62_rest_api_probe - 只读：探测"世界等价重标定"Skeleton rest 的可行 API
import unreal

def L(s): print(f"[API] {s}")

for cls in ("Skeleton", "SkeletonModifier", "SkeletalMeshEditorSubsystem",
            "SkeletonEditorSubsystem", "AnimationLibrary", "AnimationDataController",
            "SkeletonTools", "SkeletalMeshTools"):
    c = getattr(unreal, cls, None)
    if c is None:
        L(f"{cls}: 不存在")
        continue
    ms = [m for m in dir(c) if not m.startswith("_")]
    L(f"{cls}: {len(ms)} 个成员")
    for m in ms:
        if any(k in m.lower() for k in ("rest", "ref", "pose", "bone", "skeleton", "modify", "transform", "scale")):
            L(f"    {cls}.{m}")

# 现有资产
for p in ("/Game/Character/Darius/SK_Darius_GodKing_Skeleton",
          "/Game/Character/Darius/CA_Darius_Cape",
          "/Game/Character/Darius/PHYS_Darius_GodKing"):
    a = unreal.load_asset(p)
    L(f"load {p} -> {a.get_class().get_name() if a else None}")

# 物理资产搜索
ar = unreal.AssetRegistryHelpers.get_asset_registry()
f = unreal.ARFilter(package_paths=["/Game/Character/Darius"], recursive_paths=True,
                    class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "PhysicsAsset")])
L(f"PhysicsAsset = {[str(a.asset_name) for a in ar.get_assets(f)]}")

f2 = unreal.ARFilter(package_paths=["/Game/Character/Darius"], recursive_paths=True,
                     class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "Skeleton")])
L(f"Skeleton 资产 = {[str(a.asset_name) for a in ar.get_assets(f2)]}")
L("DONE")
