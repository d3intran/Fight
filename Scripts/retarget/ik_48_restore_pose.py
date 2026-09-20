# -*- coding: utf-8 -*-
"""回滚 / 重置 retarget pose 到**已知良好**的状态。

## 为什么必须有它
`ik_43`（auto align 探针）与 `ik_47`（解析求解）都会**就地改写并保存** retarget pose。
之前唯一的回滚手段是 `Saved/Backup_retarget_pose/*.uasset` 字节备份，
**必须关掉编辑器**才能还原 —— 一次实验的代价就变成「重启编辑器 5 分钟」。
本脚本用 `set_rotation_offset_for_retarget_pose_bone` 逐骨写回，
**不重启**就能回滚，实验才跑得起来。

## 已知良好基线 = `ik_36`（CHAIN_TO_CHAIN 全量对齐）的实测值
来源：`ik_38_pose_state.py` 在 `ik_36` 之后读出的快照。
它的成绩（`ik_37`，idle1 均值）：大腿L/R **0.01/0.01**、小腿L/R 5.77/4.94、
大臂L/R 9.62/16.89、小臂L/R 56.42/17.75、锁骨L/R 49.18/66.86、躯干 21.90、颈 39.94、头 62.65。
⇒ **腿是完美的**，这版是目前最好的；任何实验都以它为基准。

用法：`uv run --no-project python Scripts/ue_remote.py Scripts/retarget/ik_48_restore_pose.py`
（把 `Saved/retarget_cycle.json` 的 `restore.mode` 设为 `ik36` / `zero` / `backup_note`）
"""
import json
import os
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

CFG = "E:/UE/Fight/Saved/retarget_cycle.json"
RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"
MESH_TGT = "/Game/Character/Darius/SK_Darius_GodKing"
E = unreal.RetargetSourceOrTarget

cfg = {}
if os.path.isfile(CFG):
    with open(CFG, encoding="utf-8") as fh:
        cfg = json.load(fh)
mode = (cfg.get("restore") or {}).get("mode", "ik36")

# ik_36 之后的实测快照（单位：度，rotator = roll, pitch, yaw）
IK36 = {
    "spine_01":   (15.30, 6.85, -25.66),
    "spine_02":   (0.00, 0.00, 2.18),
    "upperarm_l": (-35.28, -18.91, -55.29),
    "lowerarm_l": (6.87, -2.76, 43.78),
    "upperarm_r": (66.28, 7.30, -11.16),
    "lowerarm_r": (0.00, 0.00, -22.50),
    "thigh_l":    (9.07, 4.02, -47.79),
    "calf_l":     (44.14, -21.10, 50.95),
    "thigh_r":    (40.42, 11.64, -30.96),
    "calf_r":     (-45.14, -4.58, -12.58),
}

# 累加状态：`ik_53` 每轮修出的偏移都会并进这个文件。
# 有了它才能「逐骨依次修」—— 否则每轮还原都会把上一轮的成果清掉。
POSE_EXTRA = "E:/UE/Fight/Saved/pose_extra.json"
EXTRA = {}
if os.path.isfile(POSE_EXTRA):
    try:
        with open(POSE_EXTRA, encoding="utf-8") as fh:
            EXTRA = {k: tuple(v) for k, v in json.load(fh).items()}
    except Exception as ex:
        LW("读 %s 失败: %s" % (POSE_EXTRA, ex))
L("累加状态 %s = %d 根骨" % (POSE_EXTRA.split("/")[-1], len(EXTRA)))

rtg = eal.load_asset(RTG)
ctrl = unreal.IKRetargeterController.get_controller(rtg)

# ---------------------------------------------------------------- 骨名表
sm = eal.load_asset(MESH_TGT)
a = actor_sub.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0))
a.set_actor_label("Probe_Restore")
comp = a.get_editor_property("skeletal_mesh_component")
try:
    comp.set_skinned_asset_and_update(sm)
except Exception:
    comp.set_skeletal_mesh(sm)
names = [str(comp.get_bone_name(i)) for i in range(int(comp.get_num_bones()))]
actor_sub.destroy_actor(a)

L("回滚模式 = %s ；目标骨 %d 根" % (mode, len(names)))


def set_off(bone, quat):
    for args in ((bone, E.TARGET, quat), (E.TARGET, bone, quat), (bone, quat, E.TARGET)):
        try:
            ctrl.set_rotation_offset_for_retarget_pose_bone(*args)
            return True
        except Exception:
            continue
    return False


identity = unreal.Quat(0.0, 0.0, 0.0, 1.0)
ok = 0
fail = []
for bn in names:
    if mode == "zero":
        q = identity
    elif mode == "ik36":
        # 累加状态优先于 ik36 表（它是「在 ik36 基础上继续修」的成果）
        d = EXTRA.get(bn) or IK36.get(bn)
        if d is None:
            q = identity
        else:
            # ⚠️ unreal.Rotator 的位置参数顺序是 (roll, pitch, yaw)
            q = unreal.Rotator(roll=d[0], pitch=d[1], yaw=d[2]).quaternion()
    else:
        LW("未知模式 %r" % mode)
        raise SystemExit(1)
    if set_off(bn, q):
        ok += 1
    else:
        fail.append(bn)
L("写入成功 %d / %d ；失败 %s" % (ok, len(names), fail[:6] if fail else "无"))

# ---------------------------------------------------------------- 复核
L("")
L("################ 复核（应与基线一致）")
for bn, d in IK36.items():
    for args in ((bn, E.TARGET), (E.TARGET, bn)):
        try:
            r = ctrl.get_rotation_offset_for_retarget_pose_bone(*args).rotator()
            L("   %-12s 期望 (%7.2f,%7.2f,%7.2f)  实读 (%7.2f,%7.2f,%7.2f)"
              % (bn, d[0], d[1], d[2], r.roll, r.pitch, r.yaw))
            break
        except Exception:
            pass
n_nonzero = 0
for bn in names:
    for args in ((bn, E.TARGET), (E.TARGET, bn)):
        try:
            q = ctrl.get_rotation_offset_for_retarget_pose_bone(*args)
            if abs(q.w) < 0.9999:
                n_nonzero += 1
            break
        except Exception:
            break
L("   非单位偏移骨数 = %d（ik36 应为 %d）" % (n_nonzero, len(IK36)))

L("")
# ⚠️ retarget pose 存在 **IK Rig** 资产里，不是 IK Retargeter 里 ⇒ 三个都要存
for p in (RTG, "/Game/Character/Darius/Retarget/IK_Darius_Target",
          "/Game/Character/Darius/Retarget/IK_LOL_Source"):
    try:
        L("   save %-20s -> %s" % (p.split("/")[-1], eal.save_asset(p, only_if_is_dirty=False)))
    except Exception as ex:
        LW("   save %s 失败: %s" % (p, str(ex)[:120]))
LW("!! retarget pose 已改 ⇒ 重跑 ik_11 才能让产物与它一致。")
L("=== DONE ===")
