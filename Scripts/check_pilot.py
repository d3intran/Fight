import unreal

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Check if viewport is locked to an actor
# Or check get_pilot_level_actor
unreal.log("Checking viewport piloting...")
level_editor_sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem) if hasattr(unreal, 'LevelEditorSubsystem') else None

for m in dir(ues):
    if 'pilot' in m.lower() or 'lock' in m.lower():
        unreal.log(f"UES: {m}")

# Let's check PIE status
pie = unreal.EditorLevelLibrary.is_in_pie() if hasattr(unreal.EditorLevelLibrary, 'is_in_pie') else False
unreal.log(f"Is in PIE: {pie}")
