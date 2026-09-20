import unreal

eal = unreal.EditorAssetLibrary
BS = "/Game/Character/Darius/Anims/BS_Darius_Locomotion"
NEW = "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Layered"
OLD = "/Game/Character/Darius/Anims/A_Darius_Walk_Layered"
AXE = "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Mixamo"

bs = eal.load_asset(BS)
if not bs:
    unreal.log_error("BS 加载失败")
    raise SystemExit(1)

unreal.log("### BS_Darius_Locomotion 当前样本")
axes = bs.get_editor_property("blend_parameters")
unreal.log("   轴 = %s" % [(str(a.get_editor_property("display_name")),
                            a.get_editor_property("min"), a.get_editor_property("max")) for a in axes])
samples = bs.get_editor_property("sample_data")
for i, s in enumerate(samples):
    anim = s.get_editor_property("animation")
    v = s.get_editor_property("sample_value")
    unreal.log("   [%d] anim=%-42s value=(%.1f, %.1f)" % (
        i, anim.get_name() if anim else None, v.x, v.y))

new_anim = eal.load_asset(NEW)
old_anim = eal.load_asset(OLD)
axe_anim = eal.load_asset(AXE)

changed = 0
rebuilt = []
for s in samples:
    a = s.get_editor_property("animation")
    v = s.get_editor_property("sample_value")
    rs = s.get_editor_property("rate_scale")
    ns = unreal.BlendSample()
    if a and a.get_path_name().split(".")[0] in (OLD, AXE):
        ns.set_editor_property("animation", new_anim)
        changed += 1
    else:
        ns.set_editor_property("animation", a)
    ns.set_editor_property("sample_value", v)
    ns.set_editor_property("rate_scale", rs)
    rebuilt.append(ns)
bs.set_editor_property("sample_data", rebuilt)
eal.save_asset(BS)
unreal.log("### 替换 %d 个样本 -> %s" % (changed, NEW))

bs2 = eal.load_asset(BS)
unreal.log("### 复核")
for i, s in enumerate(bs2.get_editor_property("sample_data")):
    a = s.get_editor_property("animation")
    v = s.get_editor_property("sample_value")
    unreal.log("   [%d] anim=%-42s value=(%.1f, %.1f)" % (
        i, a.get_name() if a else None, v.x, v.y))
unreal.log("### DONE")
