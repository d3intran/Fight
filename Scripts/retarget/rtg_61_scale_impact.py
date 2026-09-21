# rtg_61_scale_impact - 只读：确认 100 挂点 + 统计影响面
import unreal

def L(s): print(f"[IMP] {s}")

mesh = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
L(f"mesh class={mesh.get_class().get_name()}")
try:
    sk = mesh.get_editor_property("skeleton")
    L(f"mesh.skeleton = {sk.get_name() if sk else None}")
except Exception as ex:
    L(f"skeleton prop err {ex}")

# 遍历骨骼：用 skeleton 资产
try:
    sk = mesh.get_editor_property("skeleton")
    if sk:
        tree = sk.get_editor_property("bone_tree")
        acc = []
        def walk(n, d):
            acc.append((d, str(n.get_editor_property("name"))))
            for c in n.get_editor_property("children"):
                walk(c, d + 1)
        for n in tree:
            walk(n, 0)
        L(f"skeleton 总骨数 = {len(acc)}")
        L("--- 深度 0-2 ---")
        for d, nm in acc:
            if d <= 2:
                L(f"  {'  '*d}{nm}")
        # 打印深度 0/1 的骨名全集，确认最外层骨叫什么
        L(f"depth0 = {[nm for d,nm in acc if d==0]}")
        L(f"depth1 = {[nm for d,nm in acc if d==1]}")
except Exception as ex:
    L(f"bone tree err {ex}")

# 统计依赖的动画资产数量
ar = unreal.AssetRegistryHelpers.get_asset_registry()
def count(path, cls):
    f = unreal.ARFilter(package_paths=[path], recursive_paths=True,
                        class_paths=[unreal.TopLevelAssetPath("/Script/Engine", cls)])
    return [str(a.asset_name) for a in ar.get_assets(f)]

anims = count("/Game/Character/Darius", "AnimSequence")
L(f"AnimSequence 总数 = {len(anims)}")
from collections import Counter
groups = Counter()
for a in anims:
    if a.startswith("A_Darius_Axe"): groups["Layered(AxeIdle/Walk)"] += 1
    elif a.startswith("A_Darius_"): groups["其他 A_Darius"] += 1
    elif a.startswith("A_LOL"): groups["源 LOL"] += 1
    else: groups["未分类"] += 1
for k, v in groups.items():
    L(f"  {k}: {v}")

blend = count("/Game/Character/Darius", "BlendSpace")
L(f"BlendSpace = {blend}")
bp = count("/Game/Character/Darius", "Blueprint")
L(f"Blueprint = {bp}")
L("DONE")
