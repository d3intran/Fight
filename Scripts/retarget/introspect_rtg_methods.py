# -*- coding: utf-8 -*-
import unreal

c = unreal.IKRetargeterController
unreal.log("=== IKRetargeterController methods ===")
for m in sorted(dir(c)):
    if 'chain' in m.lower() or 'map' in m.lower() or 'root' in m.lower():
        unreal.log(f"  {m}")
