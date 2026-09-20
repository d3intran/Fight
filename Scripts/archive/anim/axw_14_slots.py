import unreal

eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

sk = eal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
unreal.log("### SK_Darius_GodKing")
unreal.log("   skeleton = %s" % sk.get_editor_property("skeleton").get_path_name())
try:
    mats = sk.get_editor_property("materials")
    for i, m in enumerate(mats):
        mi = m.get_editor_property("material_interface")
        slot = m.get_editor_property("material_slot_name")
        imp = m.get_editor_property("imported_material_slot_name")
        unreal.log("   slot %d  name=%-34s imported=%-34s -> %s" % (
            i, str(slot), str(imp), mi.get_path_name() if mi else None))
except Exception as ex:
    unreal.log("   materials ERR %s" % ex)

unreal.log("### 关卡角色")
found = False
for a in eas.get_all_level_actors():
    if "Darius" in a.get_actor_label() or "Darius" in a.get_name():
        found = True
        unreal.log("   actor %s" % a.get_actor_label())
        for c in a.get_components_by_class(unreal.SceneComponent):
            try:
                cn = c.get_class().get_name()
            except Exception:
                continue
            if "Skeletal" in cn or "StaticMesh" in cn:
                unreal.log("      comp %-28s %s" % (c.get_name(), cn))
                try:
                    for s in c.get_socket_names() if hasattr(c, "get_socket_names") else []:
                        pass
                except Exception:
                    pass
if not found:
    unreal.log("   （关卡里没有 Darius 角色 actor）")

unreal.log("### 资产时间戳自检（内容浏览器里的导入来源）")
for p in ("/Game/Character/Darius/SK_Darius_GodKing",
          "/Game/Character/Darius/SK_Darius_GodKing_Skeleton",
          "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Mixamo",
          "/Game/Character/Darius/Anims/A_Darius_Walk_Layered",
          "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Layered",
          "/Game/Character/Darius/Anims/BS_Darius_Locomotion",
          "/Game/Character/Darius/Blueprints/BP_DariusCharacter",
          "/Game/Character/Darius/Blueprints/ABP_Darius_Test"):
    d = eal.get_asset_data(p) if hasattr(eal, "get_asset_data") else None
    unreal.log("   %-58s %s" % (p, "OK" if d else "MISSING"))
