import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

# If still in PIE, end it
if les.is_in_play_in_editor():
    les.editor_request_end_play()

ew = ues.get_editor_world()
destroyed = 0
for a in unreal.GameplayStatics.get_all_actors_of_class(ew, unreal.Actor):
    lb = a.get_actor_label()
    if lb in ["LocoShotCapture", "CapeShotCapture", "JumpShotCapture"]:
        eas.destroy_actor(a)
        destroyed += 1

unreal.log(f"[Cleanup] Destroyed {destroyed} temporary actors.")
remaining = len(eas.get_all_level_actors())
unreal.log(f"[Cleanup] Total level actors remaining: {remaining} (baseline target: 7)")
