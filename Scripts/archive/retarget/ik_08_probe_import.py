# -*- coding: utf-8 -*-
"""探针：查 Interchange 的 pipeline 资产与可用类，定位「动画被丢掉」的开关。"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

# ---------------------------------------------------------------- 1) 可用类
names = sorted([n for n in dir(unreal) if "Interchange" in n])
L("=== dir(unreal) 含 Interchange 的名字 = %d 个 ===" % len(names))
for n in names:
    L("   %s" % n)

# ---------------------------------------------------------------- 2) pipeline 资产
CAND = [
    "/Interchange/Pipelines/DefaultFBXOBJAssetsPipeline",
    "/Interchange/Pipelines/DefaultFBXOBJSceneAssetsPipeline",
    "/Interchange/Pipelines/DefaultAssetsPipeline",
    "/Interchange/Pipelines/DefaultSceneAssetsPipeline",
]
L("")
for p in CAND:
    a = eal.load_asset(p)
    if a is None:
        LW("--- %s -> NOT FOUND" % p)
        continue
    L("--- %s -> %s" % (p, a.get_class().get_name()))
    attrs = [x for x in dir(a) if not x.startswith("_")]
    L("    attrs(%d): %s" % (len(attrs), ", ".join(attrs)))

# ---------------------------------------------------------------- 3) 深挖子 pipeline
a = eal.load_asset(CAND[0])
if a is not None:
    for sub in ("mesh_pipeline", "animation_pipeline", "material_pipeline",
                "texture_pipeline", "common_skeletal_meshes_and_animations_properties",
                "common_meshes_properties"):
        try:
            o = a.get_editor_property(sub)
        except Exception as ex:
            L("   %s: <无此属性> %s" % (sub, str(ex)[:60]))
            continue
        if o is None:
            L("   %s = None" % sub)
            continue
        sa = [x for x in dir(o) if not x.startswith("_")]
        L("   %s -> %s" % (sub, o.get_class().get_name()))
        L("      attrs(%d): %s" % (len(sa), ", ".join(sa)))
        for probe in ("import_animations", "b_import_animations", "import_animation",
                      "import_bone_tracks", "animation_length", "add_curve_metadata",
                      "use_source_animation_length"):
            for pn in (probe,):
                try:
                    L("      %s = %s" % (pn, o.get_editor_property(pn)))
                except Exception:
                    pass

L("=== DONE ===")
