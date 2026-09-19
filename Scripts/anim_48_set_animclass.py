# -*- coding: utf-8 -*-
"""把 `CharacterMesh0` 的 `anim_class` 从 **不兼容** 的 `ABP_Unarmed` 换成 `ABP_Darius_Test`。

## 为什么这是必须的
`anim_47` 实测：
    ABP_Unarmed.target_skeleton   = SK_Mannequin            ← UE 默认小白人
    SK_Darius_GodKing.skeleton    = SK_Darius_GodKing_Skeleton
两套骨架完全不同 ⇒ UE **拒绝求值**，网格体停在**参考姿势（A-pose）**
⇒ 看到「手臂横向张开、手掌朝外」= 用户说的「手脚七歪八扭」。
而 `ABP_Darius_Test` 的 target_skeleton 正是 `SK_Darius_GodKing_Skeleton`，可以用。

## 改哪里
蓝图里的组件**模板**（不是 CDO）才决定新建实例的默认值。
UE5 用 `SubobjectDataSubsystem` 找到模板对象再改，最后 `compile_blueprint`。
顺带把关卡里现存实例也改一遍，这样用户立刻能在视口里看到真实姿势。

用法：
    uv run --no-project python Scripts/ue_remote.py Scripts/anim_48_set_animclass.py
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

BP = "/Game/Character/Darius/Blueprints/BP_DariusCharacter"
ABP = "/Game/Character/Darius/Blueprints/ABP_Darius_Test"
COMP_NAME = "CharacterMesh0"

abp = eal.load_asset(ABP)
if abp is None:
    raise SystemExit("找不到 %s" % ABP)
abp_cls = abp.generated_class()
L("目标 AnimBP = %s  (class %s)" % (ABP.split("/")[-1], abp_cls.get_name()))

bp = eal.load_asset(BP)
if bp is None:
    raise SystemExit("找不到 %s" % BP)


def fix_component(tag, comp):
    try:
        cur = comp.get_editor_property("anim_class")
    except Exception as ex:
        LW("   %s 读 anim_class 失败: %s" % (tag, str(ex)[:100]))
        return False
    L("   %s 当前 anim_class = %s" % (tag, cur.get_name() if cur else None))
    if cur == abp_cls:
        L("   %s 已经是目标值，跳过" % tag)
        return True
    try:
        comp.set_editor_property("anim_class", abp_cls)
    except Exception as ex:
        LW("   %s 写 anim_class 失败: %s" % (tag, str(ex)[:140]))
        return False
    try:
        now = comp.get_editor_property("anim_class")
        L("   %s 写入后 = %s" % (tag, now.get_name() if now else None))
    except Exception:
        pass
    return True


# ---------------------------------------------------------------- 1. 蓝图里的组件模板
L("")
L("################ 1. 蓝图组件模板")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
sbfl = unreal.SubobjectDataBlueprintFunctionLibrary
n_fix = 0
try:
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    L("   子对象句柄 = %d 个" % len(handles))
    for h in handles:
        data = sds.k2_find_subobject_data_from_handle(h)
        obj = sbfl.get_object(data)
        if obj is None:
            continue
        nm = obj.get_name()
        if not isinstance(obj, unreal.SkeletalMeshComponent):
            continue
        L("   找到 SkeletalMeshComponent 模板: %s" % nm)
        if fix_component(nm, obj):
            n_fix += 1
except Exception as ex:
    LW("   SubobjectData 路径失败: %s" % str(ex)[:200])

if n_fix == 0:
    # 兜底：直接改 CDO（有些版本 CDO 与模板是同一对象）
    L("   退回 CDO 路径")
    try:
        cdo = unreal.get_default_object(bp.generated_class())
        for c in cdo.get_components_by_class(unreal.SkeletalMeshComponent):
            if fix_component("CDO.%s" % c.get_name(), c):
                n_fix += 1
    except Exception as ex:
        LW("   CDO 路径也失败: %s" % str(ex)[:200])

L("   共修改 %d 处" % n_fix)
try:
    ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    L("   compile_blueprint -> %s" % ok)
except Exception as ex:
    LW("   compile 失败: %s" % str(ex)[:150])
L("   存盘 -> %s" % eal.save_asset(BP, only_if_is_dirty=False))

# ---------------------------------------------------------------- 2. 关卡现存实例
L("")
L("################ 2. 关卡现存实例")
n_inst = 0
for a in actor_sub.get_all_level_actors():
    lb = a.get_actor_label()
    if "Darius" not in lb:
        continue
    for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
        if fix_component("%s.%s" % (lb, c.get_name()), c):
            n_inst += 1
    try:
        a.modify()
    except Exception:
        pass
L("   共处理 %d 个组件" % n_inst)

# ---------------------------------------------------------------- 3. 复核
L("")
L("################ 3. 复核（读回）")
try:
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = sds.k2_find_subobject_data_from_handle(h)
        obj = sbfl.get_object(data)
        if isinstance(obj, unreal.SkeletalMeshComponent):
            try:
                ac = obj.get_editor_property("anim_class")
                L("   模板 %-16s anim_class = %s" % (obj.get_name(), ac.get_name() if ac else None))
            except Exception:
                pass
except Exception as ex:
    LW("   复核失败: %s" % str(ex)[:120])

L("=== DONE ===")
