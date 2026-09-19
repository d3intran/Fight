import unreal

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

# 只清理本次诊断过程中由脚本生成的临时 Actor（相机 / 测试角色）
kill_prefix = ("CameraActor_", "ShotCam", "TestCamera", "BP_DariusCharacter_C")
removed = []
for a in actor_sub.get_all_level_actors():
    n = a.get_name()
    if n.startswith("CameraActor_") or n.startswith("ShotCam") or n.startswith("TestCamera") or n.startswith("BP_DariusCharacter_C"):
        removed.append(n)
        actor_sub.destroy_actor(a)
print("已清理临时 Actor:", removed)

print("剩余 Actor:")
for a in actor_sub.get_all_level_actors():
    print("   ", a.get_name(), "|", a.get_class().get_name())

# 清理导入过程中产生的冗余资产
for p in ["/Game/Character/Darius/Anims/A_Darius_LOL_Run_TP_Skeleton",
          "/Game/Character/Darius/Anims/LOL_Source"]:
    if unreal.EditorAssetLibrary.does_asset_exist(p):
        print("删除冗余资产", p, "->", unreal.EditorAssetLibrary.delete_asset(p))
    elif unreal.EditorAssetLibrary.does_directory_exist(p):
        print("删除冗余目录", p, "->", unreal.EditorAssetLibrary.delete_directory(p))

ew = ues.get_editor_world()
for k in les.get_viewport_config_keys():
    try:
        les.editor_set_game_view(False, k)
        les.set_level_viewport_camera_info(unreal.Vector(-1000, -1000, 800), unreal.Rotator(-28, 45, 0), k)
    except Exception:
        pass
les.editor_invalidate_viewports()
print("=== DONE ===")
