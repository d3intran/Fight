import unreal

def reimport_skm():
    skm_path = "/Game/Character/Darius/SK_Darius_GodKing"
    skm = unreal.load_object(None, skm_path)
    if not skm:
        unreal.log_error("SKM not found")
        return
        
    unreal.log("=== 1. 记录重导入前材质 ===")
    mats_before = []
    for m in skm.get_editor_property("materials"):
        mats_before.append((str(m.material_slot_name), m.material_interface.get_path_name() if m.material_interface else None))
    unreal.log("Mats before: %s" % mats_before)
    
    unreal.log("=== 2. 执行 Interchange Reimport ===")
    im = unreal.InterchangeManager.get_interchange_manager_scripted()
    params = unreal.ImportAssetParameters()
    params.is_automated = True
    params.replace_existing = True
    
    res = im.reimport_asset(skm, params)
    unreal.log("Reimport result: %s" % res)
    
    unreal.log("=== 3. 检查重导入后材质 ===")
    mats_after = []
    for m in skm.get_editor_property("materials"):
        mats_after.append((str(m.material_slot_name), m.material_interface.get_path_name() if m.material_interface else None))
    unreal.log("Mats after: %s" % mats_after)
    
    # 确保材质槽一致，如有丢失恢复之
    if len(mats_before) == len(mats_after):
        skm_mats = skm.get_editor_property("materials")
        changed = False
        for i in range(len(mats_before)):
            slot_name, mat_path = mats_before[i]
            if mat_path and (not skm_mats[i].material_interface or skm_mats[i].material_interface.get_path_name() != mat_path):
                target_mat = unreal.load_object(None, mat_path)
                skm_mats[i].material_interface = target_mat
                changed = True
        if changed:
            skm.set_editor_property("materials", skm_mats)
            unreal.log("Restored material interfaces")

    unreal.EditorAssetLibrary.save_loaded_asset(skm)
    unreal.log("REIMPORT_AND_SAVED_SKM")

reimport_skm()
