# -*- coding: utf-8 -*-
"""探针：判定「动画姿势不更新」到底是哪一层坏了。

三层嫌疑，逐层测：
  L1 世界有没有 tick      → get_game_time_in_seconds 前后两次是否前进
  L2 组件有没有 tick      → is_component_tick_enabled / tick 间隔 / anim instance 状态
  L3 姿势能不能被强制刷新 → play(True) 后 sleep，指纹是否变化；再试 reinitialize_anim_nodes

另外顺带验证一条备用路线：**PoseableMeshComponent + 自己算 FK 写骨骼变换**，
完全不依赖动画求值（`set_bone_transform_by_name` 是 BlueprintCallable）。
"""
import unreal
import time

L = unreal.log
LW = unreal.log_warning
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

MESH = "/Game/Character/Darius/SK_Darius_GodKing"
ANIM = "/Game/Character/Darius/Anims_TP/A_Darius_run"
BONES = ["thigh_l", "lowerarm_l", "hand_l", "foot_l"]
SP = unreal.RelativeTransformSpace.RTS_COMPONENT


def fp(comp):
    out = []
    for b in BONES:
        try:
            r = comp.get_bone_transform(b, SP).rotation
            out.append("%.3f,%.3f,%.3f,%.3f" % (r.x, r.y, r.z, r.w))
        except Exception as ex:
            out.append("ERR")
    return "|".join(out)


# ---------------------------------------------------------------- L1 世界 tick
L("################ L1 世界是否 tick")
try:
    t0 = unreal.SystemLibrary.get_game_time_in_seconds(world)
    time.sleep(1.2)
    t1 = unreal.SystemLibrary.get_game_time_in_seconds(world)
    L("   game_time %.4f -> %.4f  (Δ=%.4f)  %s"
      % (t0, t1, t1 - t0, "在 tick" if t1 > t0 + 1e-6 else "!! 世界没在 tick"))
except Exception as ex:
    LW("   读 game_time 失败: %s" % str(ex)[:100])

# ---------------------------------------------------------------- 造角色
for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith(("SkeletalMeshAct", "Probe_")):
        actor_sub.destroy_actor(a)

sm = unreal.load_asset(MESH)
anim = unreal.load_asset(ANIM)
actor = actor_sub.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0),
                                         unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0))
actor.set_actor_label("Probe_Skel")
comp = actor.get_editor_property("skeletal_mesh_component")
comp.set_skinned_asset_and_update(sm)
comp.set_editor_property("visibility_based_anim_tick_option",
                         unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE)
try:
    comp.set_update_animation_in_editor(True)
except Exception as ex:
    LW("set_update_animation_in_editor: %s" % str(ex)[:80])
try:
    comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
except Exception:
    pass
comp.set_animation(anim)

# ---------------------------------------------------------------- L2 组件 tick
L("")
L("################ L2 组件 tick 状态")
for fn, tag in ((comp.is_component_tick_enabled, "is_component_tick_enabled"),
                (comp.get_component_tick_interval, "get_component_tick_interval"),
                (comp.is_component_tick_enabled, "is_component_tick_enabled")):
    try:
        L("   %-32s = %s" % (tag, fn()))
    except Exception as ex:
        L("   %-32s <读不到> %s" % (tag, str(ex)[:60]))
for p in ("pause_anims", "update_animation_in_editor", "enable_update_rate_optimizations",
          "no_skeleton_update", "animation_mode"):
    try:
        L("   %-32s = %s" % (p, comp.get_editor_property(p)))
    except Exception:
        pass
try:
    ai = comp.get_anim_instance()
    L("   anim_instance = %s (%s)" % (ai, ai.get_class().get_name() if ai else "NONE"))
    if ai is not None:
        for p in ("position", "play_rate", "b_playing", "current_anim"):
            try:
                L("      ai.%-24s = %s" % (p, ai.get_editor_property(p)))
            except Exception:
                pass
except Exception as ex:
    LW("   get_anim_instance: %s" % str(ex)[:90])

# ---------------------------------------------------------------- L3 强制刷新
L("")
L("################ L3 姿势能否被强制刷新")
comp.set_position(0.0, False)
time.sleep(0.6)
a0 = fp(comp)
L("   set_position(0.0)      -> %s" % a0)

comp.set_position(0.9, False)
time.sleep(0.6)
a1 = fp(comp)
L("   set_position(0.9)      -> %s   %s" % (a1, "变了" if a1 != a0 else "没变"))

try:
    comp.play(True)
    time.sleep(1.2)
    a2 = fp(comp)
    L("   play(True)+1.2s        -> %s   %s" % (a2, "变了" if a2 != a1 else "没变"))
except Exception as ex:
    LW("   play(True): %s" % str(ex)[:80])

try:
    comp.reinitialize_anim_nodes(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    time.sleep(0.3)
    a3 = fp(comp)
    L("   reinitialize_anim_nodes-> %s   %s" % (a3, "变了" if a3 != a2 else "没变"))
except Exception as ex:
    LW("   reinitialize_anim_nodes: %s" % str(ex)[:90])

try:
    comp.set_component_tick_enabled(True)
    time.sleep(0.4)
    a4 = fp(comp)
    L("   set_component_tick_enabled(True) -> %s   %s" % (a4, "变了" if a4 != a3 else "没变"))
except Exception as ex:
    LW("   set_component_tick_enabled: %s" % str(ex)[:90])

# ---------------------------------------------------------------- 参考姿势对照
L("")
L("################ 参考姿势对照（判断当前是不是 rest pose）")
try:
    ref = []
    for b in BONES:
        r = comp.get_ref_pose_transform(b, SP).rotation
        ref.append("%.3f,%.3f,%.3f,%.3f" % (r.x, r.y, r.z, r.w))
    refs = "|".join(ref)
    L("   ref_pose  = %s" % refs)
    L("   当前姿势  = %s" % fp(comp))
    L("   ⇒ %s" % ("当前就是 rest pose（动画从未求值）" if refs == fp(comp) else "当前不是 rest pose"))
except Exception as ex:
    LW("   get_ref_pose_transform: %s" % str(ex)[:90])

# ---------------------------------------------------------------- 清理
for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith(("SkeletalMeshAct", "Probe_")):
        actor_sub.destroy_actor(a)
L("")
L("剩余 actor: %s" % sorted([a.get_actor_label() for a in actor_sub.get_all_level_actors()]))
L("=== DONE ===")
