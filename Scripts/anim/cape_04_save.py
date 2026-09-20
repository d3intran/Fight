import unreal

SM = "/Game/Character/Darius/SK_Darius_GodKing"
PA = "/Game/Character/Darius/SK_Darius_GodKing_Physics"
eal = unreal.EditorAssetLibrary

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
unreal.log("PIE running = %s" % les.is_in_play_in_editor())
if les.is_in_play_in_editor():
    unreal.log_error("还在 PIE，先停掉再存")
    raise SystemExit(1)

sk = eal.load_asset(SM)
pa = eal.load_asset(PA)
sub = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)

unreal.log("改前 physics_asset = %s" % sk.get_editor_property("physics_asset"))
unreal.log("兼容性 = %s" % sub.is_physics_asset_compatible(sk, pa))
unreal.log("assign -> %s" % sub.assign_physics_asset(sk, pa))
unreal.log("改后 physics_asset = %s" % sk.get_editor_property("physics_asset"))
unreal.log("save_asset -> %s" % eal.save_asset(SM))

# 复核：重新读盘上的对象
unreal.log("### 复核")
sk2 = eal.load_asset(SM)
unreal.log("   physics_asset = %s" % sk2.get_editor_property("physics_asset"))
unreal.log("### DONE")
