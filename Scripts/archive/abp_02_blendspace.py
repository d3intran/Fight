import unreal

src = unreal.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/BS_Idle_Walk_Run")
print("=== 源 BlendSpace ===")
print("  skeleton:", src.get_editor_property("skeleton"))
try:
    bp = src.get_editor_property("blend_parameters")
    print("  轴数量:", len(bp))
    for i, p in enumerate(bp):
        print(f"   axis[{i}]:", {k: p.get_editor_property(k) for k in ["display_name", "min", "max", "grid_num", "snap_to_grid"]})
except Exception as e:
    print("  blend_parameters err:", e)
try:
    print("  sample_data 数量:", len(src.get_editor_property("sample_data")))
except Exception as e:
    print("  sample_data err:", e)
try:
    print("  preview_mesh:", src.get_editor_property("preview_base_mesh"))
except Exception as e:
    pass

# ---- 创建 Darius 版 BlendSpace ----
skel = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing_Skeleton")
mesh = unreal.load_asset("/Game/Character/Darius/SK_Darius_GodKing")
DST = "/Game/Character/Darius/Anims/BS_Darius_Locomotion"
if unreal.EditorAssetLibrary.does_asset_exist(DST):
    unreal.EditorAssetLibrary.delete_asset(DST)

fac = unreal.BlendSpaceFactoryNew()
try:
    fac.set_editor_property("target_skeleton", skel)
except Exception as e:
    print("  factory skeleton err:", e)
at = unreal.AssetToolsHelpers.get_asset_tools()
bs = at.create_asset("BS_Darius_Locomotion", "/Game/Character/Darius/Anims", unreal.BlendSpace, fac)
print("新建 BS:", bs)
if bs:
    try:
        bs.set_editor_property("skeleton", skel)
    except Exception as e:
        print("  set skeleton err:", e)
    try:
        bs.set_preview_skeletal_mesh(mesh)
    except Exception as e:
        print("  preview mesh err:", e)

    # 轴：Speed 0~600
    axes = []
    a0 = unreal.BlendParameter()
    a0.set_editor_property("display_name", "Speed")
    a0.set_editor_property("min", 0.0)
    a0.set_editor_property("max", 600.0)
    a0.set_editor_property("grid_num", 4)
    a0.set_editor_property("snap_to_grid", False)
    axes.append(a0)
    a1 = unreal.BlendParameter()
    a1.set_editor_property("display_name", "Direction")
    a1.set_editor_property("min", -180.0)
    a1.set_editor_property("max", 180.0)
    a1.set_editor_property("grid_num", 4)
    a1.set_editor_property("snap_to_grid", False)
    axes.append(a1)
    try:
        bs.set_editor_property("blend_parameters", axes)
        print("  轴写入 OK")
    except Exception as e:
        print("  轴写入失败:", e)

    # 样本
    def mk(anim_path, speed, direction):
        s = unreal.BlendSample()
        s.set_editor_property("animation", unreal.load_asset(anim_path))
        s.set_editor_property("sample_value", unreal.Vector(speed, direction, 0.0))
        s.set_editor_property("rate_scale", 1.0)
        return s

    samples = [
        mk("/Game/Character/Darius/Anims/A_Darius_Idle1_TP", 0.0, 0.0),
        mk("/Game/Character/Darius/Anims/A_Darius_Run_TP", 380.0, 0.0),
        mk("/Game/Character/Darius/Anims/A_Darius_RunFast_TP", 600.0, 0.0),
        mk("/Game/Character/Darius/Anims/A_Darius_Run_TP", 380.0, 90.0),
        mk("/Game/Character/Darius/Anims/A_Darius_Run_TP", 380.0, -90.0),
        mk("/Game/Character/Darius/Anims/A_Darius_Run_TP", 380.0, 180.0),
    ]
    try:
        bs.set_editor_property("sample_data", samples)
        print("  样本写入 OK:", len(bs.get_editor_property("sample_data")))
    except Exception as e:
        print("  样本写入失败:", e)
    for s in bs.get_editor_property("sample_data"):
        an = s.get_editor_property("animation")
        print("     ", an.get_name() if an else None, s.get_editor_property("sample_value"))
    print("  保存:", unreal.EditorAssetLibrary.save_loaded_asset(bs))
print("=== DONE ===")
