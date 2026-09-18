import unreal
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
removed = []
for a in actor_sub.get_all_level_actors():
    n = a.get_name()
    if n.startswith(("CameraActor_", "BP_DariusCharacter", "ShotCam", "TestCamera", "DariusShowcase")):
        removed.append(n); actor_sub.destroy_actor(a)
print("清理:", removed)
print("关卡最终 Actor:")
for a in actor_sub.get_all_level_actors():
    print("   ", a.get_name(), "|", a.get_class().get_name())
for k in les.get_viewport_config_keys():
    try:
        les.editor_set_game_view(False, k)
        les.set_level_viewport_camera_info(unreal.Vector(-1000, -1000, 800), unreal.Rotator(-28, 45, 0), k)
    except Exception:
        pass
les.editor_invalidate_viewports()
print("视口已复位")
print("=== DONE ===")
