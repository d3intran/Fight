# -*- coding: utf-8 -*-
"""capture_retargeted_idle —— 离屏渲染 BP_DariusCharacter 播放 A_Darius_idle1"""
import unreal
import os

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eal = unreal.EditorAssetLibrary

# 清理任何残留
for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith(("TempIdle_", "SceneCapture2D_Idle")):
        actor_sub.destroy_actor(a)

anim = unreal.load_object(None, "/Game/Character/Darius/Animations/LOL_Retarget/A_Darius_idle1")

# 生成 BP_DariusCharacter
bp = unreal.load_class(None, "/Game/Character/Darius/Blueprints/BP_DariusCharacter.BP_DariusCharacter_C")
actor = actor_sub.spawn_actor_from_class(bp, unreal.Vector(0, 0, 125), unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0))
actor.set_actor_label("TempIdle_Showcase")

# 获取 Mesh 并播放动画
smc = actor.get_editor_property("mesh")
smc.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
smc.set_animation(anim)
smc.set_position(0.6) # 播放到 0.6s 姿态稳定处

# RT
if not eal.does_directory_exist("/Game/Temp"):
    eal.make_directory("/Game/Temp")
rt = unreal.load_asset("/Game/Temp/RT_IdleCap")
if rt is None:
    rt = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "RT_IdleCap", "/Game/Temp", unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew()
    )
rt.set_editor_property("size_x", 800)
rt.set_editor_property("size_y", 800)

sc_class = unreal.load_class(None, "/Script/Engine.SceneCapture2D")
# 相机正对角色正面 (BP_DariusCharacter yaw=180, 面向 +X 方向)
cap_actor = actor_sub.spawn_actor_from_class(sc_class, unreal.Vector(300.0, 0.0, 150.0), unreal.Rotator(pitch=-5.0, yaw=180.0, roll=0.0))
cap_actor.set_actor_label("SceneCapture2D_Idle")
cap = cap_actor.capture_component2d
cap.set_editor_property("texture_target", rt)
cap.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cap.set_editor_property("fov_angle", 42.0)
cap.set_editor_property("capture_every_frame", False)

cap.capture_scene()

out_file = "C:/Users/29226/.gemini/antigravity/brain/18caa78e-b5aa-4d96-abde-792ca1d14957/a_darius_idle1_verified.png"
unreal.RenderingLibrary.export_render_target(None, rt, os.path.dirname(out_file), os.path.basename(out_file))
unreal.log(f"自验截图已保存: {out_file}")

# 严格复位清理关卡
actor_sub.destroy_actor(actor)
actor_sub.destroy_actor(cap_actor)
unreal.log(f"关卡复位完成，当前 Actor 总数: {len(actor_sub.get_all_level_actors())}")
