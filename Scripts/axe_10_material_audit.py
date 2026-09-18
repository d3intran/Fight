# -*- coding: utf-8 -*-
"""主材质 / 实例的混合模式与不透明遮罩审计"""
import unreal

def L(s=""):
    unreal.log(str(s))

def dump_mat(path):
    m = unreal.load_asset(path)
    L("")
    L("=== %s ===" % path)
    if not m:
        L("  !! 载入失败")
        return
    L("  class = %s" % m.get_class().get_name())
    for p in ("blend_mode", "shading_model", "two_sided", "opacity_mask_clip_value",
              "cast_dynamic_shadow_as_masked", "wireframe", "dithered_lod_transition",
              "used_with_skeletal_mesh", "used_with_static_lighting", "used_with_particle_sprites"):
        try:
            L("  %-30s = %s" % (p, m.get_editor_property(p)))
        except Exception as e:
            L("  %-30s <无此属性>" % p)
    for p in ("opacity", "opacity_mask"):
        try:
            st = m.get_editor_property(p)
            L("  %s:" % p)
            for f in ("use_constant", "constant", "expression"):
                try:
                    v = st.get_editor_property(f)
                    L("      %s = %s" % (f, v))
                except Exception:
                    pass
        except Exception as e:
            L("  %s <err %s>" % (p, e))
    try:
        L("  parent = %s" % m.get_editor_property("parent"))
    except Exception:
        pass

for p in ("/Game/Character/Darius/Materials/M_Darius_Master",
          "/Game/Character/Darius/Materials/MI_Darius_Axe",
          "/Game/Character/Darius/Materials/MI_Darius_BodyUpper",
          "/Game/Character/Darius/Materials/M_Invisible",
          "/Game/Character/Darius/Materials/M_Darius_Outline",
          "/Game/Character/Darius/Materials/MI_Darius_Outline"):
    dump_mat(p)

L("")
L("=== M_Darius_Master 材质图节点 ===")
m = unreal.load_asset("/Game/Character/Darius/Materials/M_Darius_Master")
if m:
    try:
        mel = unreal.MaterialEditingLibrary
        for cls in (unreal.MaterialExpressionTextureSample, unreal.MaterialExpressionTextureSampleParameter2D,
                    unreal.MaterialExpressionTextureObjectParameter, unreal.MaterialExpressionConstant,
                    unreal.MaterialExpressionScalarParameter, unreal.MaterialExpressionVectorParameter,
                    unreal.MaterialExpressionComponentMask, unreal.MaterialExpressionMultiply,
                    unreal.MaterialExpressionIf, unreal.MaterialExpressionStaticSwitchParameter):
            try:
                nodes = mel.get_material_expressions(m)
                hits = [n for n in nodes if isinstance(n, cls)]
                if hits:
                    L("  %s x%d" % (cls.__name__, len(hits)))
                    for n in hits[:12]:
                        try:
                            L("     - %s" % n.get_name())
                        except Exception:
                            pass
            except Exception:
                pass
        L("")
        L("  全部表达式:")
        for n in unreal.MaterialEditingLibrary.get_material_expressions(m):
            info = ""
            try:
                if isinstance(n, unreal.MaterialExpressionTextureSample):
                    info = " tex=%s" % n.get_editor_property("texture")
            except Exception:
                pass
            try:
                if isinstance(n, unreal.MaterialExpressionConstant):
                    info = " r=%s" % n.get_editor_property("r")
            except Exception:
                pass
            try:
                if isinstance(n, unreal.MaterialExpressionScalarParameter):
                    info = " default=%s" % n.get_editor_property("default_value")
            except Exception:
                pass
            L("   %-46s %s%s" % (n.get_class().get_name(), n.get_name(), info))
    except Exception as e:
        L("  node dump err: %s" % e)
L("=== DONE ===")
