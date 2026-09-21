# -*- coding: utf-8 -*-
"""verify_clean_source —— 验证 LOL_Source 资产状态"""
import unreal

mesh = unreal.load_object(None, "/Game/Character/Darius/LOL_Source/SK_LOL_Darius")
skel = unreal.load_object(None, "/Game/Character/Darius/LOL_Source/SK_LOL_Darius_Skeleton")

unreal.log(f"=== 验证 SK_LOL_Darius 状态 ===")
unreal.log(f"Mesh: {mesh.get_name() if mesh else 'None'}")
unreal.log(f"Skeleton: {skel.get_name() if skel else 'None'}")

if mesh:
    b = mesh.get_bounds()
    unreal.log(f"Bounds size: {b.box_extent.x*2:.1f} x {b.box_extent.y*2:.1f} x {b.box_extent.z*2:.1f} cm")
    unreal.log(f"Sphere radius: {b.sphere_radius:.2f} cm")
    unreal.log(f"Materials count: {len(mesh.materials)}")

eal = unreal.EditorAssetLibrary
anims = [a for a in eal.list_assets("/Game/Character/Darius/LOL_Source", recursive=False) if "A_LOL_Darius_" in str(a)]
unreal.log(f"AnimSequences count: {len(anims)}")
death_anim = unreal.load_object(None, "/Game/Character/Darius/LOL_Source/A_LOL_Darius_death")
if death_anim:
    unreal.log(f"Death anim loaded: {death_anim.get_name()}, length: {death_anim.get_play_length():.2f}s")
