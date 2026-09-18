import unreal
f = unreal.IKRetargetBatchOperation.duplicate_and_retarget
print("duplicate_and_retarget:", f)
print("doc:", getattr(f, "__doc__", None))
print()
r = unreal.IKRetargetBatchOperation.run_batch_retarget
print("run_batch_retarget:", r)
print("doc:", getattr(r, "__doc__", None))
print()
print("=== BlendSpace Python API ===")
print("BlendSpace:", [m for m in dir(unreal.BlendSpace) if not m.startswith("_")])
print()
for n in ["BlendSpaceFactoryNew", "BlendSpaceFactory1D", "BlendSpaceFactory", "BlendSpacePlayerLibrary"]:
    print(f"unreal.{n}:", hasattr(unreal, n))
print("=== DONE ===")
