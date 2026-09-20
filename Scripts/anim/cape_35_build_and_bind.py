import unreal
import json

def run():
    ca_path = "/Game/Character/Darius/Cloth/CA_Darius_Cape"
    df_path = "/Game/Character/Darius/Cloth/CA_Darius_Cape.CA_Darius_Cape:EmbeddedDataflow"
    skm_path = "/Game/Character/Darius/SK_Darius_GodKing"
    
    ca = unreal.load_object(None, ca_path)
    df = unreal.load_object(None, df_path)
    skm = unreal.load_object(None, skm_path)
    
    if not ca or not df or not skm:
        unreal.log_error("FAILED to load assets: ca=%s df=%s skm=%s" % (ca, df, skm))
        return
        
    unreal.log("=== 1. 触发 Dataflow 评估与资产 Regenerate ===")
    dbl = unreal.DataflowBlueprintLibrary
    
    # 尝试 EvaluateTerminalNodeByName
    try:
        unreal.log("Calling evaluate_terminal_node_by_name...")
        dbl.evaluate_terminal_node_by_name(df, "ClothAssetTerminal", ca)
        unreal.log("evaluate_terminal_node_by_name SUCCESS")
    except Exception as ex:
        unreal.log_warning("evaluate_terminal_node_by_name exception: %s" % ex)
        
    # 尝试 RegenerateAssetFromDataflow
    try:
        unreal.log("Calling regenerate_asset_from_dataflow...")
        res = dbl.regenerate_asset_from_dataflow(ca)
        unreal.log("regenerate_asset_from_dataflow result = %s" % res)
    except Exception as ex:
        unreal.log_warning("regenerate_asset_from_dataflow exception: %s" % ex)

    # 尝试 evaluate_dataflow
    try:
        unreal.log("Calling evaluate_dataflow...")
        res2 = dbl.evaluate_dataflow(df, ca)
        unreal.log("evaluate_dataflow result = %s" % res2)
    except Exception as ex:
        unreal.log_warning("evaluate_dataflow exception: %s" % ex)

    # 标记 Dirty 并保存 ca
    unreal.EditorAssetLibrary.save_loaded_asset(ca)
    unreal.log("Saved CA_Darius_Cape")

    # 重新检查 ca 属性
    unreal.log("=== 2. 检查 CA_Darius_Cape 状态 ===")
    for p in ["num_cinematic_mip_levels", "global_force_mip_levels_to_be_resident"]:
        try:
            unreal.log("  %s = %s" % (p, ca.get_editor_property(p)))
        except Exception:
            pass

    unreal.log("=== 3. 重新绑定到 SK_Darius_GodKing ===")
    # 先解除 Section 1 的绑定，再重新绑定
    toolset_cls = unreal.load_class(None, "/Script/ChaosClothAssetToolset.ChaosClothAssetToolset")
    # 可以通过 Python 调用 SkeletalMeshClothingSystemUtilities 或通过 MCP
    unreal.log("Assets prepared for rebind.")

run()
