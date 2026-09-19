# -*- coding: utf-8 -*-
"""M1-③ Retarget Pose 标定（v2：已探明枚举名与参数签名）。

## 为什么必须做这一步
重定向的本质是「比较源与目标在**同一参考姿势**下的差异，再带到每一帧」。
源是 A-Pose、目标是 T-Pose（或反之）⇒ **每一帧都继承那个姿态差**，
表现为肩膀错位、手臂角度不对、手腕/脚踝扭成麻花。
Epic 官方文档 + StraySpark 完整指南 + UE 论坛多帖都把「Retarget Pose 未标定」
列为这类症状的**头号原因**。这也是我们定稿计划里的 **M1-③**，此前被跳过。

## 官方推荐流程（本脚本实现）
1. Auto Align → **Align All Bones**（方法 = `CHAIN_TO_CHAIN`，即文档里的 Direction：
   只用关节连线方向，不依赖两套骨架的局部轴约定）
2. **复位脚/踝/趾**：自动对齐会把脚也拧过去，脚必须保持正确朝向
3. **Snap Character to Ground**：按身高差纵向吸附，避免漂浮/陷地
"""
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"
E = unreal.RetargetSourceOrTarget
M = unreal.RetargetAutoAlignMethod

rtg = eal.load_asset(RTG)
ctrl = unreal.IKRetargeterController.get_controller(rtg)


def try_sigs(label, fn, sigs):
    """依次尝试多组参数签名，返回第一个成功的返回值。"""
    for i, args in enumerate(sigs):
        try:
            r = fn(*args)
            L("  %-46s [sig%d] %s -> %s" % (label, i, args, r))
            return r
        except Exception as ex:
            LW("  %-46s [sig%d] : %s" % (label, i, str(ex)[:110]))
    return None


def offset_of(bone):
    for sigs in (((bone, E.TARGET), (E.TARGET, bone))):
        for a in (sigs,):
            try:
                return ctrl.get_rotation_offset_for_retarget_pose_bone(*a)
            except Exception:
                pass
    return None


PROBE_BONES = ["upperarm_l", "lowerarm_l", "hand_l", "thigh_l", "calf_l", "foot_l",
               "clavicle_l", "spine_01", "head"]


def snapshot(tag):
    L("  --- %s 的 retarget pose 旋转偏移" % tag)
    for b in PROBE_BONES:
        o = offset_of(b)
        if o is None:
            L("      %-14s <读不到>" % b)
            continue
        try:
            r = o.rotator() if hasattr(o, "rotator") else o
            L("      %-14s %s" % (b, r))
        except Exception:
            L("      %-14s %s" % (b, o))


L("################ 1. 标定前")
snapshot("标定前")

L("")
L("################ 2. Align All Bones（目标 → 源，方法 CHAIN_TO_CHAIN = Direction）")
try_sigs("auto_align_all_bones", ctrl.auto_align_all_bones,
         ((E.TARGET, M.CHAIN_TO_CHAIN), (E.TARGET,), (E.TARGET, M.MESH_TO_MESH)))

L("")
L("################ 3. 标定后")
snapshot("标定后")

L("")
L("################ 4. 复位脚/踝/趾（用「把旋转偏移置为单位四元数」实现 Reset）")
FEET = ["foot_l", "ball_l", "toe_l", "foot_r", "ball_r", "toe_r"]
identity = unreal.Quat(0.0, 0.0, 0.0, 1.0)
for b in FEET:
    r = try_sigs("reset %s" % b, ctrl.set_rotation_offset_for_retarget_pose_bone,
                 ((b, E.TARGET, identity), (E.TARGET, b, identity), (b, identity, E.TARGET)))
    if r is None:
        LW("     %s 复位失败" % b)

L("")
L("################ 5. Snap to Ground")
try_sigs("snap_bone_to_ground", ctrl.snap_bone_to_ground,
         (("", E.TARGET), (E.TARGET, ""), (E.TARGET,), (None, E.TARGET)))

L("")
L("################ 6. 最终快照 + 存盘")
snapshot("最终")
L("  存盘 -> %s" % eal.save_asset(RTG, only_if_is_dirty=False))
L("")
LW("!! retarget pose 一改，**之前导出的动画全部作废**（导出的是快照），必须重跑批量重定向。")
L("=== DONE ===")
