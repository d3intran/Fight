import unreal

eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
elsu = unreal.EditorLoadingAndSavingUtils

unreal.log("### 关卡 actor（基线应为 7）")
for a in eas.get_all_level_actors():
    loc = a.get_actor_location()
    unreal.log("   %-32s %-32s z=%.2f" % (a.get_name(), a.get_actor_label(), loc.z))

unreal.log("### 脏包检查（不要盲存）")
try:
    dm = [p.get_name() for p in elsu.get_dirty_map_packages()]
    dc = [p.get_name() for p in elsu.get_dirty_content_packages()]
    unreal.log("   dirty maps = %s" % dm)
    unreal.log("   dirty content = %s" % dc)
except Exception as ex:
    unreal.log("   ERR %s" % ex)

unreal.log("### /Game/Temp 残留")
try:
    for p in eal.list_assets("/Game/Temp", recursive=True, include_folder=False):
        unreal.log("   %s" % p)
except Exception as ex:
    unreal.log("   ERR %s" % ex)

unreal.log("### 关卡包里有没有混进临时对象（之前 create_render_target2d 把 RT 建在了地图包里）")
for cand in ("/Game/Level/Lv-FIght.Lv-FIght:TextureRenderTarget2D_0",
             "/Game/Level/Lv-FIght.Lv-FIght:TextureRenderTarget2D_1"):
    try:
        o = unreal.load_object(None, cand)
    except Exception as ex:
        o = "ERR %s" % ex
    unreal.log("   %-58s -> %s" % (cand, o))
unreal.log("### /Game/Level 下的资产")
try:
    for p in eal.list_assets("/Game/Level", recursive=True, include_folder=False):
        unreal.log("   %s" % p)
except Exception as ex:
    unreal.log("   ERR %s" % ex)

unreal.log("### 交付物自检")
A = "/Game/Character/Darius/Anims/A_Darius_AxeWalk_Layered"
a = eal.load_asset(A)
unreal.log("   存在 = %s" % eal.does_asset_exist(A))
unreal.log("   class = %s" % a.get_class().get_name())
unreal.log("   skeleton = %s" % a.get_editor_property("skeleton").get_path_name())
unreal.log("   length = %.4f s   keys = %d   frames = %d" % (
    a.get_play_length(),
    a.controller.get_model_interface().get_number_of_keys(),
    a.controller.get_model_interface().get_number_of_frames()))
unreal.log("   root_motion = %s   rate_scale = %.2f" % (
    a.get_editor_property("enable_root_motion"), a.get_editor_property("rate_scale")))

unreal.log("### BS_Darius_Locomotion 样本")
bs = eal.load_asset("/Game/Character/Darius/Anims/BS_Darius_Locomotion")
for i, s in enumerate(bs.get_editor_property("sample_data")):
    an = s.get_editor_property("animation")
    v = s.get_editor_property("sample_value")
    unreal.log("   [%d] %-30s (%.0f, %.0f)" % (i, an.get_name() if an else None, v.x, v.y))
unreal.log("### DONE")
