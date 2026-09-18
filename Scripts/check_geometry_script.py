import unreal

unreal.log(f"Has GeometryScript: {hasattr(unreal, 'GeometryScript_MeshBasic') or hasattr(unreal, 'GeometryScriptMeshBasic') or hasattr(unreal, 'GeometryScriptLibrary_MeshBasic')}")
methods = [m for m in dir(unreal) if 'geometryscript' in m.lower()]
unreal.log(f"GeometryScript methods count: {len(methods)}")
for m in methods[:10]:
    unreal.log(f"  {m}")
