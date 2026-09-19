# -*- coding: utf-8 -*-
"""查「角色到底在播什么」—— AnimBP 是不是还在用 UE 默认小人那套。

## 为什么需要它
`HANDOFF.md §5` 记着一条未决项：`CharacterMesh0.anim_class` 仍是 `ABP_Unarmed`。
`ABP_Unarmed` 是 UE 默认**小白人**的动画蓝图，它按 `ThirdPerson` 那套骨名找姿势；
挂到 310 根的 2XKO 骨架上，多半只会输出一堆**没被驱动的骨 = 参考姿势**，
看起来就像「手脚七歪八扭」。也就是说：**用户看到的扭曲，可能有一部分根本不是重定向的问题，
而是视口里压根没在播重定向产物。**

本脚本把「谁在播什么」一次问清楚：
  1. `BP_DariusCharacter` 的 CDO：`CharacterMesh0` 的 `skeletal_mesh` / `anim_class` / `anim_mode`
  2. 关卡里现有的 Darius 实例（若有）同样的三项
  3. 世界是否在 tick（`get_game_time_in_seconds` 两次采样）—— 关系到视口能不能看到动画
  4. `A_Darius_*` 产物的 `skeleton` 与 `SK_Darius_GodKing` 的 skeleton 是否一致
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

BP = "/Game/Character/Darius/Blueprints/BP_DariusCharacter"
MESH = "/Game/Character/Darius/SK_Darius_GodKing"


def show_comp(tag, comp):
    if comp is None:
        L("   %s: <没有 SkeletalMeshComponent>" % tag)
        return
    def g(p):
        try:
            return getattr(comp, p)
        except Exception as ex:
            return "<读不到 %s>" % str(ex)[:60]
    sm = g("skeletal_mesh")
    ac = g("anim_class")
    try:
        am = comp.get_editor_property("animation_mode")
    except Exception:
        am = "?"
    L("   %-22s mesh=%s" % (tag, sm.get_name() if sm else None))
    L("   %-22s anim_class=%s  mode=%s" % ("", ac.get_name() if ac else None, am))
    try:
        L("   %-22s anim_to_play=%s" % ("", comp.get_editor_property("animation_data").anim_to_play))
    except Exception:
        pass


L("################ 1. BP_DariusCharacter 的 CDO")
bp = eal.load_asset(BP)
if bp is None:
    LW("   load %s 失败" % BP)
else:
    try:
        cdo = unreal.get_default_object(bp.generated_class())
    except Exception:
        cdo = bp.get_editor_property("generated_class").get_default_object()
    L("   CDO = %s" % cdo)
    for attr in ("mesh", "character_mesh0"):
        try:
            show_comp("CDO.%s" % attr, getattr(cdo, attr))
        except Exception as ex:
            L("   CDO.%s 读不到: %s" % (attr, str(ex)[:80]))
    # 列出所有 SkeletalMeshComponent
    try:
        for c in cdo.get_components_by_class(unreal.SkeletalMeshComponent):
            show_comp("CDO<%s>" % c.get_name(), c)
    except Exception as ex:
        LW("   get_components_by_class 失败: %s" % str(ex)[:120])

L("")
L("################ 2. 关卡里的 Darius 实例")
n = 0
for a in actor_sub.get_all_level_actors():
    try:
        label = a.get_actor_label()
    except Exception:
        label = "?"
    if "Darius" not in label and "Darius" not in a.get_name():
        continue
    n += 1
    L("   actor %s (%s)" % (label, a.get_class().get_name()))
    for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
        show_comp("   %s" % c.get_name(), c)
L("   关卡里 Darius 相关 actor = %d 个" % n)

L("")
L("################ 3. 世界是否在 tick")
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    t0 = w.get_time_seconds()
    import time as _t
    _t.sleep(1.5)
    t1 = w.get_time_seconds()
    L("   world time %.4f -> %.4f  (Δ=%.4f)  %s"
      % (t0, t1, t1 - t0, "TICK_OK" if abs(t1 - t0) > 1e-4 else "!! TICK_FROZEN"))
except Exception as ex:
    LW("   取世界失败: %s" % str(ex)[:150])

L("")
L("################ 4. 产物骨架一致性")
sm = eal.load_asset(MESH)
sk = sm.get_editor_property("skeleton") if sm else None
L("   SK_Darius_GodKing.skeleton = %s" % (sk.get_name() if sk else None))
for p in ("/Game/Character/Darius/Anims_TP/A_Darius_idle1",
          "/Game/Character/Darius/Anims_TP/A_Darius_run"):
    a = eal.load_asset(p)
    if a is None:
        LW("   %s 不存在" % p)
        continue
    try:
        a_sk = a.get_editor_property("skeleton")
    except Exception:
        a_sk = None
    try:
        nf = int(unreal.AnimationLibrary.get_num_frames(a))
    except Exception:
        nf = -1
    try:
        nt = len(a.get_editor_property("bone_track_names"))
    except Exception:
        nt = -1
    L("   %-14s skeleton=%s  frames=%d  bone_tracks=%d"
      % (p.split("/")[-1], a_sk.get_name() if a_sk else None, nf, nt))

L("=== DONE ===")
