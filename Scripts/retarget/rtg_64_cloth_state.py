# rtg_64_cloth_state - 只读：确认布料资产现状（根治方案的最大变量）
import unreal

def L(s): print(f"[CLOTH] {s}")

ar = unreal.AssetRegistryHelpers.get_asset_registry()

for cls_path in ("/Script/ChaosClothAsset", "/Script/ChaosCloth", "/Script/ClothingSystemRuntimeInterface"):
    try:
        f = unreal.ARFilter(package_paths=["/Game"], recursive_paths=True,
                            class_paths=[unreal.TopLevelAssetPath(cls_path, "ChaosClothAsset")])
        got = [str(a.package_name) for a in ar.get_assets(f)]
        L(f"{cls_path} -> {got}")
    except Exception as ex:
        L(f"{cls_path} err {str(ex)[:60]}")

# 全量枚举 /Game 下 Cloth 相关
try:
    f = unreal.ARFilter(package_paths=["/Game"], recursive_paths=True)
    hits = []
    for a in ar.get_assets(f):
        n = str(a.asset_name)
        cn = str(a.asset_class_path.asset_name) if hasattr(a, "asset_class_path") else ""
        if "cloth" in n.lower() or "cape" in n.lower() or "Cloth" in cn:
            hits.append(f"{a.package_name} :: {n} ({cn})")
    L(f"Cloth/Cape 相关资产 {len(hits)} 个：")
    for h in hits:
        L(f"   {h}")
except Exception as ex:
    L(f"enum err {ex}")

# mesh 的材质槽与 LOD / skin 数量
mesh = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
try:
    mats = mesh.get_editor_property("materials")
    L(f"材质槽 {len(mats)} 个: {[str(m.get_editor_property('material_interface').get_name()) if m.get_editor_property('material_interface') else None for m in mats]}")
except Exception as ex:
    L(f"materials err {str(ex)[:60]}")

try:
    LOD = mesh.get_editor_property("lod_info")
    L(f"LOD 数 = {len(LOD)}")
except Exception as ex:
    L(f"lod err {str(ex)[:60]}")

# Skeleton 上挂的兼容骨架（影响改造爆炸半径）
sk = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")
try:
    cs = sk.get_editor_property("compatible_skeletons")
    L(f"compatible_skeletons = {[str(c.get_name()) if c else None for c in cs]}")
except Exception as ex:
    L(f"compat err {str(ex)[:60]}")
L("DONE")
