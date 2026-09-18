import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== 编辑器关卡现有 Actor 全量清单 ===")
acts = actor_sub.get_all_level_actors()
print("总数:", len(acts))
for a in acts:
    try:
        loc = a.get_actor_location()
    except Exception:
        loc = None
    print(f"   {a.get_name():42s} | {a.get_class().get_name():28s} | {loc}")

print()
print("=== 恢复视口状态 ===")
for k in les.get_viewport_config_keys():
    try:
        les.editor_set_game_view(False, k)
        les.editor_set_viewport_realtime(True, k)
        les.set_level_viewport_camera_info(unreal.Vector(-900, -900, 700), unreal.Rotator(-25, 45, 0), k)
        print("  重置视口:", k)
    except Exception as e:
        print("  视口 err", k, e)

for cmd in ["ShowFlag.Selection 1", "ShowFlag.Billboard 1", "ShowFlag.Grid 1"]:
    unreal.SystemLibrary.execute_console_command(ew, cmd)
les.editor_invalidate_viewports()
print("=== DONE ===")
