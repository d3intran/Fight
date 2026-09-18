import unreal

# Search all subsystems and libraries for "focus" or "capture"
found = []
for obj in [unreal.EditorLevelLibrary, unreal.LevelEditorSubsystem, unreal.EditorActorSubsystem, unreal.UnrealEditorSubsystem]:
    for m in dir(obj):
        if any(w in m.lower() for w in ['focus', 'capture', 'shot', 'image']):
            found.append(f"{obj.__name__}.{m}")

for f in found:
    unreal.log(f)
