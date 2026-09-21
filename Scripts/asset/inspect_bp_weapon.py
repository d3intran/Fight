# -*- coding: utf-8 -*-
"""inspect_bp_weapon —— 检查 BP_DariusCharacter 上的武器组件配置与插槽实读值"""
import unreal

bp_path = "/Game/Character/Darius/Blueprints/BP_DariusCharacter"
bp = unreal.load_object(None, bp_path)
unreal.log(f"=== 检查 {bp.get_name()} 武器装配 ===")

sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
axe_comp = None
for h in sub.k2_gather_subobject_data_for_blueprint(bp):
    d = sub.k2_find_subobject_data_from_handle(h)
    o = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(d)
    if isinstance(o, unreal.StaticMeshComponent) and "Weapon" in o.get_name():
        axe_comp = o
        break

if axe_comp:
    unreal.log(f"找到武器组件: {axe_comp.get_name()}")
    unreal.log(f"   attach_socket_name: {axe_comp.get_attach_socket_name()}")
    unreal.log(f"   relative_location: {axe_comp.get_editor_property('relative_location')}")
    unreal.log(f"   relative_rotation: {axe_comp.get_editor_property('relative_rotation')}")
    unreal.log(f"   relative_scale3d: {axe_comp.get_editor_property('relative_scale3d')}")
    sm = axe_comp.get_editor_property("static_mesh")
    unreal.log(f"   static_mesh: {sm.get_name() if sm else 'None'}")
    if sm:
        unreal.log(f"   网格插槽检查: {[s for s in ['Grip_Main', 'Grip_Assist', 'Pommel', 'Blade_Tip', 'Blade_Edge'] if sm.find_socket(s)]}")
else:
    unreal.log_warning("未找到武器组件！")
