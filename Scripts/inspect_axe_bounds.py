import unreal

axe = unreal.load_asset("/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe.SM_Darius_GodKing_Axe")
unreal.log(f"Loaded: {axe}")
if axe:
    bounds = axe.get_bounds()
    unreal.log(f"Axe Bounds: Origin={bounds.origin}, BoxExtent={bounds.box_extent}, SphereRadius={bounds.sphere_radius}")
    unreal.log(f"  Width X = {bounds.box_extent.x * 2}")
    unreal.log(f"  Length Y = {bounds.box_extent.y * 2}")
    unreal.log(f"  Height Z = {bounds.box_extent.z * 2}")
