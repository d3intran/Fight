# 会话交接 —— LOL → 2XKO 握斧行走

> 更新时间：2026-09-19 11:05 GMT+8
> **本文件是临时进度快照。任务走完请删除或归档。**
> 配套阅读：
> - `Docs/Retarget/FOUNDATIONS.md` —— UE 5.8 / LOL 资产 / 我们模型三方面的特性，与收窄后的 M1' 计划
> - `Docs/Retarget/Retarget_Pose_Guide.md` —— **本次卡点的成因、手动流程、参考来源**（新会话先读这个）
> - `AGENTS.md` §3.6 / §3.7 —— 本轮踩过的全部坑

---

## 0. 一句话现状

**「手脚七歪八扭」的主因不是重定向 —— 是关卡角色挂着一个骨架不兼容的 AnimBP，
一直在显示参考姿势（A-pose）。已修。**

分三条说清楚，别再混：

1. **★ 主因（已修，已复核）**：`CharacterMesh0.anim_class` 是 **`ABP_Unarmed`**，
   而它的 `target_skeleton` 是 `SK_Mannequin`（UE 默认小白人），与
   `SK_Darius_GodKing_Skeleton` **完全不同** ⇒ UE 拒绝求值 ⇒ 网格停在 **ref pose**。
   渲染图 `Saved/Shots/AnimCheck/png/idle1_f00_front.png` 就是那个 A-pose：
   手臂横向张开、手掌朝外 —— 与用户描述逐字对应。
   修法：`Scripts/anim_48_set_animclass.py` 把蓝图模板与关卡实例都改成
   **`ABP_Darius_Test`**（它的 target_skeleton 正是 Darius 骨架），compile + save + 读回复核通过。
2. **Retarget Pose 的现状（数字）**：最好的姿势是 **`ik_36`（= `CHAIN_TO_CHAIN` 全量对齐）**，
   13 段里 **腿 4 段已到 0.01°~5.8°（完美）**，剩 **9 段上半身超门限**
   （小臂L 56.4 / 锁骨R 66.9 / 锁骨L 49.2 / 颈 39.9 / 头 62.7 / 躯干 21.9 / 大臂R 16.9 / 小臂R 17.8 / 大臂L 9.5）。
3. **交付物状态**：**`Anims_TP_tw_feet/`** 6 个资产 = **目前最好的产物**
   （ik36 姿势 + 脚部 twist 修正 + 根骨 scale 已修 + 骨架一致 + 动画在动）。
   **这是唯一能直接拿去 Persona 看的完整产物。**（`Anims_TP_t3/` 是它的上一版：没修 twist。）

---

## 1. 当前资产状态

| 资产 | 路径 | 状态 |
|---|---|---|
| 源骨架 + 网格 + **46 源动画** | `/Game/Character/Darius/LOL_Source/` | ✅ 48 个，已落盘 |
| `IK_LOL_Source` / `IK_Darius_Target` / `RTG_LOL_to_Darius` | `/Game/Character/Darius/Retarget/` | ✅ 链已映射；retarget root：源=`Root`、目标=**`root`** |
| **`Anims_TP_tw_feet/`** | `/Game/Character/Darius/Anims_TP_tw_feet/` | ✅ **★ 目前最好的产物**（见 §2.5） |
| `Anims_TP_t3/` | 同上 | ✅ 上一版（ik36 姿势 + 已修 scale，**未修 twist**） |
| `Anims_TP/` | 同上 | ⚠️ **已过时**（标定前导出，且未修 scale） |
| 实验产物 20+ 个目录 | `Anims_TP_{z0,z02,e1..e4,h1,h2,c1,m1,g1,t1,t2,t3,cr,cp,cy,tw_*}/` | 供对照；**选定赢家后可清** |
| `ABP_Darius_Test` | `/Game/Character/Darius/Blueprints/` | ✅ **已挂到 `CharacterMesh0`**（本轮的修复） |
| 渲染检查图 | `Saved/Shots/AnimCheck/`、`Saved/Shots/PoseRender/`（EXR）+ `png/` | 见 §3 |

---

## 2. 🔴 本轮核心发现（2026-09-19 第二轮）

### 2.0 ★ 主因：AnimBP 骨架不兼容 ⇒ 一直显示参考姿势

见 §0 第 1 条。**证据链**：
`anim_47_abp_audit.py` 读出 `ABP_Unarmed.target_skeleton = /Game/Characters/Mannequins/Meshes/SK_Mannequin`，
`SK_Darius_GodKing.skeleton = /Game/Character/Darius/SK_Darius_GodKing_Skeleton`；
渲染图与用户描述逐字吻合。

⇒ **`HANDOFF §4` 第 2 步的问题（「手臂张开」是动画还是参考姿势）答案：是参考姿势。**

### 2.1 判定实验：逐骨写偏移**有效**，`auto_align_all_bones` 会**整体覆盖**

`Scripts/exp_cycle.py` 跑出的判定批次（日志 `Saved/exp_logs/cycle-20260919-015856.log`）：

| 段 | `z0` 纯零基线 | `t1` 只把大腿绕 Z 拧 90° | `t3` 用 `SET_BONE` 写回 ik36 表 | `t2` 写完再跑 CHAIN |
| :--- | ---: | ---: | ---: | ---: |
| 大腿L | 49.05 | **137.63** | **0.01** | 0.01 |
| 大腿R | 54.17 | **120.25** | **0.01** | 0.01 |
| 小臂L | 51.61 | 51.61 | 56.44 | 56.45 |
| 锁骨L | 28.54 | 28.54 | 49.18 | 49.16 |

- `z0` 与「标定前」的数字**逐位相同** ⇒ 归零有效、判据可复现。
- `t1` 把大腿L 从 49 推到 138 ⇒ **`set_rotation_offset_for_retarget_pose_bone` 确实有效**。
- `t3` 复现 ik36 基线 ⇒ **读/写是同一套约定**。
- `t2` ≡ `t3` ⇒ **`auto_align_all_bones` 会整体覆盖**，先写后对齐等于没写。

⇒ **正确顺序：先 `auto_align_all_bones` 定大面，再逐骨修。**

### 2.2 ⚠️ `dir(父→子)` 对「绕骨轴自转」**天生免疫** —— 判据有盲区

`t3` 与 `e4` 的 `thigh_l` 偏移差 **30°**（`(9.07,4.02,-47.79)` vs `(-6.39,-4.64,-71.97)`），
两者 `ik_37` 却都是 `0.01°`。离线算 `q2⁻¹·q1` 的轴是 `(-0.512,-0.304,0.803)` —— 不是 `(±1,0,0)`，
因为偏移作用在父骨/世界系里，骨轴在该系里就是个一般方向。

**⇒ `ik_37` 看不见 twist，而用户抱怨的正是「手脚拧」。**
**待办：补一个能测 twist 的判据**（用脚/手的次生方向，如 `foot_l→ball_l`、`hand_l→指骨`）。

### 2.3 方法学结论（修正此前写错的推断）

- ❌ **作废**：「逐骨写偏移无效 / `ik_48` 的还原是假象」—— `t1`/`t3` 证明**有效**。
  之前之所以看着「无效」，是因为 `ik_48` 跑完**没重新导出**，`ik_37` 读到的是上一轮旧产物。
  **教训：验收必须跟在「导出之后」，不能只改姿势就量。**
- ❌ **作废**：「`h2` 失败说明写回不可信」—— 真因是 **`auto_align` 把祖先骨（根骨）带歪了**，
  写回腿部子骨救不回来（见 `c1` 实验：CHAIN 之后复位根骨，腿从 0.01° 掉到 28.5°，
  说明 **CHAIN 给根骨写的那个偏移是腿能对上的关键**）。

### 2.4 其余 Alignment Method 的成绩（全量，`ik_37` idle1 均值）

| 段 | e2 `LOCAL_ROTATION_AXES` | e3 `GLOBAL_ROTATION_AXES` | h2 `MESH`+写回 | **e4 `CHAIN_TO_CHAIN`** |
| :--- | ---: | ---: | ---: | ---: |
| 大腿L | 49.32 | 90.00 | 100.70 | **0.01** |
| 小腿L | 77.47 | 89.40 | 168.06 | **5.77** |
| 大臂L | 85.82 | 88.65 | 48.39 | **9.62** |
| 小臂L | 40.68 | 77.03 | 85.86 | 56.42 |
| 锁骨L | 43.74 | **15.01** | 139.97 | 49.16 |
| 锁骨R | 67.10 | **19.75** | 143.00 | 66.86 |
| 颈 | 67.24 | **13.64** | 140.87 | 39.93 |
| 头 | 60.22 | **14.95** | 108.16 | 62.62 |

- `LOCAL_ROTATION_AXES` **全面劣化，弃**。
- `GLOBAL_ROTATION_AXES` 把**锁骨/颈/头**修到 15° 级（ik36 是 49/40/63），**但腿变 90°、臂全面劣化**
  ⇒ 单用不行，**它是链尾问题的唯一有效线索**，值得继续挖。

---

### 2.5 ★★ twist：判据原来看不见的、**用户真正在抱怨的那一半**

`ik_37` 的主判据 `dir(父→子)` **对「绕骨轴自转」天生免疫**（子骨沿父骨轴偏移，绕该轴转它不动）。
所以「大腿 0.01°、小腿 5.77°」看起来完美，**脚掌其实拧了 66.6°**。

**新加的 twist 判据（`ik_37` 内）**，全部只用关节坐标（符合 AGENTS.md §0.3）：
- `膝面/肘面/颈面` = 关节面法线 `cross(dir(p→m), dir(m→c))`。
  ⚠️ **事后判定：这三个是冗余的** —— 完全由 `dir(父→子)` 决定，不提供新信息。
- **`脚L/R`、`手L/R` = 末梢方向**（`foot_l→ball_l`、`hand_l→middle_01_l`）。
  ✅ **只有这四个是真正独立的 twist 观测量**（垂直于上游骨轴，上游整条链的自转都体现在它身上）。

**基线（ik36，idle1 均值）**：

| 量 | 值 | 读法 |
| :--- | ---: | :--- |
| 膝面L/R | 0.03 / 0.01 | 大腿自转**完美** |
| **脚L / 脚R** | **66.64 / 44.44** | **脚掌绕小腿轴拧了 66°/44°** |
| 手L / 手R | 90.78 / 15.98 | 手（**但见下方存疑**） |
| 肘面L | 80.48 | 大臂自转（冗余量） |

**修法（`ik_53_fix_twist.py`，解析式，不用扫描）**：
1. 在源与目标的产物上各取一帧，算同一根末梢的方向（`大腿L 0.01°` 说明两个组件空间对腿是对齐的）。
2. `Q = rot_diff(d_tgt, d_src)` —— 世界系里需要施加给上游骨的旋转。误差逐帧恒定 ⇒ 一帧算出的 `Q` 对全帧成立。
3. 折进该骨的 offset。`foot_*` / `hand_*` 在 ik36 里 offset 是**单位四元数** ⇒ 干净，不用和旧值相乘。
4. **约定未知**，三种都算（`self`/`parent`/`world`）各跑一轮比数字。

**结果**：

| 量 | 基线 ik36 | `tw_self`（自身系） | `tw_par` | `tw_world` |
| :--- | ---: | ---: | ---: | ---: |
| **脚L** | 66.64 | **5.06** ✅ | 62.00 | 49.50 |
| **脚R** | 44.44 | **15.64** | 15.82 | 77.85 |
| 手L | 90.78 | 146.18 ✗ | 110.99 | 71.18 |

⇒ **约定 = `self`（offset 作用在自身系）**，已确认。
⇒ **`tw_feet`（只修脚）= 干净胜利**：脚L 66.64→**5.06**、脚R 44.44→**15.64**，
   而**其余 13 段逐位不变** —— 印证了「twist 与方向判据正交，可以独立修」。

⚠️ **手部存疑（未决）**：`手L` 基线 90.78°，但任何修正都让它**更差**。
换 `middle_metacarpal_l` 作叶骨也一样差（→138.49）。
怀疑 **`hand_l→middle_01_l` 与 `L_Hand→L_Middle1` 根本不是对应方向**：
2XKO 手腕与手指之间多一根**掌骨**，LOL 没有 ⇒ 基线那 90.78° 可能是**几何不匹配的假象**，
不是真的拧。**在找到正确的手部参考方向之前，不要按这个数字动手。**

### 2.6 ❌ 已被数据否掉的假设：**同一套 `Q` 折法对「方向」不成立**

「用 `Q = rot_diff(d_tgt, d_src)` 折进 offset」这套方法**修脚（twist）成了**，
于是想用它顺手把「颈 / 头 / 锁骨 / 躯干」这 5 段的方向也修掉。**结果被否。**

| 实验 | 颈（基线 39.94） | 头（基线 62.67） | 锁骨R（基线 66.89） | 副作用 |
| :--- | ---: | ---: | ---: | :--- |
| `fx_s03` 约定=self | 29.50 | 44.81 | 50.34 | 大臂L 9.5→**15.9**、小臂L 56.4→**67.7**、大臂R 16.9→**34.4** |
| `fx_s03p` 约定=parent | 29.52 | 44.83 | 50.35 | 同上 |
| `fx_s03w` 约定=world | 47.56 | 59.78 | 67.89 | 小臂L→39.2、手R→9.0（局部变好，但颈/头/锁骨R 变差） |

**三条否证**：
1. `spine_03` 的 `|Q| = 39.89°`，而「颈」只从 39.94 降到 **29.50** —— 本该到 0。
   ⇒ 把 `Q` 折进 offset 用的**参照系**不对，而且**三种候选都不对**。
   （`self` 之所以修脚能成，可能只是因为脚的局部系恰好接近正确参照系 —— 别把它当通法。）
2. `spine_03` 是**整条手臂链的祖先**（`spine_03 → clavicle_* → upperarm_* → …`），
   转它会**连带把已经不错的手臂带歪**（大臂R 16.9→34.4）。这个耦合是真实的，
   要修必须**连同下游一起联立求解**，不能单骨修。
3. `neck_01`（`fx_neck`，`|Q| = 62.84°`）更糟：「头」从 44.81 掉到 **58.25**。

⇒ **结论：方向修正这条线暂时走不通，别再按这个思路硬撑。**
   交付物保持 `Anims_TP_tw_feet`（只含已验证有效的脚部 twist 修正）。

**下一步该试的（换方向，不是继续调这个）**：
- 回到**链**这条根因线：`HANDOFF §5` 第 1 项「给源 IK Rig 补上缺失的链」。
  `auto_align_all_bones(CHAIN_TO_CHAIN)` 靠「链里子骨方向」定朝向，
  而 `spine_03` / `neck_01` / `clavicle_*` 这些骨**所在的链没有源对应**，所以偏移恒为 0。
  把源侧的链补齐，让 auto_align 自己去对齐 —— 这是**根因级**的修法。
  `Scripts/archive/ik_50_api_dump.py` 已写好（已跑过，结论在 §2.7），用来一次问清 controller 到底暴露了哪些链接口。
- 或者：把「正确参照系」用**实测标定**出来 —— 对同一根骨加 3 个正交探针（`+30°` 各绕一轴），
  从观测到的方向变化反解 3×3 映射矩阵，而不是猜 `self`/`parent`/`world`。

---


### 2.7 链的清单与跨度终于查清了（**但「补链」这条路也被否**）

**接口**：`unreal.IKRigController` **完全可用**（此前以为拿不到）：
`get_retarget_chains()` · `add_retarget_chain(name,start,end,goal)` · `remove_retarget_chain(name)`
· `get/set_retarget_chain_start_bone / end_bone / goal` · `get/set_retarget_root`
· `apply_auto_generated_retarget_definition`。
`IKRetargeterController` 侧还有 `get_source_chain(target)` / `set_source_chain(src,tgt)`
/ `auto_map_chains` / `assign_ik_rig_to_all_ops` / `reset_chain_settings_in_all_ops`。

**链数**：目标 `IK_Darius_Target` = **30 条**；源 `IK_LOL_Source` = **10 条**。
差的 **20 条 = 手指 10（Left/Right × Thumb/Index/Middle/Ring/Pinky）+ 掌骨 8 + LeftFoot/RightFoot 2**。

**链的实际跨度（★ 关键，这是「偏移恒为 0」的直接原因）**：

| 侧 | 链 | 跨度 | 后果 |
| :--- | :--- | :--- | :--- |
| 目标 | `Spine` | `spine_01 → spine_03` | **`spine_03` 是链尾** ⇒ 偏移 0 ⇒ 锁骨L/R + 颈 全歪 |
| 目标 | `Neck` | `neck_01 → neck_01` | **单骨链** ⇒ 尾 ⇒ 0 |
| 目标 | `Head` | `Head → Head` | **单骨链** ⇒ 尾 ⇒ 0 |
| 目标 | `LeftClavicle` | `clavicle_l → clavicle_l` | **单骨链** ⇒ 尾 ⇒ 0 |
| 目标 | `LeftArm` | `upperarm_l → hand_l` | 正常多骨 |
| 目标 | **`LeftFoot`** | **`ball_l → ball_l`** | **`foot_l` 根本不在这条链里**；它只在 `LeftLeg`(`thigh_l→foot_l`) 里当**尾** ⇒ 0 ⇒ **脚掌拧 66.6°** |
| 源 | `Spine` | `Spine1 → Spine2` | `Spine2` 是尾 |
| 源 | `LeftLeg` | `L_Hip → L_Foot` | `L_Foot` 是尾 |
| 源 | `Neck` | `Neck → Neck` | 单骨链 |

**试过并被否的两条修法（都已回滚）**：

1. **给源补 `LeftFoot`/`RightFoot` 链并映射**（`ik_55`）：
   加链成功（源 10→12）、`set_source_chain` 返回 True、读回复核通过、三个资产都存了。
   ⇒ 但 `CHAIN_TO_CHAIN` 成绩**毫无变化**（脚L 66.64→65.53、脚R 44.44→54.15）。
   **原因**：目标侧那条 `LeftFoot` 链里**根本没有 `foot_l`**（是 `ball_l→ball_l`），
   所以给它配源链也没用。
2. **把 8 处链跨度拉长**（`ik_56`：`LeftFoot` 改 `foot_l→ball_l`、`Neck` 改 `neck_01→head`、
   `Clavicle` 改 `clavicle_*→upperarm_*`、源 `Neck` 改 `Neck→Head`）：
   8 处**全部改成功并复核通过**，但 `CHAIN_TO_CHAIN` 成绩**没有改善，反而把手臂搞坏**
   （手L 90.77→**127.85**、手R 16.00→**45.82**）。
   **原因**：`clavicle_*→upperarm_*` 与 `LeftArm`(`upperarm_l→hand_l`) **在 `upperarm_l` 上重叠**，
   同一根骨被两条链各对齐一次 ⇒ 冲突。

⇒ **结论：`CHAIN_TO_CHAIN` 并不按「链跨度」工作** —— 拉长链不改变它的结果。
   「链尾 ⇒ 偏移 0」是**观察到的事实**，但**修链不是解法**。
   已全部回滚（API 回滚 `ik_57` + IK Rig **字节级**恢复 `Saved/Backup_ikrig/*.uasset.bak`）。
   回滚后 13 段方向 + 手L/手R/锁骨/颈/头 **逐位回到基线**。

⚠️ **回滚后的残留（已知、可接受，但要知道）**：
`IK_LOL_Source` / `IK_Darius_Target` 已用 `Saved/Backup_ikrig/*.uasset.bak` **字节级**恢复，
但 **脚部 twist 的两个数字没有完全回到原位**：

| 量 | 原始基线 | 回滚后 | 差 |
| :--- | ---: | ---: | ---: |
| 脚L | 66.64 | 65.53 | −1.1 |
| 脚R | 44.44 | **54.15** | **+9.7** |

其余 **21 个量（13 段方向 + 膝面/肘面/颈面 + 手L/手R）全部逐位回到基线**。
⇒ 残留只可能在 **`RTG_LOL_to_Darius.uasset`**（它在实验中被反复存盘，体积 45325 → 27366 字节）。
若要彻底还原，可关掉编辑器后用 `Saved/Backup_retarget_pose/RTG_after_ik36.uasset` 覆盖它。
**这不影响交付物**（`Anims_TP_tw_feet` 是早先导出的，与当前 IK Rig 状态无关），
且 `ik_53` 是「按当前误差算修正量」的自校正方法，换基线只会得到等价的修正。
**但下一个会话跑 `e4` 对照时，请以「65.53 / 54.15」为基线，别拿旧的 66.64 / 44.44。**

**下一步（第三次换方向）**：
- **实测标定参照系**：对同一根骨加 3 个正交探针（各 `+30°` 绕一轴），
  从观测到的方向变化反解 3×3 映射矩阵 —— 不再猜 `self`/`parent`/`world`。
  这是目前唯一还没试过、且**可控**的路子（`ik_53` 的 5 元组作业格式已经支持）。
- 或者接受现状：把已确认有效的部分（脚部 twist）作为交付，上半身 5 段留给后续单独攻坚。

---

### 2.8 ★★ 参照系**实测标定**成功 —— 一个参数修好 4 段

「猜约定」连错三次（§2.6）之后改成**实测标定**：对同一根骨加 3 个正交探针（各 `+30°` 绕一轴），
直接看受它控制的段怎么变。

**`spine_03`（控制「颈 + 锁骨L/R」）的三探针（基线 = `SET_BONE` 写 ik36 表）：**

| 量 | 基线 | +30 roll | +30 pitch | **+30 yaw** |
| :--- | ---: | ---: | ---: | ---: |
| **颈** | 39.93 | 39.65 | 39.97 | **14.84** |
| **锁骨L** | 49.16 | 57.96 | 51.25 | **19.49** |
| **锁骨R** | 66.89 | 65.88 | 62.99 | **38.20** |
| **头** | 62.64 | 59.43 | 64.34 | **35.40** |
| 大臂R | 16.92 | 33.96 | **5.63** | 10.77 |
| 躯干 | 21.85 | 21.85 | 21.85 | 21.85（**不受影响** ✓） |

⇒ **`spine_03` 的 yaw 就是那个有效方向**（roll/pitch 都几乎无效甚至有害）。

**yaw 扫描：**

| 量 | 基线 | +30 | **+45** | **+48** | +60 | +75 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **锁骨L** | 49.16 | 19.49 | **5.07** ✅ | **2.85** ✅ | 10.75 | 25.49 |
| **锁骨R** | 66.89 | 38.20 | 24.97 | **22.58** | 15.33 | 17.15 |
| **颈** | 39.93 | 14.84 | **14.04** | 15.68 | 24.84 | 38.47 |
| **头** | 62.64 | 35.40 | **23.79** | **21.93** | 17.71 | 22.29 |
| 大臂L | 9.50 | 24.45 | 33.83 | 35.71 | 43.14 | 52.10 |
| 大臂R | 16.92 | 10.77 | 24.57 | 27.33 | 38.32 | 51.95 |
| 小臂R | 17.81 | 9.89 | 23.64 | 26.38 | 37.34 | 50.94 |
| 躯干 | 21.85 | 21.85 | 21.85 | 21.85 | 21.85 | 21.85 |

**结论**：
- **一个参数（`spine_03` yaw ≈ +45~48°）就把 4 段大幅拉好**：
  锁骨L 49.16→**2.85** ✅、锁骨R 66.89→**22.58**、颈 39.93→**14.04**、头 62.64→**21.93**。
  躯干完全不受影响（符合预期 —— 它由 `spine_01` 控制）。
- **代价在手臂**：`spine_03` 是整条手臂链的祖先，转它必然把手臂带歪
  （大臂L 9.50→33.83、大臂R 16.92→24.57）。
  ⇒ **必须同时给手臂做「反向补偿」**（见下）。
- `+30 pitch` 对**右侧**手臂特别好（大臂R 16.92→**5.63**、小臂R 17.81→**5.88**），
  说明手臂的修正方向是 pitch 类 —— 但要和 `spine_03` 的 yaw 分开处理（两回事）。

**下一步（这就是现在该做的）**：
按**层级顺序联立求解**：
1. `spine_03` 用 yaw 修到最优（≈+45~48°）。
2. 它下游的 `upperarm_l/r` 必须**抵消**这次旋转：`O_new = C ⊗ O_old`，
   其中 `C = W_ref(骨)⁻¹ · A⁻¹ · W_ref(骨)`，`A` = `spine_03` 这次施加的旋转。
   （`ik_53` 的 `self` 约定已在脚上验证过，这里是对它的**第二次验证**：
   若补偿后大臂L/R 回到 9.50/16.92，说明约定正确、且「下游补偿」这套机制可用。）
3. 再用同样手法处理 `neck_01`（管「头」）与 `spine_01`（管「躯干」）。

⚠️ **基线要用 `SET_BONE` 写 `ik36` 表，不要用 `CHAIN_TO_CHAIN`**：
实测 `CHAIN_TO_CHAIN` 的输出在本轮实验后**漂了**（脚L 65.53 / 脚R 54.15），
而**显式写 `ik36` 表仍能逐位复现原始基线（脚L 66.64 / 脚R 44.44）**。
⇒ 「已知良好姿势」是那张表，不是 `CHAIN_TO_CHAIN` 的当前输出。

---

### 2.9 ★★★ 层级联立求解**成功**：一次改动把 6 段打到基线以下

承 §2.8。`spine_03` 转 +48° yaw 后手臂被带歪，于是**按层级顺序给下游做反向补偿**。

**第一步：标定手臂的补偿方向**（基线 = ik36 + `spine_03` +48y，再对 `upperarm_l` 各加 +30°）：

| 量 | sy48 | +30 roll | +30 pitch | **+30 yaw** |
| :--- | ---: | ---: | ---: | ---: |
| **大臂L** | 35.71 | 23.05 | 23.71 | **19.76** |
| **小臂L** | 63.28 | 73.90 | 58.54 | **40.85** |
| **手L** | 102.58 | 93.16 | 85.25 | **83.54** |
| 大臂R | 27.33 | 27.33 | 27.33 | 27.33（**不受影响** ✓ 隔离干净） |

⇒ `upperarm_l` 也是 **yaw** 最有效；大臂L 的响应率 ≈ −0.532°/° ⇒ 需 yaw ≈ +49°。

**第二步：施加并对比左右符号**

| 量 | 原始基线 | sy48 | `c1`（双 +49） | **`c2`（左 +49 / 右 −49）** |
| :--- | ---: | ---: | ---: | ---: |
| **锁骨L** | 49.16 | 2.85 | 2.85 | **2.85** ✅ |
| **颈** | 39.93 | 15.68 | 15.68 | **15.68** ✅ |
| **头** | 62.64 | 21.93 | 21.93 | **21.93** ✅ |
| **锁骨R** | 66.89 | 22.58 | 22.58 | **22.58** ✅ |
| **小臂L** | 56.45 | 63.28 | 26.24 | **26.24** ✅ |
| **小臂R** | 17.81 | 26.38 | 46.35 ✗ | **16.79** ✅ |
| **肘面R** | 14.62 | 19.46 | 32.29 ✗ | **2.09** ✅ |
| **手L** | 90.77 | 102.58 | 73.54 | **73.54** ✅ |
| 手R | 16.00 | 57.15 | 82.39 | 34.59 |
| 大臂L | 9.50 | 35.71 | 24.58 | 24.58 |
| 大臂R | 16.92 | 27.33 | 47.31 | **17.85** |
| 躯干 | 21.85 | 21.85 | 21.85 | 21.85（未动，由 `spine_01` 控制） |
| 脚L/脚R | 66.64/44.44 | 同 | 同 | 同（twist 修正未叠加） |

**结论**：
1. **✅ 机制成立**：`spine_03` 用 yaw 修上游 + 双臂 `upperarm_*` 用**镜像符号**的 yaw 补偿下游，
   一次就把 **6 个量打到原始基线以下**（锁骨L 49.16→2.85、锁骨R 66.89→22.58、
   颈 39.93→15.68、头 62.64→21.93、小臂L 56.45→26.24、肘面R 14.62→2.09）。
2. **★ 左右符号相反**：`upperarm_l` 要 **+yaw**、`upperarm_r` 要 **−yaw**（`c1` 同号会把右臂搞坏 47.31）。
3. 超门限段数 **16 → 14**，且多项显著改善 —— 这是**本轮第一个净收益的姿势改动**。
4. 还没做的：`大臂L` 还差（24.58，需再加 yaw）、`lowerarm_*` 尚未补偿、
   `spine_01`（管躯干）与 `neck_01`（管头）未单独优化、脚部 twist 修正未叠加。

**下一步**：
- 继续加 `upperarm_l` yaw（≈再 +30°）把大臂L 拉回；
- 补 `lowerarm_l/r` 的 yaw（管小臂L/手L）；
- 再对 `spine_01` / `neck_01` 各做一轮「3 探针 + 扫描」；
- 最后叠加 `ik_53` 的脚部 twist 修正 → 跑 `ik_11` + `ik_31` 出新交付物。

⚠️ 记录一下**这次能成的关键**：`ik_37` 的**逐段独立观测**（每一段只受一根父骨控制）
+ **单骨单分量扫描**（一次只动一个 rotator 分量）+ **基线用显式 `ik36` 表**。
三者缺一不可 —— 之前三次失败都栽在「一次改太多、分不清是谁的功劳」。

---

## 3. 渲染检查（可用，但要修冻结）

### 3.1 已有的成熟做法
`Scripts/anim_40_render_check.py`（新写）+ 复用 `axe_14_scene_capture_char.py` 的方案：
- 用**裸 `SkeletalMeshActor`**（`BP_DariusCharacter` 挂着 AnimBP，会覆盖 `set_animation`）
- `capture_source = SCS_FINAL_COLOR_LDR`
- 相机 front：`(0, −450, 110) pitch 0 yaw 90`，fov 40；q34：`(−320, −330, 130) pitch −6 yaw 46`

### 3.2 输出是 **EXR**（文件头 `76 2f 31 01`），必须转码
```bash
ffmpeg -y -i <无扩展名文件> \
  -vf "zscale=t=linear,tonemap=hable,zscale=t=bt709:m=bt709:r=tv,format=rgb24" \
  png/<名字>.png
```
（`Saved/Shots/AnimCheck/png/` 下已有 5 张转好的）

### 3.3 🔴 采集会冻结 —— 真因已定位（**不是节流**）

md5 显示 `idle1_f40` == `run_f00` == `run_f09` —— 第 4 张之后**每帧都是同一张**。

**真因（2026-09-19 实测，两条链）**：

1. **编辑器世界根本没在 tick。** `get_game_time_in_seconds` 在 1.2 s 采样里 **Δ = 0.0000**。
   而 `USceneCaptureComponent2D::capture_scene()` 是**延迟执行**的 ——
   它只是置 `bCaptureSceneDeferred`，真正的 `CaptureSceneImpl()` 在
   **`TickComponent`** 里跑。世界不 tick ⇒ 渲染目标内容永不更新 ⇒ 每张图都一样。
   （这也解释了为什么「姿势指纹」逐帧全同、而 `export_render_target` 照常出图。）
2. **崩溃后重启会卡在模态框 `Restore Packages`**（Slate 窗口，类名是 `UnrealWindow`
   **不是** `#32770`）。它阻塞游戏线程 ⇒ Remote Execution **完全无响应**，
   现象与「编辑器没起来」一模一样（进程在、内存在涨、日志停在 Engine init）。
   修：`Scripts/editor_dialog.py --auto`（用 `keybd_event` 发**真实** Esc；
   `PostMessage` 对 Slate 无效）。已接进 `exp_cycle.py` 每轮开头。

**试过但无效**（留档，别再试）：
- `disable_throttling.py` 的 6 个 CVar（`t.IdleWhenNotForeground` 等）—— 对 tick 无影响。
- `editor_focus.py` 恢复/前台化窗口 —— 窗口本来就是 `visible=True iconic=False`。
- `LevelEditorSubsystem.editor_set_viewport_realtime(True, <4 个 key>)` —— **调用成功但 tick 依旧 Δ=0**。
  ⚠️ 注意签名是 `(realtime, viewport_config_key)`，**参数顺序反了会报 bool→Name 转换失败**；
  key 要从 `get_viewport_config_keys()` 取（本机是 `FourPanes2x2.Viewport 1.Viewport0..3`）。
- `editor_invalidate_viewports()`。

**可用的绕行方案**：`Scripts/anim_51_pose_render.py` —— 用
`SubobjectDataSubsystem.add_new_subobject` 给关卡实例动态加一个 `PoseableMeshComponent`，
自己算 FK 后逐骨 `set_bone_transform_by_name`，**绕开动画系统**。
实测写入 310/310 根骨、引擎侧读回逐帧不同 ✅ ——
**但渲染仍是旧的**（因为 `capture_scene()` 同样要等 tick）。
⇒ **渲染这条线在「世界能 tick」之前都是死路**；要么修 tick，要么走 PIE/SIE。

### 3.4 已经看到的东西

`saved/Shots/AnimCheck/png/idle1_f00_front.png`（01:07 那张）：
角色正面朝向相机、腿站立正常，**手臂横向张开、手掌朝外**。
⇒ 结合 §2.0，**这就是参考姿势（A-pose）**，不是动画、也不是重定向错误。

---

## 4. 现在的第一步（按这个顺序）

1. **★ 先看产物**：在 Persona 里打开
   **`/Game/Character/Darius/Anims_TP_tw_feet/A_Darius_idle1`**
   —— 它是「ik36 姿势 + 脚部 twist 修正 + 已修 scale」，骨架一致、动画在动。
   这是判断「还剩多少错」的最快路径。
2. ~~给 `ik_37` 补 twist 判据~~ —— **✅ 已完成（§2.5）**。`脚L/R` 已从 66.6/44.4 压到 **5.1/15.6**。
3. **上半身 5 段（锁骨L/R + 颈 + 躯干 + 头）** —— 控制骨 `spine_01` / `spine_03` / `neck_01`
   在 ik36 里偏移都是 0。⚠️ **「用 `Q` 折 offset」这条解析路已被否（§2.6）**，换下面两条：
   - **首选（根因级）**：给**源 IK Rig 补上缺失的链**，让 `auto_align_all_bones(CHAIN_TO_CHAIN)`
     自己把 `spine_03` / `neck_01` / `clavicle_*` 对齐。接口清单已由 `Scripts/archive/ik_50_api_dump.py` 问清（§2.7）。
     问清链接口（`add_new_subchain` 之类）。
   - **备选**：**实测标定参照系** —— 对同一根骨加 3 个正交探针（各 `+30°` 绕一轴），
     从观测到的方向变化反解 3×3 映射矩阵，而不是猜 `self`/`parent`/`world`。
   ⚠️ 无论走哪条，`spine_03` 是整条手臂链的祖先，**必须连下游一起联立**，
   否则会像 `fx_s03` 那样把大臂R 从 16.9 拖到 34.4。
4. **搞清楚手部的参考方向**（§2.5 末尾的存疑）。在解决之前 `手L` 那个 90.8° 不要当缺陷处理。
5. **每轮实验都用 `Scripts/exp_cycle.py <tag>`**（已封装 还原→对齐→[修twist]→导出→验收，
   自动换新输出目录、自动清模态框、自动检查网关）。
   `ik_53` 会把每轮结果累加进 `Saved/pose_extra.json`，`ik_48` 还原时会带上
   ⇒ **逐骨依次修可以跨轮累积**（想从干净 ik36 重来就删掉这个文件）。
6. 直到 `ik_37` 全段均值 <8° / 最大值 <35°



---

## 5. 未决项

1. ~~**20 条目标链没有源对应**~~ —— **✅ 清单已查清（§2.7）**：目标 **30** 条 / 源 **10** 条，
   差的 20 条 = 手指 10 + 掌骨 8 + `LeftFoot`/`RightFoot` 2。
   手指/脚趾**确实完全没被驱动**，会僵在 rest 姿势（近景显眼）。
   ⚠️ 但**「补链」这条修法已被否**（§2.7）：加链/拉长链都不改变 `CHAIN_TO_CHAIN` 的结果。
   ⇒ 手指要不要驱动，**得另想办法**（例如单独手写偏移，而不是靠链）。
   手指的源骨名：`L_/R_Thumb1-2`、`Index1-2`、`Middle1-2`、`Ring1-2`、`Pinky1-2`；
   目标骨名：`thumb_01-03_l/r`、`index_01-03_l/r`（+`index_metacarpal_l/r`）等。
2. **24 根 twist 骨 + ~150 根面部骨 + 4 根 `camera_*`** 既不在链里也没列入 Excluded Bones
   ⇒ 可能抖动（CSDN 那篇明确建议加 Excluded Bones）。
3. **`Spine` 链 2 骨 vs 3 骨**（源 `Spine1→Spine2`，目标 `spine_01→spine_03`）。
   ⚠️ 这会让 `ik_37` 的「躯干」段变成**苹果比橘子**：源 2 段跨整个腹部，目标 `spine_01→spine_02`
   只跨三分之一。**21.9° 这个数字里有多少是骨数不匹配的假象，未量化。**
4. **源骨架 forward 是 −Y 还是 +Y** —— 至今未敲定（`MEMORY.md` §5.1 有冲突标记）。
   ⚠️ 新线索：`c1` 实验显示 **CHAIN 给根骨写了一个非零偏移**，而复位它腿就从 0.01° 掉到 28.5°
   ⇒ **根骨那个偏移很可能就是在补全局朝向差**。查清它 = 同时解决本项。
5. ~~`CharacterMesh0.anim_class` 仍是 `ABP_Unarmed`~~ —— **✅ 已修，改成 `ABP_Darius_Test`**（§2.0）。
6. **源动作里没有 `walk`** —— 走路只能用 `run` 放慢（速率约 **0.70** ⇒ 1.67 s/循环 ⇒ 1.2 步/s）。
7. **retarget pose 存在 IK Rig 里，不在 Retargeter 里**：
   实测 `IK_Darius_Target.uasset` 时间戳停在 00:04，而 `RTG_*.uasset` 一直在更新
   ⇒ 之前所有 `auto_align_all_bones` **只活在内存里，从没落过盘**。
   已修：`ik_43` / `ik_48` 现在三个资产都存。

8. **手部 twist 的参考方向没找到**（§2.5）：`手L` 基线 90.8°，但任何修正都让它更差。
   怀疑 `hand_l→middle_01_l` 与 `L_Hand→L_Middle1` **不是对应方向**
   （2XKO 手腕与手指之间多一根掌骨）。**在搞清对应关系前，不要按这个数字动手。**
9. **`spine_03` / `neck_01` / `spine_01` 的偏移仍是 0**（不在 ik36 表里）。
   它们是「锁骨L/R + 颈 + 躯干 + 头」这 5 段的控制骨 ⇒ 这 5 段是下一步的主战场。

---

## 6. 里程碑

**M0 尺子 → M1 垂直切片 → M2 全量**

- ✅ M1-① 源骨架净化
- ✅ M1-② 第 1 步 修历史脚本 FBX 导出
- ✅ M1-② 第 2 步 IK Rig ×2 + Retargeter + 批量重定向链路（6 个动作已产出）
- ⏳ **M1-③ Retarget Pose 标定** ← **现在卡在这里**
- ⬜ M1-④ 比例补偿 + 去倾斜 + 步幅闭环
- ⬜ M1-⑤ ABP_Darius 落地

**收窄版 M1'（握斧走路）见 `FOUNDATIONS.md` §6**：6 步约 1.7 天，每步带数字验收。

---

## 7. 工程卫生

- 关卡基线 **7 个 actor**，跑完必须回到这个基线（本轮已用 `anim_41_cleanup.py` 清干净）
- ⚠️ **清理时 `get_name()` 与 `get_actor_label()` 都要匹配**：spawn 出来的 actor
  name 是 `SkeletalMeshActor_0`，label 才是你设的那个
- 临时 UE 资产：`Scripts/plan_99_clean_temp.py`
- **交付物禁止放 `Saved/`**（截图/日志/中转 FBX 可以）
- Python 走 `uv`，JS/TS 走 `deno`
- 编辑器当前由后台任务的 `--hold` 维持（PID 10604）；**停那个任务 = 杀编辑器**，
  关闭请先 `deno task editor:down`

---

## 8. Git 状态

`main` 领先 `origin/main` **6 个提交**（未推送）。本轮改动**均未提交**。

```
37fa789  docs(retarget): 新增会话交接文档 HANDOFF.md + AGENTS.md 顶部加当前任务指针
09fad41  feat(retarget): M1-② 第 2 步 —— UE 侧 IK Rig x2 + IK Retargeter 建成
424ecad  fix(retarget): 修复 4 个重定向脚本的 FBX 导出 bind pose 污染
0198357  feat(retarget): M1-① 源骨架净化完成
```

未提交内容：`AGENTS.md`（§3.6/§3.7 新增坑）、`Docs/Retarget/` 下三份文档、
`Scripts/ik_13~ik_41`、`Scripts/anim_40~41`、`Scripts/editor.deno.ts`、`deno.json`、
以及 `Content/` 下 48 + 6 个 uasset。
`LOL_Source/SK_LOL_Darius*.uasset` 是**重建**的（git 里有旧版可回退）。

---

## 9. 脚本速查

| 脚本 | 作用 |
|---|---|
| `editor.deno.ts` | 编辑器启停（`--hold` 常驻）；`deno task editor:up/down/status` |
| **`editor_dialog.py`** | **★ 清掉挡住游戏线程的模态框**（典型：崩溃后的 `Restore Packages`）。`--auto` 只在有阻挡框时才发 Esc。**每轮 UE 操作前都该跑** |
| `editor_focus.py` | 恢复/前台化编辑器窗口（`ctypes` 直调 user32；PowerShell 的 `Add-Type`/COM 被沙箱挡） |
| **`exp_cycle.py`** | **★ 实验回路驱动器**：写配置 → 还原 → 对齐 → 导出 → 验收，一轮一条命令。自带换目录/清模态框/查网关 |
| `exp_reparse.py` | 从 `Saved/exp_logs/*.log` 重解析 `ik_37` 汇总表（**数据在日志里，不必重跑**） |
| `ik_11_batch_retarget.py` | 批量重定向（自带清目录门禁 + 存盘；`out_dir` 可被配置覆盖） |
| `ik_23_purge_animstp.py` | 清 `Anims_TP`（**必须编辑器刚启动时跑**） |
| `ik_31_fix_root_scale.py` | 删最外层骨假缩放轨道（副本验证 + 双门禁；`out_dir` 可被配置覆盖） |
| `ik_27_optionB_config.py` | retarget root 层级修复 + pelvis 加 FK 链（坑 D） |
| `ik_36_calibrate_retarget_pose.py` | Retarget Pose 标定（auto align + 复位脚 + 贴地） |
| **`ik_37_verify_orientation.py`** | **★ 朝向验收器（G1）**。⚠️ **对 twist 免疫**（§2.2）；内含 `Sampler` 类（**修掉了崩编辑器的 `find_bone_path_to_root` 热点**）。现已加 **twist 判据**（膝面/肘面/颈面 + 脚/手） |
| `ik_43_align_probe.py` | 按配置施加对齐；支持 `CHAIN_TO_CHAIN`/`MESH_TO_MESH`/`LOCAL_ROTATION_AXES`/`GLOBAL_ROTATION_AXES` + **`SET_BONE`**（显式逐骨写）+ `KEEP_IK36` |
| **`ik_55_add_source_chains.py`**（archive/） | 给**源** IK Rig 补链（`IKRigController.add_retarget_chain`）+ `set_source_chain` 接链。⚠️ **效果被否**（§2.7） |
| **`ik_56_fix_chain_spans.py`**（archive/） | 改链的起止骨（`set_retarget_chain_start_bone/end_bone`）。⚠️ **效果被否且把手臂搞坏**（§2.7） |
| **`ik_57_revert_chain_spans.py`**（archive/） | 把 `ik_55`/`ik_56` 的改动**全部回滚**（API 层）。字节级备份在 `Saved/Backup_ikrig/` |
| **`ik_53_fix_twist.py`** | **★ 修 twist**：算 `Q = rot_diff(d_tgt, d_src)` 折进 offset。约定 `self`/`parent`/`world` 三选一，**实测 `self` 正确**。⚠️ 三个坑：变量名 `anim_dir` 与 FK 函数**重名**、`unreal.Vector` 没有 `rotation_difference`、读姿势要指向**当前姿势已导出的那批** |
| `ik_48_restore_pose.py` | 回滚 retarget pose（`zero` / `ik36`），**不重启编辑器** |
| `anim_40_render_check.py` | 渲染动画供肉眼检查（EXR，需转码）；含 `wait_tick()` 等世界推进 |
| **`anim_46_what_plays.py`** | **★ 查角色到底在播什么**（mesh / anim_class / mode / 关卡实例 / 产物骨架一致性） |
| **`anim_47_abp_audit.py`** | **★ AnimBP 与骨架兼容性审计**（只读）——查出「一直显示参考姿势」的那个根因 |
| **`anim_48_set_animclass.py`** | **★ 把 `CharacterMesh0.anim_class` 换成 `ABP_Darius_Test`**（改组件模板 + compile + save + 读回复核） |
| **`anim_51_pose_render.py`** | **★ 不依赖世界 tick 的按帧渲染**：`SubobjectDataSubsystem` 动态加 `PoseableMeshComponent` + 自己算 FK。⚠️ 写姿势**有效**，但 `capture_scene()` 仍要等 tick ⇒ 渲染这条路还没通 |
| `anim_41_cleanup.py` | 渲完清临时 actor，回到 7 个基线 |
| `plan_99_clean_temp.py` | 清 `/Game/Temp*` + 临时 actor（**已补 `PoseRnd_`/`SceneCapture2D_`/`AnimChk_` 前缀**） |
| `disable_throttling.py` | 关视口后台节流（**对本次的 tick 冻结无效**，见 §3.3） |

