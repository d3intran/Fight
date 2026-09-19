import unreal

for name in dir(unreal):
    if any(k in name.lower() for k in ['screenshot', 'automation', 'viewport', 'camera']):
        unreal.log(f"unreal.{name}")
