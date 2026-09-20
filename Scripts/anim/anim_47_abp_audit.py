# -*- coding: utf-8 -*-
"""审 AnimBP 与骨架的兼容性 —— 弄清「角色为什么一直显示参考姿势」。

## 背景（2026-09-19 实测）
`anim_46` 查出 `CharacterMesh0.anim_class = ABP_Unarmed_C`，`mode = ANIMATION_BLUEPRINT`。
`ABP_Unarmed` 是 **UE 默认小白人**的动画蓝图，骨架是 `SKM_Manny`/`SK_Mannequin` 那一套。
把它挂到 `SK_Darius_GodKing`（310 根骨）上，UE 会因为**骨架不兼容**而拒绝求值，
网格体就停在**参考姿势（A-pose）**上 —— 于是看到「手臂横向张开、手掌朝外」。

⇒ 这解释了 `HANDOFF.md §4` 第 2 步要回答的问题：**「手臂张开」不是动画，是参考姿势。**

本脚本把「谁能用、谁不能用」查清楚，并**不改任何东西**（只读）：
  1. 两个 AnimBP 的 `target_skeleton` / 父类
  2. `SK_Darius_GodKing` 的骨架
  3. 逐个比对是否兼容
  4. 关卡里 Darius actor 的当前状态
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

MESH = "/Game/Character/Darius/SK_Darius_GodKing"
ABPS = ["/Game/Character/Darius/Blueprints/ABP_Darius_Test",
        "/Game/Character/Darius/Blueprints/ABP_NodeTest",
        "/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed"]

sm = eal.load_asset(MESH)
sk_tgt = sm.get_editor_property("skeleton") if sm else None
L("################ 目标网格体")
L("   %s" % MESH)
L("   skeleton = %s" % (sk_tgt.get_path_name() if sk_tgt else None))

L("")
L("################ AnimBP 清单")
for p in ABPS:
    a = eal.load_asset(p)
    if a is None:
        LW("   %s  ->  不存在" % p)
        continue
    L("   %s" % p.split("/")[-1])
    L("      class = %s" % a.get_class().get_name())
    # 蓝图生成的类 → 拿骨架
    sk = None
    for attr in ("target_skeleton", "skeleton"):
        try:
            v = a.get_editor_property(attr)
            if v is not None:
                sk = v
                L("      %s = %s" % (attr, v.get_path_name()))
        except Exception:
            pass
    try:
        gc = a.generated_class()
        L("      generated_class = %s" % gc.get_name())
        # 从 CDO 的 mesh 组件读骨架
        cdo = unreal.get_default_object(gc)
        for c in cdo.get_components_by_class(unreal.SkeletalMeshComponent):
            try:
                m = c.get_editor_property("skeletal_mesh")
            except Exception:
                m = None
            try:
                msk = m.get_editor_property("skeleton") if m else None
            except Exception:
                msk = None
            L("      CDO<%s> mesh=%s skeleton=%s"
              % (c.get_name(), m.get_name() if m else None,
                 msk.get_name() if msk else None))
            if msk is not None and sk_tgt is not None:
                L("         ⇒ 与目标骨架%s" % ("**一致** ✅" if msk == sk_tgt else "**不一致** ❌"))
    except Exception as ex:
        LW("      读 generated_class 失败: %s" % str(ex)[:120])

L("")
L("################ 关卡实例现状")
for a in actor_sub.get_all_level_actors():
    lb = a.get_actor_label()
    if "Darius" not in lb:
        continue
    L("   %s (%s)" % (lb, a.get_class().get_name()))
    for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
        try:
            ac = c.get_editor_property("anim_class")
        except Exception:
            ac = None
        try:
            am = c.get_editor_property("animation_mode")
        except Exception:
            am = "?"
        L("      %s  anim_class=%s  mode=%s"
          % (c.get_name(), ac.get_name() if ac else None, am))
        # 兼容性：把 AnimBP 的类拿去问 SkeletalMeshComponent 能不能用
        if ac is not None and sk_tgt is not None:
            try:
                ok = unreal.AnimationLibrary.is_valid_anim_blueprint_class_for_skeleton(
                    ac, sk_tgt)
                L("      兼容性(AnimLibrary) = %s" % ok)
            except Exception as ex:
                L("      兼容性接口不可用: %s" % str(ex)[:100])

L("=== DONE ===")
