# -*- coding: utf-8 -*-
"""实验回路驱动器 —— 一次跑完「还原 → 对齐 → 导出 → 验收」若干组，输出汇总表。

## 为什么需要它
单轮实验要跑 4 个脚本（`ik_48` / `ik_43` / `ik_11` / `ik_37`），手工敲命令既慢又容易
把 `Saved/retarget_cycle.json` 写错。本脚本把「写配置 + 依次执行 + 抓日志 + 汇总」封装，
一轮实验只花一次 `ik_11` 的时间。

## 铁律（见 AGENTS.md §0）
- 每轮必须**换新输出目录**（`Anims_TP_<tag>`），因为 `ik_11` 拒绝写入非空目录，
  而在编辑器里删 AnimSequence 会让编辑器崩溃。
- 每轮开始前 `ik_48` 把 retarget pose 还原到**已知基线**（`zero` 或 `ik36`），
  否则上一轮的残留会污染本轮结论。

用法：
    uv run --no-project python Scripts/exp_cycle.py            # 跑默认实验组
    uv run --no-project python Scripts/exp_cycle.py e2 e3      # 只跑指定 tag
"""
import json
import os
import re
import subprocess
import sys
import time

ROOT = "E:/UE/Fight"
CFG = ROOT + "/Saved/retarget_cycle.json"
LOG_DIR = ROOT + "/Saved/exp_logs"
GW = [ROOT + "/Scripts/ue_remote.py"]

# 已经良好的骨（`ik_36` CHAIN_TO_CHAIN 的成绩），混合实验里要逐骨写回
KEEP_GOOD = ["thigh_l", "calf_l", "thigh_r", "calf_r",
             "upperarm_l", "upperarm_r", "spine_01", "spine_02", "lowerarm_r"]

# `ik_36` 的实测偏移表（度，rotator = roll/pitch/yaw），来自 `ik_38` 的读回快照
KEEP_TABLE_IK36 = {
    "spine_01":   [15.30, 6.85, -25.66],
    "spine_02":   [0.00, 0.00, 2.18],
    "upperarm_l": [-35.28, -18.91, -55.29],
    "lowerarm_l": [6.87, -2.76, 43.78],
    "upperarm_r": [66.28, 7.30, -11.16],
    "lowerarm_r": [0.00, 0.00, -22.50],
    "thigh_l":    [9.07, 4.02, -47.79],
    "calf_l":     [44.14, -21.10, 50.95],
    "thigh_r":    [40.42, 11.64, -30.96],
    "calf_r":     [-45.14, -4.58, -12.58],
}

# 「祖先骨」= 影响**整条骨链**世界旋转的骨。`dir(parent→child)` 只受父骨世界旋转影响，
# 所以祖先骨写错会连带把整条链的方向带偏。`ik36` 里这几根的偏移都是 0
# （不在 KEEP_TABLE_IK36 里 ⇒ 按 0 处理），复位成 0 就是回到已知良好状态。
RESET_ANCESTORS = {
    "darius_godking_mesh_LOD0_Skeleton": None,   # 骨架根
    "root": None,                                # 有些骨架叫 root
    "pelvis": None,                              # 大腿/脊柱的共同祖先
}


# 已知良好姿势（ik36 = CHAIN_TO_CHAIN 全量）**已经导出并修过 scale** 的那批产物。
# `ik_53`（修 twist）要拿它当「当前姿势」的参考来算修正量 —— 不能指向本轮的新目录。
IK36_ANIM_DIR = "/Game/Character/Darius/Anims_TP_t3"


def ik36_with(**deltas):
    """`ik36` 全表 + 指定骨的 rotator 分量增量（度）。

    用途：**twist 轴探针**。`ik_37` 原判据对「绕骨轴自转」免疫（见 `ik_37` 注释），
    新加的 twist 判据里真正独立的只有末梢方向（脚/手）。要修 twist 就得知道
    「offset 的哪个分量对应绕骨轴自转」—— 本函数用来生成三个正交探针。
    """
    t = {k: list(v) for k, v in KEEP_TABLE_IK36.items()}
    for b, d in deltas.items():
        base = t.setdefault(b, [0.0, 0.0, 0.0])
        for i in range(3):
            base[i] += d[i]
    return t


def c6_base(**extra):
    """当前最优姿势（c6）+ 指定骨的**增量**（叠加，不是替换）。

    c6 = ik36 全表 + `spine_03` yaw+48（修锁骨/颈/头）
        + `upperarm_l` yaw+49 / `upperarm_r` yaw−49（镜像补偿下游）
        + `lowerarm_l` yaw+30（修小臂L/肘面L）。
    `best` 交付物 = c6 + 脚部 twist 修正。
    """
    base = {"spine_03": (0, 0, 48), "upperarm_l": (0, 0, 49),
            "upperarm_r": (0, 0, -49), "lowerarm_l": (0, 0, 30)}
    for k, v in extra.items():
        b = base.get(k, (0.0, 0.0, 0.0))
        base[k] = tuple(b[i] + v[i] for i in range(3))
    return ik36_with(**base)


# tag -> (restore_mode, align_jobs, 说明)
EXPS = {
    "z0": ("zero", [{"method": "NOOP"}],
           "★ 纯零基线：所有偏移为 0（`NOOP` 会被 ik_43 当未知方法跳过）"),
    "e2": ("zero", [{"method": "LOCAL_ROTATION_AXES", "bones": "ALL"}],
           "LOCAL_ROTATION_AXES 全量"),
    "e3": ("zero", [{"method": "GLOBAL_ROTATION_AXES", "bones": "ALL"}],
           "GLOBAL_ROTATION_AXES 全量"),
    "e4": ("zero", [{"method": "CHAIN_TO_CHAIN", "bones": "ALL"}],
           "CHAIN_TO_CHAIN 全量（复现 ik36，对照）"),
    "e1": ("zero", [{"method": "MESH_TO_MESH", "bones": "ALL"}],
           "MESH_TO_MESH 全量"),
    "cg": ("zero", [{"method": "CHAIN_TO_CHAIN", "bones": "ALL"},
                    {"method": "GLOBAL_ROTATION_AXES", "bones": "ALL"}],
           "CHAIN → GLOBAL（测两种方法能否按骨叠加）"),
    "gc": ("zero", [{"method": "GLOBAL_ROTATION_AXES", "bones": "ALL"},
                    {"method": "CHAIN_TO_CHAIN", "bones": "ALL"}],
           "GLOBAL → CHAIN（同上，反序）"),
    "cm": ("zero", [{"method": "CHAIN_TO_CHAIN", "bones": "ALL"},
                    {"method": "MESH_TO_MESH", "bones": "ALL"}],
           "CHAIN → MESH"),
    # ---------------------------------------------------------------- 判定「写偏移」这条路
    "t1": ("zero", [{"method": "SET_BONE", "table": {"thigh_l": [0, 0, 90],
                                                     "thigh_r": [0, 0, 90]}}],
           "★ 只把大腿绕 Z 拧 90°：若「大腿L」误差不变 ⇒ 逐骨写入无效"),
    "t3": ("zero", [{"method": "SET_BONE", "table": KEEP_TABLE_IK36}],
           "★ 用 SET_BONE 写回 ik36 全表：与 e4 对比可判定读/写是否同一套约定"),
    "t2": ("zero", [{"method": "SET_BONE", "table": {"thigh_l": [0, 0, 90]}},
                    {"method": "CHAIN_TO_CHAIN", "bones": "ALL"}],
           "写偏移后再跑 CHAIN 全量：看 CHAIN 是否把它盖掉"),
    # ---------------------------------------------------------------- 复位「祖先骨」后能否救回
    # 推断：`dir(parent→child)` 只受**父骨的世界旋转**影响，而大腿的祖先链是
    # `根骨 → pelvis → thigh_*`。`MESH`/`GLOBAL` 会给祖先骨写一个很大的偏移，
    # 于是即使把 `thigh_*` 写回正确值，腿依然被祖先带歪（`h2` 的 100.7° 就是这么来的）。
    # 这组实验把祖先骨的偏移**单独复位**，看能不能既保住链尾的改善、又救回腿。
    "m1": ("zero", [{"method": "MESH_TO_MESH", "bones": "ALL"},
                    {"method": "SET_BONE", "table": RESET_ANCESTORS}],
           "★ MESH 全量后只复位祖先骨"),
    "g1": ("zero", [{"method": "GLOBAL_ROTATION_AXES", "bones": "ALL"},
                    {"method": "SET_BONE", "table": RESET_ANCESTORS}],
           "★ GLOBAL 全量后只复位祖先骨（GLOBAL 的锁骨/颈/头最好）"),
    "c1": ("zero", [{"method": "CHAIN_TO_CHAIN", "bones": "ALL"},
                    {"method": "SET_BONE", "table": RESET_ANCESTORS}],
           "对照：CHAIN 全量后复位祖先骨（应等于 e4）"),
    "h2": ("zero", [{"method": "MESH_TO_MESH", "bones": "ALL"},
                    {"method": "KEEP_IK36", "bones": KEEP_GOOD}],
           "MESH 全量 + 逐骨写回（已知不可信，留作反例）"),
    # ---------------------------------------------------------------- twist 轴探针
    # 目的：找出「offset 的哪个 rotator 分量 = 绕骨轴自转」。
    # 判读：绕骨轴自转**不改** dir(父→子) ⇒ 小腿L 不动、脚L 大动 的那个分量才是轴向。
    "cr": ("zero", [{"method": "SET_BONE", "table": ik36_with(calf_l=(45, 0, 0))}],
           "twist 探针：calf_l 加 45° roll"),
    "cp": ("zero", [{"method": "SET_BONE", "table": ik36_with(calf_l=(0, 45, 0))}],
           "twist 探针：calf_l 加 45° pitch"),
    "cy": ("zero", [{"method": "SET_BONE", "table": ik36_with(calf_l=(0, 0, 45))}],
           "twist 探针：calf_l 加 45° yaw"),
    # ---------------------------------------------------------------- twist 修正（三种约定）
    # 基底用 ik36（已知最好的姿势），只在 foot_*/hand_* 上补 twist 修正。
    # 判读：看「脚L/脚R/手L/手R」四行能不能压到 <8°，同时**其余 13 段不许变差**。
    "tw_self": ("ik36", [{"method": "NOOP"},
                         {"method": "FIX_TWIST", "convention": "self"}],
                "twist 修正 · offset 作用在**自身系**"),
    "tw_par": ("ik36", [{"method": "NOOP"},
                        {"method": "FIX_TWIST", "convention": "parent"}],
               "twist 修正 · offset 作用在**父系**"),
    "tw_world": ("ik36", [{"method": "NOOP"},
                          {"method": "FIX_TWIST", "convention": "world"}],
                 "twist 修正 · offset 作用在**世界系**"),
    # 只用脚的两条 job（手先不动）—— 手在 tw_self 里反而变差，怀疑是**指骨对应关系不对**
    "tw_feet": ("ik36", [{"method": "NOOP"},
                         {"method": "FIX_TWIST", "convention": "self",
                          "jobs": [["foot_l", "ball_l", "L_Toe"],
                                   ["foot_r", "ball_r", "R_Toe"]]}],
                "twist 修正 · **只修脚**（自身系）"),
    # 换目标侧的叶骨：2XKO 手腕与手指之间多一根 `middle_metacarpal_l`，LOL 没有
    # ⇒ `hand_l→middle_01_l` 与 `L_Hand→L_Middle1` 可能**根本不是同一个方向**。
    "tw_hmeta": ("ik36", [{"method": "NOOP"},
                          {"method": "FIX_TWIST", "convention": "self",
                           "jobs": [["hand_l", "middle_metacarpal_l", "L_Middle1"],
                                    ["hand_r", "middle_metacarpal_r", "R_Middle1"]]}],
                 "twist 修正 · 手改用**掌骨**作叶骨（试对应关系）"),
    # ---------------------------------------------------------------- 方向修正（上半身 5 段）
    # 控制骨 `spine_01` / `spine_03` / `neck_01` 在 ik36 里偏移都是 0（不在表里）
    # ⇒ 「锁骨L/R + 颈 + 躯干 + 头」这 5 段一直超门限。
    # 作业是 **5 元组**：[目标骨, 目标父, 目标叶, 源父, 源叶]。
    # ⚠️ 按层级顺序跑：`spine_03` 是 `neck_01` 的祖先，先修上游。
    # ⚠️ 只挑**对应关系干净**的段：`Spine2→Neck` vs `spine_03→neck_01`、
    #    `Neck→Head` vs `neck_01→head`。
    #    「躯干」(`Spine1→Spine2` vs `spine_01→spine_02`) **不干净** ——
    #    源 2 根脊柱骨、目标 3 根，那段是苹果比橘子，先不动。
    "fx_s03": ("ik36", [{"method": "NOOP"},
                        {"method": "FIX_TWIST", "convention": "self",
                         "jobs": [["spine_03", "spine_03", "neck_01", "Spine2", "Neck"]]}],
               "方向修正 · `spine_03`（管「颈」，应连带改善锁骨L/R）"),
    "fx_neck": ("ik36", [{"method": "NOOP"},
                         {"method": "FIX_TWIST", "convention": "self",
                          "jobs": [["neck_01", "neck_01", "head", "Neck", "Head"]]}],
                "方向修正 · `neck_01`（管「头」）—— 依赖上一轮的累加状态"),
    # `fx_s03` 只把「颈」从 39.94 修到 29.50（|Q|=39.89 ⇒ 本该到 0）
    # ⇒ 把 Q 折进 offset 用的那个**参照系**不对。三种约定再各跑一次，直接看谁能到 0。
    "fx_s03p": ("ik36", [{"method": "NOOP"},
                         {"method": "FIX_TWIST", "convention": "parent",
                          "jobs": [["spine_03", "spine_03", "neck_01", "Spine2", "Neck"]]}],
                "方向修正 · spine_03 · 约定=**父系**"),
    "fx_s03w": ("ik36", [{"method": "NOOP"},
                         {"method": "FIX_TWIST", "convention": "world",
                          "jobs": [["spine_03", "spine_03", "neck_01", "Spine2", "Neck"]]}],
                "方向修正 · spine_03 · 约定=**世界系**"),
    # ---------------------------------------------------------------- 参照系**实测标定**
    # 前三次「猜约定」全错（§2.6）。改用实测：对同一根骨加 3 个正交探针（各 +30° 绕一轴），
    # 看「颈 / 锁骨L / 锁骨R / 头」怎么变 —— 从而反解出「哪个 rotator 方向是轴向」，
    # 以及「观测到的方向变化 ↔ rotator 增量」的 3×3 映射，不再靠猜。
    "sr": ("ik36", [{"method": "SET_BONE", "table": ik36_with(spine_03=(30, 0, 0))}],
           "标定探针：spine_03 +30° roll"),
    "sp": ("ik36", [{"method": "SET_BONE", "table": ik36_with(spine_03=(0, 30, 0))}],
           "标定探针：spine_03 +30° pitch"),
    "sy": ("ik36", [{"method": "SET_BONE", "table": ik36_with(spine_03=(0, 0, 30))}],
           "标定探针：spine_03 +30° yaw"),
    # ★ 探针结论：`spine_03` 的 **yaw 就是轴向** —— +30° 让「颈/锁骨L/锁骨R/头」各改善 ~25-30°。
    #   外推（颈 39.93→14.84，约 −0.84°/°）≈ +48° 能把「颈」压到 0。做一轮 yaw 扫描找最优点。
    "sy45": ("ik36", [{"method": "SET_BONE", "table": ik36_with(spine_03=(0, 0, 45))}],
             "spine_03 yaw 扫描 · +45°"),
    "sy60": ("ik36", [{"method": "SET_BONE", "table": ik36_with(spine_03=(0, 0, 60))}],
             "spine_03 yaw 扫描 · +60°"),
    "sy75": ("ik36", [{"method": "SET_BONE", "table": ik36_with(spine_03=(0, 0, 75))}],
             "spine_03 yaw 扫描 · +75°"),
    "sy48": ("ik36", [{"method": "SET_BONE", "table": ik36_with(spine_03=(0, 0, 48))}],
             "spine_03 yaw 扫描 · +48°（外推最优）"),
    # ---------------------------------------------------------------- 手臂补偿的标定
    # `spine_03` 转 +48° 后手臂被带歪（大臂L 9.50→35.71）。要对下游做**反向补偿**，
    # 先得知道「`upperarm_l` 的哪个 rotator 方向能把它转回去」—— 同法实测。
    # 基线 = ik36 + spine_03 yaw 48，再对 `upperarm_l` 各加 +30° 绕一轴。
    "ar48": ("ik36", [{"method": "SET_BONE",
                       "table": ik36_with(spine_03=(0, 0, 48), upperarm_l=(30, 0, 0))}],
             "补偿标定：spine_03 +48y 且 upperarm_l +30 roll"),
    "ap48": ("ik36", [{"method": "SET_BONE",
                       "table": ik36_with(spine_03=(0, 0, 48), upperarm_l=(0, 30, 0))}],
             "补偿标定：spine_03 +48y 且 upperarm_l +30 pitch"),
    "ay48": ("ik36", [{"method": "SET_BONE",
                       "table": ik36_with(spine_03=(0, 0, 48), upperarm_l=(0, 0, 30))}],
             "补偿标定：spine_03 +48y 且 upperarm_l +30 yaw"),
    # 标定结论：`upperarm_l` 的 **yaw** 也最有效（大臂L 35.71→19.76，小臂L 63.28→40.85），
    # 且**只影响左臂**（大臂R 恒为 27.33）⇒ 隔离干净。
    # 大臂L 需从 35.71 回到 ~9.50，按 −0.532°/° 需 yaw ≈ +49°。
    # 右臂的误差性质不同（spine_03 +30 pitch 曾把大臂R 修到 5.63），先试正负两个方向。
    "c1": ("ik36", [{"method": "SET_BONE",
                     "table": ik36_with(spine_03=(0, 0, 48),
                                        upperarm_l=(0, 0, 49), upperarm_r=(0, 0, 49))}],
           "下游补偿：spine_03+48y，双 upperarm +49y"),
    "c2": ("ik36", [{"method": "SET_BONE",
                     "table": ik36_with(spine_03=(0, 0, 48),
                                        upperarm_l=(0, 0, 49), upperarm_r=(0, 0, -49))}],
           "下游补偿：spine_03+48y，upperarm_l +49y / upperarm_r −49y"),
    # `c2` 后大臂L 仍 24.58（基线 9.50），响应率 −0.532°/° ⇒ 再加 ≈28°（合计 77°）。
    "c3": ("ik36", [{"method": "SET_BONE",
                     "table": ik36_with(spine_03=(0, 0, 48),
                                        upperarm_l=(0, 0, 77), upperarm_r=(0, 0, -77))}],
           "下游补偿 · 加量：upperarm ±77y"),
    # 小臂/手由 `lowerarm_*` 控制 —— 补它们。左右同样镜像。
    "c4": ("ik36", [{"method": "SET_BONE",
                     "table": ik36_with(spine_03=(0, 0, 48),
                                        upperarm_l=(0, 0, 77), upperarm_r=(0, 0, -77),
                                        lowerarm_l=(0, 0, 30), lowerarm_r=(0, 0, -30))}],
           "下游补偿 · 再加 lowerarm ±30y"),
    "c5": ("ik36", [{"method": "SET_BONE",
                     "table": ik36_with(spine_03=(0, 0, 48),
                                        upperarm_l=(0, 0, 77), upperarm_r=(0, 0, -77),
                                        lowerarm_l=(0, 0, -30), lowerarm_r=(0, 0, 30))}],
           "下游补偿 · lowerarm 反号（对照）"),
    # 汇总三组的最好部分：`c2` 的双臂 upperarm（大臂R/小臂R/肘面R 都好）
    # + `c4` 的 `lowerarm_l`（把肘面L 打到 2.85）。只动左小臂，别碰右小臂。
    "c6": ("ik36", [{"method": "SET_BONE",
                     "table": ik36_with(spine_03=(0, 0, 48),
                                        upperarm_l=(0, 0, 49), upperarm_r=(0, 0, -49),
                                        lowerarm_l=(0, 0, 30))}],
           "★ 汇总最优：spine_03+48y / upperarm ±49y / lowerarm_l +30y"),
    # ★★ 把「层级联立」的结果与「脚部 twist 修正」叠起来，出**新交付物**。
    # 姿势 = c6 那张表；twist 的修正量从 `Anims_TP_c6`（c6 已导出的那批）读。
    "best": ("ik36", [{"method": "SET_BONE",
                       "table": ik36_with(spine_03=(0, 0, 48),
                                          upperarm_l=(0, 0, 49), upperarm_r=(0, 0, -49),
                                          lowerarm_l=(0, 0, 30))},
                      {"method": "FIX_TWIST", "convention": "self",
                       "anim_dir": "/Game/Character/Darius/Anims_TP_c6",
                       "jobs": [["foot_l", "ball_l", "L_Toe"],
                                ["foot_r", "ball_r", "R_Toe"]]}],
              "★★ 交付物：c6 姿势 + 脚部 twist 修正"),
    # ---------------------------------------------------------------- 收敛扫描（d 系列，2026-09-19 第五轮）
    # c6 基础上收敛剩余段：大臂L 24.58（ay48 显示最小值在 +30~49 之间，c3 证明 +77 过冲）、
    # 躯干 21.85（spine_01 从未探过）、头 21.93（neck_01 从未探过）。
    "d1": ("ik36", [{"method": "SET_BONE", "table": c6_base(upperarm_l=(0, 0, -14))}],
           "收敛：upperarm_l yaw 49→35（细扫）"),
    "d2": ("ik36", [{"method": "SET_BONE", "table": c6_base(upperarm_l=(0, 0, -7))}],
           "收敛：upperarm_l yaw 49→42（细扫）"),
    "d3": ("ik36", [{"method": "SET_BONE", "table": c6_base(spine_01=(30, 0, 0))}],
           "探针：spine_01 +30 roll（管躯干）"),
    "d4": ("ik36", [{"method": "SET_BONE", "table": c6_base(spine_01=(0, 30, 0))}],
           "探针：spine_01 +30 pitch（管躯干）"),
    "d5": ("ik36", [{"method": "SET_BONE", "table": c6_base(spine_01=(0, 0, 30))}],
           "探针：spine_01 +30 yaw（管躯干）"),
    "d6": ("ik36", [{"method": "SET_BONE", "table": c6_base(neck_01=(30, 0, 0))}],
           "探针：neck_01 +30 roll（管头）"),
    "d7": ("ik36", [{"method": "SET_BONE", "table": c6_base(neck_01=(0, 30, 0))}],
           "探针：neck_01 +30 pitch（管头）"),
    "d8": ("ik36", [{"method": "SET_BONE", "table": c6_base(neck_01=(0, 0, 30))}],
           "探针：neck_01 +30 yaw（管头）"),
    # ---------------------------------------------------------------- 交付物 v2（d 系列收敛结论）
    # d1/d2：uL yaw 42 优于 49（大臂L 24.58→21.34，小臂L 10.25 保持）；d3~d5：spine_01
    # 三个 +30 探针全部恶化 ⇒ 躯干不动（要试只能负向）；d8：neck_01 +30 yaw 把
    # 颈面 94.78→6.01（头绕颈轴的平面扭曲被修正，代价 头 +2.3）。
    # ⚠️ 脚部 twist 已在 Saved/pose_extra.json 里，随 ik_48 还原自动带上（d 系列脚L/R
    #    全程 5.06/15.64 可证），无需再挂 FIX_TWIST 作业。
    "v2": ("ik36", [{"method": "SET_BONE",
                     "table": c6_base(upperarm_l=(0, 0, -7), neck_01=(0, 0, 30))}],
           "★★ 交付物 v2：c6 + uL yaw42 + neck_01 yaw30"),
}

# ⚠️ `ue_remote.py` 会给 UE 侧每一行加 `[Info] ` / `[Warning] ` 前缀，
#    而且 UE 日志本身会把行首缩进吃掉 ⇒ 必须**先剥前缀**，再用 `^\s*` 匹配。
PREFIX = re.compile(r"^\[(?:Info|Warning|Error|Verbose|Display)\]\s?")
ROW = re.compile(r"^\s*(\S+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)")
ANIM = re.compile(r"^#{4,}\s+([A-Za-z0-9_]+)（")


def pick_out_dir(tag):
    """选一个**磁盘上不存在**的输出目录。

    `ik_11` 拒绝写入非空目录（在编辑器里删 AnimSequence 会崩），
    而「在编辑器开着的时候删内容目录」也有风险 ⇒ 最省事的办法是**换名**。
    崩溃/中断留下的半成品目录因此不会挡住下一轮。
    """
    base = "/Game/Character/Darius/Anims_TP_" + tag
    disk = ROOT + "/Content" + base[len("/Game"):]
    if not os.path.exists(disk):
        return base
    for i in range(2, 40):
        cand = base + str(i)
        if not os.path.exists(ROOT + "/Content" + cand[len("/Game"):]):
            return cand
    raise SystemExit("!! %s 的候选目录全被占用" % tag)


def write_cfg(tag, restore, jobs):
    out_dir = pick_out_dir(tag)
    # `FIX_TWIST` 不是对齐作业，而是「跑 ik_53 修 twist」的开关 —— 从 align_jobs 里摘出去
    twist = None
    align = []
    for j in jobs:
        if str(j.get("method", "")).upper() == "FIX_TWIST":
            twist = {"convention": j.get("convention", "self"),
                     "apply": True,
                     "frame": int(j.get("frame", 0)),
                     # ⚠️ 必须指向**当前姿势已经导出的那一批**（ik36 = t3），
                     #    不能指向本轮的新目录 —— 它还没建出来（ik_47 踩过这个坑）。
                     "anim_dir": j.get("anim_dir", IK36_ANIM_DIR)}
            if j.get("jobs"):
                twist["jobs"] = j["jobs"]
        else:
            align.append(j)
    cfg = {
        "out_dir": out_dir,
        "pose_anim_dir": "/Game/Character/Darius/Anims_TP",
        "restore": {"mode": restore},
        "align_jobs": align,
    }
    if twist:
        cfg["twist"] = twist
    with open(CFG, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)
    return out_dir, bool(twist)


def clear_dialog(log):
    """每轮开始前清掉可能挡住游戏线程的模态框（典型：崩溃后的 `Restore Packages`）。

    🔴 2026-09-19 实测：UE 崩溃后重启会弹一个 **Slate 模态框**，它阻塞游戏线程，
    于是 Remote Execution（走游戏线程）**完全无响应** —— 现象和「编辑器没起来」
    一模一样（进程在、内存在涨、日志停在 Engine init），极易误判。
    """
    try:
        p = subprocess.run(["uv", "run", "--no-project", "python",
                            ROOT + "/Scripts/editor_dialog.py", "--auto"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=90)
        out = (p.stdout or "") + (p.stderr or "")
    except Exception as ex:
        out = "!! editor_dialog 失败: %s" % ex
    log.write("\n[modal] %s\n" % out.strip().replace("\n", " | "))
    log.flush()
    return out


def gateway_alive():
    try:
        p = subprocess.run(["uv", "run", "--no-project", "python"] + GW +
                           [ROOT + "/Saved/_probe_editor_ready.py"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
        return "PROBE_RESULT" in ((p.stdout or "") + (p.stderr or ""))
    except Exception:
        return False


def run_script(script, log):
    """经网关跑一个 UE 侧脚本，返回 (输出文本, 秒)。"""
    t0 = time.time()
    cmd = ["uv", "run", "--no-project", "python"] + GW + [ROOT + "/Scripts/" + script]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900)
        out = (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        out = "!! TIMEOUT %s" % script
    dt = time.time() - t0
    log.write("\n\n========== %s  (%.1fs) ==========\n" % (script, dt))
    log.write(out)
    log.flush()
    return out, dt


def parse_ik37(out):
    """把 ik_37 的输出解析成 {段: (均值, 最大)}。"""
    res, cur = {}, None
    for raw in out.splitlines():
        ln = PREFIX.sub("", raw)
        ma = ANIM.match(ln)
        if ma:
            cur = ma.group(1)
            res.setdefault(cur, {})
            continue
        r = ROW.match(ln)
        if r and cur:
            res[cur][r.group(1)] = (float(r.group(2)), float(r.group(3)))
    return res


def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    want = sys.argv[1:] or ["e2", "e3", "h2"]
    stamp = time.strftime("%Y%m%d-%H%M%S")
    log_path = "%s/cycle-%s.log" % (LOG_DIR, stamp)
    summary = {}

    with open(log_path, "w", encoding="utf-8") as log:
        log.write("实验组：%s\n日志：%s\n" % (want, log_path))
        for tag in want:
            if tag not in EXPS:
                log.write("!! 未知实验 %r\n" % tag)
                continue
            restore, jobs, note = EXPS[tag]
            out_dir, has_twist = write_cfg(tag, restore, jobs)
            log.write("\n\n############ %s  %s\n   out_dir = %s\n" % (tag, note, out_dir))
            clear_dialog(log)
            if not gateway_alive():
                print("!! 网关不通，中止于 %s" % tag)
                log.write("!! 网关不通，中止本轮（编辑器可能崩了或还卡在模态框）\n")
                break

            run_script("ik_48_restore_pose.py", log)
            run_script("ik_43_align_probe.py", log)
            if has_twist:
                run_script("ik_53_fix_twist.py", log)
            out, _ = run_script("ik_11_batch_retarget.py", log)
            if "非空" in out:
                log.write("!! %s 输出目录非空，跳过\n" % tag)
                continue
            out, _ = run_script("ik_37_verify_orientation.py", log)
            summary[tag] = parse_ik37(out)

        # ---------------------------------------------------------- 汇总
        log.write("\n\n\n################ 汇总（ik_37：均值 / 最大，度）\n")
        order = ["大腿L", "小腿L", "大腿R", "小腿R", "大臂L", "小臂L", "大臂R", "小臂R",
                 "锁骨L", "锁骨R", "躯干", "颈", "头",
                 "膝面L", "膝面R", "肘面L", "肘面R", "颈面",
                 "脚L", "脚R", "手L", "手R"]
        head = "%-8s" % "段"
        for tag in summary:
            head += " | %-16s" % tag
        log.write(head + "\n")
        for seg in order:
            line = "%-8s" % seg
            for tag in summary:
                d = summary[tag].get("idle1", {}).get(seg)
                line += " | %-16s" % ("%6.2f /%6.2f" % d if d else "  <无>")
            log.write(line + "\n")
        # 超门限计数
        log.write("\n超门限段数（均值>8 或 最大>35）：\n")
        for tag in summary:
            bad = [s for s, (m, x) in summary[tag].get("idle1", {}).items()
                   if m > 8.0 or x > 35.0]
            log.write("   %-6s %d 段：%s\n" % (tag, len(bad), ", ".join(bad) if bad else "全过 ✅"))
        log.write("\n日志：%s\n" % log_path)

    # 终端也回显一遍汇总
    with open(log_path, encoding="utf-8") as fh:
        txt = fh.read()
    print(txt[txt.index("################ 汇总"):] if "################ 汇总" in txt else txt[-4000:])
    print("\n[log] %s" % log_path)


if __name__ == "__main__":
    main()
