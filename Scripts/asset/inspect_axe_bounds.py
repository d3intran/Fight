# -*- coding: utf-8 -*-
import unreal

mesh = unreal.load_object(None, "/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")
b = mesh.get_bounds()
unreal.log(f"Axe Bounds Box Extent: {b.box_extent}")
unreal.log(f"Axe Origin: {b.origin}")
unreal.log(f"Axe Size: X={b.box_extent.x*2:.1f}, Y={b.box_extent.y*2:.1f}, Z={b.box_extent.z*2:.1f} cm")
