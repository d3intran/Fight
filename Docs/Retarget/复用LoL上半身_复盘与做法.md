# 复用 LoL 上半身 —— 复盘与做法

> 2026-09-21 · 回答两个问题：① 之前到底为什么失败？② 现在能不能重新拿 LoL 原版静止 pose 的上半身？
> **前置更正**：`Docs/Retarget/HANDOFF.md`（09-19 12:50）已经过时 —— 它写的是「下一步待确认」，
> 而实际路线后来换成了**手动 IK 标定 + 分层合并**。本文件按已核实的证据重写这条时间线。

---

## 0. 结论

| 问题 | 答案 |
| :--- | :--- |
| **失败是因为 IK Rig / IK Retargeter 弄不好吗？** | **不是。** 那套资产建好了、批量重定向也跑通了。真正漏掉的是自家计划里的 **M1-③ Retarget Pose 标定**，而这一步**不报错**。 |
| **现在能重新拿 LoL 原版静止 pose 的上半身吗？** | **能，而且比当初容易得多** —— 只要上半身的话，当初最难的几块（腿/脚/脚趾链尾、髋宽 −22%、骨盆朝向）**全都不在范围内**。 |
| **需要动现有已验收的资产吗？** | **不需要。** 分层合并只换 `spine_01` 子树，下半身沿用当前已验收的那份。 |
| **武器要重调吗？** | 要。但保留 `Weapon` 骨之后可以变成**数据驱动**的正确握法，不用再靠 FK 反解「跟手」。 |

---

## 1. 时间线（已核实）

| 时间 | 事件 | 证据 |
| :--- | :--- | :--- |
| 09-18 18:44 ~ 21:39 | LOL → TP 重定向计划与尝试，产物不可用 | `Docs/Retarget/*.html` |
| 09-18 22:00 ~ | UE 侧自动化重定向：`IK_LOL_Source`(9 链) + `IK_Darius_Target`(29 链) + `RTG_LOL_to_Darius`(5 op，9/9 配对) | `Content/Character/Darius/Retarget/` |
| **09-19 00:55** | **定位到真因**：Retarget Pose 标定被跳过；`hand_l` / `foot_l` 是**链尾骨**，`Direction` 方法定不出方向 ⇒ 偏移留 0 | `Docs/Retarget/Retarget_Pose_Guide.md` |
| 09-19 12:50 | HANDOFF 记「交叉腿是重定向层引入、源干净」，结论是「下一步待确认再执行」 | `Docs/Retarget/HANDOFF.md §3.5` |
| **09-20 13:46** | **手动 IK 标定完成**：`IK_Mixamo` + `IK_Darius` + `RTG_Darius`（Mixamo → Darius） | `Content/Character/Darius/IK/` |
| 09-20 15:40 / 16:25 | 分层合并上线：`A_Darius_AxeWalk_Layered` / `A_Darius_AxeIdle_Layered` | `Docs/Locomotion/AxeWalk_Layered_Merge.md` |

**「手动做的」这个判断的证据**：`Content/Character/Darius/IK/` 那套资产在 `Scripts/` 里**零引用**；
而旧的那套（`Retarget/RTG_LOL_to_Darius`）的脚本**全部躺在 `Scripts/archive/retarget/`** 里。
⇒ 旧路线已归档，新路线是在编辑器里手工建的。

---

## 2. 之前到底失败在哪（一句话版）

> **不是 IK Rig / Retargeter 配不出来，是 `Retarget Pose` 标定这一步被跳过了。
> 而这一步不报错 —— 重定向照跑、帧数照对、平移比值 1.00、缩放 100，当时所有验收全过，只有「朝向」是错的。**

机理（`Retarget_Pose_Guide.md §1` 实测）：

`hand` / `foot` 是**链尾、没有子骨**，而自动对齐的 `Direction`（= `CHAIN_TO_CHAIN`）原理是
**用链里子骨的方向定义本骨朝向** ⇒ 链尾骨定不出方向 ⇒ 偏移**留 0**。

| 骨 | 标定前偏移 | `auto_align_all_bones(Direction)` 之后 |
| :--- | ---: | :--- |
| `upperarm_l` | ≈68° | 几乎没变 |
| `thigh_l` | ≈72° | 明显变了 |
| **`hand_l`** | **0°** | **仍然是 0°** ← 关键 |
| **`foot_l`** | **0°** | **仍然是 0°** ← 关键 |

而两套骨架本来的手/脚局部轴就差很多（**前臂 39° / 锁骨 43° / 骨盆-胯 41°**）。
偏移留 0 等于「假装它们一样」⇒ 手腕脚踝被拧成麻花。

**最该记住的一条**：`AGENTS.md §0.1` 写了「相信数据」，但当时把「数据」窄化成了**位置**。
所有既有验收（骨名对上 / 帧数相等 / 平移比值 / 缩放）**全都量不到朝向**。
⇒ **「几何位置对了」≠「姿势对了」。**

### 2.1 另外三个加剧「扭曲感」的结构性问题（重定向器解决不了）

| # | 问题 | 后果 |
| :--- | :--- | :--- |
| 1 | 源 IK Rig **9 条链** vs 目标 **29 条** ⇒ 20 条目标链没有源对应 | 十根手指 + 脚趾**完全没被驱动**，僵在 rest |
| 2 | 24 根 twist 骨 + ~150 根面部骨 + 4 根 `camera_*` 既不在链里、也没进 Excluded Bones | 可能不可预测抖动 |
| 3 | 源 `Spine1→Spine2`（**2 节**）vs 目标 `spine_01→spine_03`（**3 节**） | 躯干引入额外偏差 |

### 2.2 顺带纠正一条不可靠的旧结论

`HANDOFF §3.5` 提出「髋轴方向相差约 **137°**」。这条**与同一段的实测互相矛盾** ——
同段写着「源与产物的大腿方向几乎完全一致（2D 分量 −0.879/0.477 vs −0.876/0.482，即 0.01°）」。
大腿是骨盆的子骨，**骨盆转 137° 而子骨方向不变，几何上不可能**。
⇒ 那个 137° 大概率是**参考系不一致**造成的测量假象（同类坑在 `AxeWalk_Layered_Merge.md §9.1` 才被发现：
`CharacterMesh0.relative_rotation.yaw = -90`，量左右次序必须用**锁骨线自校准**）。

**可靠的观测只剩一条**：`脚 次序差` 在 **65/65 帧全部为负**（左脚踏到右侧约 17cm）⇒ 腿确实交叉。
但它的**成因**至今没有被验证过，别再拿 137° 当结论用。

---

## 3. 为什么「只做上半身」比当初容易得多

| 维度 | 当初（全身） | 现在（只上半身） |
| :--- | :--- | :--- |
| 链数 | 源 9 / 目标 29 | **约 13 条**（含 `Weapon`） |
| **链尾骨（最难的一块）** | `hand_l/r` + **`foot_l/r`** + 脚趾 | **只剩 `hand_l/r`** |
| 比例问题 | 髋宽 −22%、腿长投影差 22cm、脚浮空 15cm、站姿 71~119cm | **完全不涉及** |
| 骨盆/根骨朝向 | 交叉腿 65/65 帧 + 争议的 137° | **分层合并直接丢掉源的 `pelvis`** |
| twist 骨 | 24 根 | 只涉及 `upperarm_twist_*` / `lowerarm_twist_*` 12 根（仍不驱动） |
| 手指 3 节 | 全部 | 仍是问题，但攻击里可用 Control Rig 补「握拳」 |

**关键**：当初最花时间、最后仍没解决的东西（腿、脚、脚趾、髋宽、骨盆朝向）
**一个都不在「上半身」范围内**。而分层合并**从不搬源的 `pelvis`** ⇒ 骨盆级错误被直接丢弃。

---

## 4. 必须显式处理的三件事

### 4.1 `hand_l` / `hand_r` 是链尾 —— 必须手动对齐

照 `Retarget_Pose_Guide.md §3` 走：`Auto Align → Align All Bones`（Direction）拿到大面，
然后**单独**对 `hand_l` / `hand_r` 做 `Align Selected`，方法依次试 **Mesh → Local Rotation Axes → Global Rotation Axes**，
不理想就**在视口里手转**，最后 `Set Current Pose as Retarget Pose`。

这是攻击里**最要紧的骨**（握斧），值得单独花时间。

### 4.2 `Spine1/Spine2` → `spine_01/02/03` 的 2→3 分配要**显式决定**

不要让自动去猜。建议先定一个明确规则再试，例如：

```
Spine1  → spine_01（各半）
Spine1  → spine_02
Spine2  → spine_03
```

或用 FK Chain 的 `translation_mode: None` + 只搬旋转、把 2 节的旋转按比例摊到 3 节。
**规则要写进脚本常量**，不要每次重跑随机。

### 4.3 `Weapon` 骨 —— 被 `plan_10_src_clean.py` 删了

源骨架真实层级是 `Axe_Head ← Weapon ← R_Hand`（斧头是右手的子骨），
而 `plan_10_src_clean.py` 明确把 `Weapon` / `Axe_Head` / `SnapWeapon` 剔了（净化后 60 骨）。

⇒ 要拿到真实握法，得**重导一份保留武器骨的源骨架变体**（不动现有那份）。

---

## 5. 武器：保留 `Weapon` 骨之后的做法

`Docs/Attack/普通攻击设计建议.md §3` 的路线 A 在这里落地：

1. 源骨架变体保留 `Weapon` / `Axe_Handle` / `Axe_Jaw`。
2. 重定向把 `Weapon` 的世界变换带到目标的 **`weapon_jnt`**（骨架自带的武器锚点）。
3. **斧头几何从 `hand_rSocket` 改挂到 `weapon_jnt`**（改一次 `BP_DariusCharacter`）。
   - `relative_scale` 仍须 **0.01**（抵消最外层 100×），这条红线不变。
4. 左手：斧头网格加 `Grip_Upper` / `Grip_Lower` 两个 socket，Control Rig 用 Two-Bone IK 把 `hand_l` 拉上去，
   用 float 曲线 `GripWeight` 控制权重。
   - ⚠️ **曲线不能全程 = 1**：LoL 的左手是「挥击时才握上」的（attack1 左手到斧柄轴线 f0 26.7cm → 挥击瞬间 150cm 脱开 → 收招 4.7cm）。

**为什么这样比现在好**：现在 `weapon_jnt` 是**FK 反解「跟手」**（把右手的世界变换反解成局部键），
它只能复现「斧头刚性挂在右手上」；而 LoL 里斧头相对右手**逐帧在动**（`Weapon` 被 K 帧，走 `SnapWeapon`/`SnapWeapon2Hand` 换握法）：

| clip | `Axe_Head` 在 `R_Hand` 局部系的偏移模长 |
| :--- | ---: |
| `idle1` | 恒定 **73.7 cm** |
| `attack1` | **83 → 128 → 84 cm** |
| `attack2` | 131 → 71 → 83 cm |

⇒ 保留 `Weapon` 骨 = **把换握法这件事变成数据**，而不是靠手调 socket 猜。

---

## 6. ⚠️ 风格提醒：LoL 的 idle 是「后仰」的

LoL 源 `idle1` f0（本轮从 GLB 实测，用髋轴定参考系）：

| 段 | 离竖直 | 方向 |
| :--- | ---: | :--- |
| `Spine1` | 9.4° | **90% 向后** |
| `Spine2` | 10.6° | **99% 向后** |
| `Neck` | 24.9° | **89% 向后** |

对照 `Retarget_Pose_Guide.md` / `AxeWalk_Layered_Merge.md §8.3` 记的重定向产物：
`spine_01` 8.1° 向后、`neck_01` 25.3° 向后 —— **角度和源几乎一模一样（8.1↔9.4、25.3↔24.9）**。

⇒ **「歪」不是重定向引入的，LoL 的 idle 本来就是后仰驼背剪影** —— 这是给**俯视角**读轮廓用的姿势
（`FOUNDATIONS.md §2.3` 已经写过这条）。搬到第三人称过肩机位，它**天然就是后仰的**。

**建议**：做 A/B（现 Mixamo 待机 vs LoL 待机上半身），谁在过肩机位读得顺用谁。
但**攻击必须用 LoL**（没有别的资产有「德莱厄斯挥巨斧」），风格一致性倾向于也把 idle 换成 LoL —— 值得先量一次再定。

---

## 7. 建议顺序与门禁

> ⚠️ **2026-09-21 修订**：本节下面的第 1~2 步走的是 **UE IK Retargeter 手工标定**那条路。
> 但 `hand` / `foot` 是**链尾骨**，恰恰是 UE 的 `Direction` / `CHAIN_TO_CHAIN` 从原理上处理不了的
> —— 这正是上次翻车的点。**推荐路线已改为「离线世界空间传递」**（链尾骨天然正确、全脚本、可回归）。
> 最新路线见 `Docs/Attack/普通攻击_实施路线.md`；下面的门禁指标仍然有效，继续沿用。

| 步 | 内容 | 门禁 |
| :--- | :--- | :--- |
| **1** | 重导**保留武器骨**的 LoL 源骨架变体（不动现有那份） | 骨数 = 60 + 4（`Weapon` / `Axe_Handle` / `Axe_Jaw` / `SnapWeapon`）；`Weapon` 的父级 = `R_Hand` |
| **2** | 手工建 `IK_LOL_U`（源）+ 复用 `IK_Darius`（目标）+ `RTG_LOL_to_Darius_U`；链 = `Pelvis→Spine1` 父链 · `Spine1` · `Spine2` · `Neck` · `Head` · `Clavicle/Shoulder/Elbow/Hand` ×2 · `Weapon` | `ik_37` 朝向验收：**均值 < 8° / P90 < 20° / max < 35°**（G1）；**`idle1` 与 `attack1` 必须同时报** |
| **3** | 批量重定向 `idle1` / `attack1` / `attack2` / `attack1_toidle` / `attack2_toidle` | 帧数与源**逐一相等**：66 / 74 / 70 / 59 / 37 |
| **4** | 分层合并（沿用 `axw_10_merge.py` 结构）<br>idle：上半身 ← LoL idle，下半身 ← 当前已验收资产<br>attack：上半身 ← LoL attack，下半身按 `Docs/Attack/普通攻击设计建议.md §坑3` 方案① | 上半身 vs 源 **0.000°**；下半身 vs 设计值 **0.0000 cm**；`weapon_jnt` ↔ `Weapon` 世界变换 **≤ 0.1 cm** |
| **5** | 斧头几何改挂 `weapon_jnt` + 左手 IK + `GripWeight` 曲线 | 斧刃到右手距离逐帧 **≤ 0.1 cm**；左手到斧柄轴线 **≤ 3 cm** |

⚠️ **改过 retarget pose，之前导出的动画全部作废**（导出的是快照）⇒ 第 2 步定稿后必须重跑批量重定向。

---

## 8. 需要标注为过时的文档

| 文档 | 问题 | 处理 |
| :--- | :--- | :--- |
| `Docs/Retarget/HANDOFF.md` | 停在 09-19 12:50 的「下一步待确认」；实际路线已换成手动标定 + 分层合并 | 已在文件头加指向本文件的横幅 |
| `AGENTS.md §0.1` | 「已达成」只写了移动/机位/布料，没写动画侧的真正解法（Mixamo 上半身 + 分层合并） | 建议补一行（未改） |
| `AGENTS.md §3` | `retarget/` 目录标了 `ik_36` / `ik_37` / `ik_60` 为现役，但它们服务的 `RTG_LOL_to_Darius` 已归档 | 建议改标（未改） |
