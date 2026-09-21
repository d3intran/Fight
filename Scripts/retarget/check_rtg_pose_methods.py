# -*- coding: utf-8 -*-
import unreal

c = unreal.IKRetargeterController
unreal.log("=== IKRetargeterController pose methods ===")
for m in sorted(dir(c)):
    if "pose" in m.lower() or "anim" in m.lower():
        unreal.log(f"  {m}")
