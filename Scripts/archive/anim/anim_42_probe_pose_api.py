# -*- coding: utf-8 -*-
"""探针：查清「SceneCapture 采到的姿势不随 set_position 变化」的真因。

假设 A：组件根本没在 tick 动画 ⇒ 姿势恒为 set_position 那一次的结果
假设 B：组件有 `update_animation_in_editor` 之类的开关，spawn 出来默认 False
假设 C：set_position 生效了，但 SceneCapture 拿的是缓存的渲染状态

本脚本只读不改：打印相关 API、读两个不同帧下**组件实际求值出的骨骼变换**，
若两者相同 ⇒ 假设 A/B 成立（姿势没变）；若两者不同 ⇒ 假设 C 成立（渲染缓存）。
"""
import unreal

L = unreal.log
LW = unreal.log_warning
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

MESH = "/Game/Character/Darius/SK_Darius_GodKing"
ANIM = "/Game/Character/Darius/Anims_TP/A_Darius_run"
BONES = ["thigh_l", "lowerarm_l", "hand_l", "foot_l"]

# ---------------------------------------------------------------- 1. API 面
comp_cls = unreal.SkeletalMeshComponent
names = [n for n in dir(comp_cls)
         if any(k in n.lower() for k in ("pose", "bone", "tick", "editor", "update", "anim"))]
L("################ 1. SkeletalMeshComponent 相关 API（%d 个）" % len(names))
L("   " + ", ".join(sorted(names)))

for p in ("update_animation_in_editor", "b_update_animation_in_editor",
          "visibility_based_anim_tick_option", "animation_mode",
          "allow_anim_curve_metadata_update", "b_pause_anims_in_editor"):
    try:
        v = comp_cls.get_editor_property(comp_cls, p) if False else None
    except Exception:
        v = None
    L("   prop? %-40s" % p)

# ---------------------------------------------------------------- 2. 造 actor
killed = []
for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith(("SkeletalMeshAct", "SceneCapture2D_")):
        killed.append(a.get_name())
        actor_sub.destroy_actor(a)
L("")
L("清理: %s" % killed)

sm = unreal.load_asset(MESH)
actor = actor_sub.spawn_actor_from_class(unreal.SkeletalMeshActor,
                                         unreal.Vector(0.0, 0.0, 0.0),
                                         unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0))
actor.set_actor_label("Probe_Skel")
comp = actor.get_editor_property("skeletal_mesh_component")
comp.set_skinned_asset_and_update(sm)
try:
    comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    L("set_animation_mode OK")
except Exception as ex:
    LW("set_animation_mode: %s" % str(ex)[:90])

# ---------------------------------------------------------------- 3. 属性读写
L("")
L("################ 2. 关键属性当前值")
for p in ("update_animation_in_editor", "visibility_based_anim_tick_option",
          "animation_mode", "component_tick_interval", "component_has_begin_play"):
    for fn, tag in ((comp.get_editor_property, "get"),):
        try:
            L("   %-40s = %s" % (p, fn(p)))
        except Exception as ex:
            L("   %-40s <读不到> %s" % (p, str(ex)[:60]))

L("")
L("################ 3. 尝试打开编辑器内动画求值")
for p, v in (("update_animation_in_editor", True),
             ("visibility_based_anim_tick_option",
              unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE)):
    try:
        comp.set_editor_property(p, v)
        L("   set %-40s = %s  OK" % (p, v))
    except Exception as ex:
        LW("   set %-40s 失败: %s" % (p, str(ex)[:90]))


def read_pose(tag):
    out = []
    for b in BONES:
        try:
            m = comp.get_bone_transform(b, unreal.RelativeTransformSpace.RTS_Component)
            t = m.translation
            r = m.rotation
            out.append("%s=(%.2f,%.2f,%.2f|%.3f,%.3f,%.3f,%.3f)"
                       % (b, t.x, t.y, t.z, r.x, r.y, r.z, r.w))
        except Exception as ex:
            out.append("%s=ERR:%s" % (b, str(ex)[:40]))
    L("   [%s] %s" % (tag, "  ".join(out)))


# ---------------------------------------------------------------- 4. 换帧读姿势
anim = unreal.load_asset(ANIM)
L("")
L("################ 4. 换帧读组件实际姿势（anim=%s）" % (anim.get_name() if anim else "NONE"))
if anim is None:
    raise SystemExit(1)
comp.set_animation(anim)
try:
    comp.play(False)
except Exception as ex:
    LW("play: %s" % str(ex)[:80])

for f in (0, 9, 18, 27):
    t = f / 30.0
    try:
        comp.set_position(t, False)
    except Exception as ex:
        LW("set_position(%s): %s" % (t, str(ex)[:80]))
    read_pose("f%02d t=%.2f" % (f, t))

# ---------------------------------------------------------------- 5. 清理
killed2 = []
for a in actor_sub.get_all_level_actors():
    if a.get_name().startswith(("SkeletalMeshAct", "SceneCapture2D_")):
        killed2.append(a.get_name())
        actor_sub.destroy_actor(a)
L("")
L("已销毁: %s" % killed2)
L("剩余 actor: %s" % sorted([a.get_actor_label() for a in actor_sub.get_all_level_actors()]))
L("=== DONE ===")
