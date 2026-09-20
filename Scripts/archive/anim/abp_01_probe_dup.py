import unreal

# 1) 测试 BlendSpace 能否用 Python 写入样本
print("=== BlendSpace 样本写入测试 ===")
bs = unreal.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run")
print("源 BS:", bs, "skeleton:", bs.get_editor_property("skeleton") if bs else None)
try:
    sd = bs.get_editor_property("sample_data")
    print("  sample_data 可读:", sd)
    for s in sd:
        print("    sample:", s)
        for f in ["animation", "sample_value", "rate_scale"]:
            try:
                print("       ", f, "=", s.get_editor_property(f))
            except Exception as e:
                print("       ", f, "<err>")
except Exception as e:
    print("  sample_data 读取失败:", e)

# 2) 测试 AnimBlueprint.target_skeleton 能否写入
print()
print("=== AnimBlueprint.target_skeleton 写入测试 ===")
abp = unreal.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed")
print("  abp:", abp, "target_skeleton:", abp.get_editor_property("target_skeleton"))
skel = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")
dst = "/Game/Character/Darius/Blueprints/ABP_Darius_Test"
if unreal.EditorAssetLibrary.does_asset_exist(dst):
    unreal.EditorAssetLibrary.delete_asset(dst)
dup = unreal.EditorAssetLibrary.duplicate_asset("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed", dst)
print("  副本:", dup)
if dup:
    try:
        dup.set_editor_property("target_skeleton", skel)
        print("  写入 target_skeleton ->", dup.get_editor_property("target_skeleton"))
    except Exception as e:
        print("  写入失败:", e)
    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(dup)
        print("  compile 完成")
    except Exception as e:
        print("  compile err:", e)
    # 再枚举节点看是否还能读
    n = unreal.AnimationLibrary.get_nodes_of_class(dup, unreal.AnimGraphNode_SequencePlayer)
    print("  副本中 SequencePlayer 节点数:", len(n))
    for x in n:
        try:
            print("     ", x.get_name(), "->", x.get_editor_property("node").get_editor_property("sequence"))
        except Exception as e:
            print("     ", x.get_name(), "<err>", e)
print("=== DONE ===")
