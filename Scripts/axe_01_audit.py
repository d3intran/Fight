# -*- coding: utf-8 -*-
"""战斧显示缺失 - 客观审计：角色网格 / 武器静态网格 / 蓝图组件装配"""
import unreal

def L(s=""):
    unreal.log(str(s))

def mat_name(mi):
    return mi.get_path_name() if mi else "None"

L("=== [1] SK_Darius_GodKing ===")
sk = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
L("asset: " + str(sk))
if sk:
    mats = sk.get_editor_property("materials")
    L("material slots: %d" % len(mats))
    for i, m in enumerate(mats):
        L("   Slot[%d] name=%s -> %s" % (i, m.get_editor_property("material_slot_name"),
                                          mat_name(m.get_editor_property("material_interface"))))
    try:
        lod = sk.get_editor_property("lod_info")
        L("LOD count: %d" % len(lod))
        for i, l in enumerate(lod):
            secs = l.get_editor_property("sections")
            tot = 0
            info = []
            for j, s in enumerate(secs):
                mi_ = s.get_editor_property("material_index")
                # num_triangles not directly exposed; use triangle count probe
                info.append("sec%d(mat=%d)" % (j, mi_))
            L("   LOD%d sections=%d %s" % (i, len(secs), " ".join(info)))
    except Exception as e:
        L("lod err: %s" % e)
    try:
        b = sk.get_bounds()
        L("bounds origin=%s extent=%s" % (b.origin, b.box_extent))
        L("   z range: %.1f ~ %.1f  x: %.1f~%.1f  y: %.1f~%.1f" % (
            b.origin.z - b.box_extent.z, b.origin.z + b.box_extent.z,
            b.origin.x - b.box_extent.x, b.origin.x + b.box_extent.x,
            b.origin.y - b.box_extent.y, b.origin.y + b.box_extent.y))
    except Exception as e:
        L("bounds err: %s" % e)
    try:
        sks = sk.get_editor_property("sockets")
        for s in sks:
            L("   socket %s bone=%s loc=%s rot=%s scale=%s" % (
                s.get_editor_property("socket_name"), s.get_editor_property("bone_name"),
                s.get_editor_property("relative_location"), s.get_editor_property("relative_rotation"),
                s.get_editor_property("relative_scale")))
    except Exception as e:
        L("socket err: %s" % e)

L("")
L("=== [2] SM_Darius_GodKing_Axe ===")
sm = unreal.load_asset("/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")
L("asset: " + str(sm))
if sm:
    try:
        b = sm.get_bounds()
        L("bounds origin=%s extent=%s" % (b.origin, b.box_extent))
        L("   size(cm): X %.1f  Y %.1f  Z %.1f" % (b.box_extent.x * 2, b.box_extent.y * 2, b.box_extent.z * 2))
        L("   z range: %.1f ~ %.1f" % (b.origin.z - b.box_extent.z, b.origin.z + b.box_extent.z))
    except Exception as e:
        L("bounds err: %s" % e)
    try:
        L("material slots: %d" % sm.get_num_materials(0))
        for i in range(sm.get_num_materials(0)):
            L("   Slot[%d] -> %s" % (i, mat_name(sm.get_material(i))))
    except Exception as e:
        L("mat err: %s" % e)
    try:
        L("num sections LOD0: %d" % sm.get_num_sections(0))
    except Exception as e:
        L("sec err: %s" % e)
    try:
        for s in sm.get_editor_property("sockets"):
            L("   socket %s loc=%s rot=%s" % (s.get_editor_property("socket_name"),
                                              s.get_editor_property("relative_location"),
                                              s.get_editor_property("relative_rotation")))
    except Exception as e:
        L("socket err: %s" % e)

L("")
L("=== [3] BP_DariusCharacter SCS ===")
bp = unreal.load_asset("/Game/Character/Darius/Blueprints/BP_DariusCharacter")
L("bp: " + str(bp))
if bp:
    try:
        scs = bp.get_editor_property("simple_construction_script")
        nodes = scs.get_editor_property("all_nodes")
        L("SCS node count: %d" % len(nodes))
        for n in nodes:
            cc = n.get_editor_property("component_class")
            L("--- Node var=%s class=%s attachTo=%s parent=%s" % (
                n.get_editor_property("variable_name"),
                cc.get_name() if cc else None,
                n.get_editor_property("attach_to_name"),
                n.get_editor_property("parent_component_or_variable_name")))
            ct = n.get_editor_property("component_template")
            if ct:
                try:
                    L("      relLoc=%s relRot=%s relScale=%s" % (
                        ct.get_editor_property("relative_location"),
                        ct.get_editor_property("relative_rotation"),
                        ct.get_editor_property("relative_scale3d")))
                except Exception as e:
                    L("      xform err %s" % e)
                for prop in ("static_mesh", "visible", "cast_shadow", "hidden_in_game",
                             "collision_enabled", "collision_profile_name", "mobility"):
                    try:
                        L("      %s = %s" % (prop, ct.get_editor_property(prop)))
                    except Exception:
                        pass
                try:
                    nm = ct.get_num_materials()
                    for i in range(nm):
                        L("      Slot[%d] -> %s" % (i, mat_name(ct.get_material(i))))
                except Exception:
                    pass
    except Exception as e:
        L("scs err: %s" % e)

L("")
L("=== [4] M_Invisible ===")
mi = unreal.load_asset("/Game/Character/Darius/Materials/M_Invisible")
L("mat: " + str(mi))
if mi:
    for p in ("blend_mode", "cast_dynamic_shadow_as_masked", "two_sided"):
        try:
            L("   %s = %s" % (p, mi.get_editor_property(p)))
        except Exception:
            pass

L("")
L("=== [5] 资产清单 ===")
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for a in ar.get_assets_by_path("/Game/Character/Darius", recursive=True):
    L("   %s | %s" % (a.package_name, a.asset_class_path.asset_name))
L("=== DONE ===")
