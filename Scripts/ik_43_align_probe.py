# -*- coding: utf-8 -*-
"""按 `Saved/retarget_cycle.json` 里的 `align_jobs` 施加 retarget pose 自动对齐，并存盘。

## 为什么需要它
`ik_36` 的标定把**腿修到 0.01°（完美）**，但上半身反而变差（锁骨 49~67°、头 62°、小臂 56°）。
`ik_38` 读回显示：`clavicle_*` / `neck_01` / `head` / `hand_*` / `foot_*` 的偏移**全是 0** ——
因为 `auto_align_all_bones(CHAIN_TO_CHAIN)` 是靠**链里子骨的方向**定朝向，
而这些骨所在的链**没有源对应**（源 IK Rig 只有 9 条链，目标 29 条）⇒ 无从对齐。

本脚本就是那个「换个方法再试一次」的旋钮：对指定的骨集合施加指定的对齐方法。
四种方法（`unreal.RetargetAutoAlignMethod`）：
  - CHAIN_TO_CHAIN (0)      —— 用子骨方向（Direction），链尾无效
  - MESH_TO_MESH (1)        —— 用网格顶点权重推方向，**对链尾最可能有效**
  - LOCAL_ROTATION_AXES (2) —— 用局部旋转轴
  - GLOBAL_ROTATION_AXES (3)—— 用全局旋转轴

## 配置（Saved/retarget_cycle.json）
```json
{ "out_dir": "/Game/.../Anims_TP_e1",
  "align_jobs": [ { "method": "MESH_TO_MESH", "bones": "ALL" },
                  { "method": "CHAIN_TO_CHAIN", "bones": ["spine_01","upperarm_l"] } ] }
```
`bones` 为 `"ALL"` 走 `auto_align_all_bones`，否则走 `auto_align_bones(选定集合)`。
jobs 按顺序执行。**每跑一次都会改 retarget pose 并存盘** ⇒ 旧产物作废，必须重跑 `ik_11`。
"""
import json
import os
import unreal

L = unreal.log
LW = unreal.log_warning
eal = unreal.EditorAssetLibrary

CFG = "E:/UE/Fight/Saved/retarget_cycle.json"
RTG = "/Game/Character/Darius/Retarget/RTG_LOL_to_Darius"
# retarget pose 存在 IK Rig 里 ⇒ 存盘必须连 IK Rig 一起（见文件末注释）
IK_TGT = "/Game/Character/Darius/Retarget/IK_Darius_Target"
IK_SRC = "/Game/Character/Darius/Retarget/IK_LOL_Source"
E = unreal.RetargetSourceOrTarget

cfg = {}
if os.path.isfile(CFG):
    try:
        with open(CFG, encoding="utf-8") as fh:
            cfg = json.load(fh)
    except Exception as ex:
        LW("配置读失败: %s" % ex)
jobs = cfg.get("align_jobs") or []
if not jobs:
    LW("!! 配置里没有 align_jobs，无事可做")
    raise SystemExit(1)

rtg = eal.load_asset(RTG)
ctrl = unreal.IKRetargeterController.get_controller(rtg)

M = unreal.RetargetAutoAlignMethod
METHODS = {n: getattr(M, n) for n in
           ("CHAIN_TO_CHAIN", "MESH_TO_MESH", "LOCAL_ROTATION_AXES", "GLOBAL_ROTATION_AXES")
           if hasattr(M, n)}

# 🔴 2026-09-19 实测：`auto_align_bones(TARGET, [骨名], 方法)` 是**空操作** ——
#    传骨名列表一个偏移都不改（`ik_38` 复核过），它要的是**链名**，
#    而链名在 Python 侧拿不到（`get_all_chain_settings()` 返回空数组）。
#    ⇒ 定向对齐只能这样拼：先 `auto_align_all_bones(方法)` 全量刷一遍，
#      再用 `KEEP_IK36` 把不想动的骨**逐骨写回**已知良好值。
#
# 🔴🔴 2026-09-19 更重要的实测（推翻上面那条「拼」法）：
#    **`get/set_rotation_offset_for_retarget_pose_bone` 读写的那个偏移量，
#    并不是驱动重定向的那个状态。** 两组硬证据（同一批 `exp_logs/cycle-20260919-014604.log`）：
#      1) `e4`（zero → CHAIN_TO_CHAIN 全量）读回的 `thigh_l` = (-6.39,-4.64,-71.97)，
#         与 `ik36` 表的 (9.07,4.02,-47.79) **差 26°**，可两者 `ik_37` 结果**逐位相同**
#         （大腿 0.01 / 小腿 5.77 / 大臂 9.62 / 锁骨 49.16 / 头 62.62 …）。
#      2) `e3`（GLOBAL）与 `e4`（CHAIN）的 `spine_03` 偏移只差 **0.25°**，
#         但「锁骨L」误差差 **34°**（15.0 vs 49.2）。
#    ⇒ 结论：**只有 `auto_align_all_bones` 真正写到了被使用的数据**；
#      逐骨写回（`ik_48` 的还原、本文件的 `KEEP_IK36`）**不可信**。
#      因此 `h2`（MESH 全量 + KEEP_IK36 写回腿）才出现「偏移读回正确、大腿却 100.7°」的怪象。
#    ⇒ 后续实验**只比较 `auto_align_all_bones` 的调用序列**，不要指望逐骨拼接。
#      （`ik_48` 之所以「看起来能还原」，是因为它跑完**没有重新导出**，
#        `ik_37` 读到的还是上一轮的旧产物 —— 这个假象已在本文件注释中留档。）

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


def offset(bone):
    for args in ((bone, E.TARGET), (E.TARGET, bone)):
        try:
            r = ctrl.get_rotation_offset_for_retarget_pose_bone(*args).rotator()
            return (r.roll, r.pitch, r.yaw)
        except Exception:
            pass
    return None


def dump(tag, bones):
    L("   --- %s" % tag)
    for b in bones:
        d = offset(b)
        L("      %-14s %s" % (b, ("(%7.2f, %7.2f, %7.2f)" % d) if d else "<读不到>"))


WATCH = ["darius_godking_mesh_LOD0_Skeleton", "root", "pelvis",
         "spine_01", "spine_02", "spine_03", "clavicle_l", "clavicle_r",
         "neck_01", "head",
         "upperarm_l", "lowerarm_l", "hand_l", "upperarm_r", "lowerarm_r", "hand_r",
         "thigh_l", "calf_l", "foot_l", "thigh_r", "calf_r", "foot_r"]

L("################ 施加前")
dump("施加前", WATCH)

for i, job in enumerate(jobs):
    name = job.get("method")
    bones = job.get("bones", "ALL")
    L("")
    L("################ job[%d] %s  bones=%s" % (i, name, bones if bones == "ALL" else len(bones)))

    if name in ("SET_BONE", "SET_TABLE"):
        # 逐骨写入**显式指定**的旋转（用来判定「写偏移」这条路到底通不通）。
        # 配置形如 {"method":"SET_BONE","table":{"thigh_l":[0,0,90]}}；
        # 表里没有的骨一律写单位四元数（等价于「清零」）。
        tbl = job.get("table") or {}
        bl = job.get("bones")
        if isinstance(bl, dict) and not tbl:
            tbl = bl
        if not tbl:
            LW("   %s 需要 table 字段" % name)
            continue
        n_ok = 0
        for b, d in tbl.items():
            if d is None:
                q = unreal.Quat(0.0, 0.0, 0.0, 1.0)
            else:
                q = unreal.Rotator(roll=d[0], pitch=d[1], yaw=d[2]).quaternion()
            wrote = False
            for args in ((str(b), E.TARGET, q), (E.TARGET, str(b), q), (str(b), q, E.TARGET)):
                try:
                    ctrl.set_rotation_offset_for_retarget_pose_bone(*args)
                    wrote = True
                    break
                except Exception:
                    continue
            n_ok += 1 if wrote else 0
        L("   写入 %d / %d 根骨" % (n_ok, len(tbl)))
        continue

    if name == "KEEP_IK36":
        # 逐骨写回 ik36 的已知良好值（腿就是靠这一手保住的）
        if bones == "ALL":
            LW("   KEEP_IK36 必须给具体骨名列表")
            continue
        n_ok = 0
        for b in bones:
            d = IK36.get(str(b))
            if d is None:
                LW("   %s 不在 ik36 表里，跳过" % b)
                continue
            q = unreal.Rotator(roll=d[0], pitch=d[1], yaw=d[2]).quaternion()
            wrote = False
            for args in ((str(b), E.TARGET, q), (E.TARGET, str(b), q), (str(b), q, E.TARGET)):
                try:
                    ctrl.set_rotation_offset_for_retarget_pose_bone(*args)
                    wrote = True
                    break
                except Exception:
                    continue
            n_ok += 1 if wrote else 0
        L("   写回 %d / %d 根骨" % (n_ok, len(bones)))
        continue

    if name not in METHODS:
        LW("job[%d] 未知方法 %r（可用：%s + KEEP_IK36）" % (i, name, list(METHODS)))
        continue
    try:
        if bones == "ALL":
            r = ctrl.auto_align_all_bones(E.TARGET, METHODS[name])
        else:
            r = ctrl.auto_align_bones(E.TARGET, [str(b) for b in bones], METHODS[name])
        L("   返回 %s" % r)
    except Exception as ex:
        LW("   失败: %s" % str(ex)[:200])

L("")
L("################ 施加后")
dump("施加后", WATCH)

L("")
L("################ 存盘")
# ⚠️ **retarget pose 存在 IK Rig 资产里，不是 IK Retargeter 资产里。**
#    实测（2026-09-19 01:49）：`RTG_LOL_to_Darius.uasset` 时间戳一直在更新，
#    而 `IK_Darius_Target.uasset` / `IK_LOL_Source.uasset` 停在 00:04 ——
#    说明此前所有 `auto_align_all_bones` 的结果**只活在内存里，从没落过盘**。
#    必须两边都存。
for p in (RTG, IK_TGT, IK_SRC):
    try:
        L("   save %-20s -> %s" % (p.split("/")[-1], eal.save_asset(p, only_if_is_dirty=False)))
    except Exception as ex:
        LW("   save %s 失败: %s" % (p, str(ex)[:120]))
LW("!! retarget pose 已改，`Anims_TP*` 里旧产物全部作废，必须重跑 ik_11。")
L("=== DONE ===")
