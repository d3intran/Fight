# -*- coding: utf-8 -*-
"""决定性 A/B：同一 SM，四种装配方式对照 + LOD/渲染参数全量输出"""
import unreal, os, time

def L(s=""):
    unreal.log(str(s))

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ew = ues.get_editor_world()

if les.is_in_play_in_editor():
    les.editor_request_end_play()
    L("!! PIE 未结束")
    raise SystemExit

killed = []
for a in actor_sub.get_all_level_actors():
    n = a.get_name()
    if n.startswith(("BP_DariusCharacter", "AXE_", "CameraActor_", "AxeProxy", "AxeCap_",
                     "SceneCapture2D_", "ABTest_", "StaticMeshActor_0", "StaticMeshActor_5",
                     "StaticMeshActor_6", "TempAudit_", "DariusShowcase")):
        killed.append(n); actor_sub.destroy_actor(a)
L("清理: %s" % killed)

sm = unreal.load_asset("/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe")
L("")
L("=== SM 渲染参数 ===")
for p in ("num_lods", "lod_group", "lod_for_collision", "min_lod", "important", "never_stream"):
    try:
        L("  %s = %s" % (p, sm.get_editor_property(p)))
    except Exception:
        pass
try:
    L("  LOD count = %s" % unreal.EditorStaticMeshLibrary.get_lod_count(sm))
except Exception as e:
    L("  lodcount err %s" % e)
for i in range(0, 4):
    try:
        L("  LOD%d verts=%s sections=%d" % (i, unreal.EditorStaticMeshLibrary.get_number_verts(sm, i),
                                            sm.get_num_sections(i)))
    except Exception:
        break

bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
actor = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125),
                                         unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0))
actor.set_actor_label("ABTest_Darius")
actor_sub.set_selected_level_actors([])
weapon = None
for c in actor.get_components_by_class(unreal.StaticMeshComponent):
    if "Weapon" in c.get_name():
        weapon = c
L("")
L("=== WeaponAxe 渲染参数 ===")
for p in ("forced_lod_model", "lod_bias", "override_materials", "override_vertex_colors",
          "use_as_occluder", "cast_shadow", "visible", "bounds_scale", "detail_mode",
          "affect_dynamic_indirect_lighting", "runtime_virtual_textures"):
    try:
        L("  %-34s = %s" % (p, weapon.get_editor_property(p)))
    except Exception:
        pass
L("  world_transform = %s" % weapon.get_world_transform())

# ---- 就地再摆一个同资产 StaticMeshActor，变换完全复制组件 ----
t = weapon.get_world_transform()
wrot = weapon.get_world_rotation()
clone = actor_sub.spawn_actor_from_class(unreal.StaticMeshActor, t.translation, wrot)
clone.set_actor_label("ABTest_Clone")
cc = clone.static_mesh_component
cc.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
cc.set_editor_property("static_mesh", sm)
clone.set_actor_transform(t, False, False)
L("clone spawned at %s rot %s scale %s" % (t.translation, wrot, t.scale3d))

# 再摆一个"只换 SM 强制刷新"的临时角色
actor2 = actor_sub.spawn_actor_from_class(bp, unreal.Vector(700, 0, 125),
                                          unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0))
actor2.set_actor_label("ABTest_Darius2")
w2 = None
for c in actor2.get_components_by_class(unreal.StaticMeshComponent):
    if "Weapon" in c.get_name():
        w2 = c
if w2:
    w2.set_editor_property("static_mesh", None)
    w2.set_editor_property("static_mesh", sm)
    L("Darius2 weapon re-set: %s" % w2.get_editor_property("static_mesh"))

# ---- RT + SceneCapture ----
if not unreal.EditorAssetLibrary.does_directory_exist("/Game/Temp"):
    unreal.EditorAssetLibrary.make_directory("/Game/Temp")
rt = unreal.load_asset("/Game/Temp/RT_AxeCap")
if rt is None:
    rt = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "RT_AxeCap", "/Game/Temp", unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew())
rt.set_editor_property("size_x", 1200); rt.set_editor_property("size_y", 900)

out = "E:/UE/Fight/Saved/Shots/AxeAudit"
os.makedirs(out, exist_ok=True)
sc_class = unreal.load_class(None, "/Script/Engine.SceneCapture2D")
ca = actor_sub.spawn_actor_from_class(sc_class, unreal.Vector(-520.0, -90.0, 140.0),
                                      unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
ca.set_actor_label("SceneCapture2D_ab")
cap = ca.capture_component2d
cap.set_editor_property("texture_target", rt)
cap.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cap.set_editor_property("fov_angle", 46.0)
cap.set_editor_property("capture_every_frame", False)

def snap(tag):
    cap.capture_scene(); time.sleep(0.9)
    unreal.RenderingLibrary.export_render_target(ew, rt, out, "AB_" + tag)
    L("snap AB_%s" % tag)

snap("0_baseline")            # 原样（角色 + 克隆 + 角色2 都在画面外/内）

# 隐藏角色自己的武器组件
weapon.set_editor_property("visible", False)
cap.set_editor_property("capture_every_frame", False)
snap("1_weapon_hidden")
weapon.set_editor_property("visible", True)

# 隐藏克隆的 actor（对照：如果是克隆在渲染斧刃，隐藏后应消失）
clone.set_actor_hidden_in_game(True)
snap("2_clone_hidden")

L("=== DONE ===")
