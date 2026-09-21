# -*- coding: utf-8 -*-
import unreal

c = unreal.IKRigController
unreal.log("=== IKRigController methods ===")
for m in sorted(dir(c)):
    if 'pose' in m.lower() or 'bone' in m.lower() or 'transform' in m.lower():
        unreal.log(f"  {m}")
