# Fight 项目 Agent 核心上下文 (AGENTS.md)

> 接手本项目的 Agent **开工前必读 §0 与 §1**。历史战术快照见 `Docs/` 与 `.workbuddy/memory/`。

---

## 0. 工程全景与当前阶段（2026-09-20 奠基闭环）

### 0.1 已达成的地基里程碑（100% 验收通过）
- **扎实站立与行走**：
  - 待机：`A_Darius_AxeIdle_Layered`（右手握战斧垂立，接地稳固，循环接缝 0.00cm）。
  - 行走：`A_Darius_AxeWalk_Layered`（分层合并，腿-臂对侧摆动相位 185.3°，双手稳固握斧，双脚踏实地面）。
- **3A 战斗过肩机位与动力学手感**：
  - 角色蓝图 `BP_DariusCharacter` 装配具备三阶物理阻尼的 `USpringArmComponent`（视距 380cm，右肩偏移 (0, 45, 20)，中心偏移 (0, 0, 50)，俯角 -12°，Camera Lag 9.0）；
  - 移动起跑时弹簧物理拉伸 **23.8cm**，制动收步柔和回弹，彻底消除纯几何水平“滑板车平移感”。
- **步态速度严格对齐**：
  - `CharacterMovementComponent.MaxWalkSpeed = 220 cm/s`；
  - `BS_Darius_Locomotion` 速度轴上限收窄为 220，满速样本配置 `RateScale = 1.48`，**脚底滑差率降至 0.10%**（严于 25% 验收门槛）。
- **披风布料解算与穿模根治**：
  - DCC 彻底剥离 Section 0（描边壳）内的 1,426 个披风面，消除硬壳穿插；
  - Chaos Cloth Dataflow 节点图修复，**1,313 个流体粒子**在 Section 1 实时解算，肩部 34 个运动学点牢固钉住。
- **关卡环境**：训练场保持干净纯粹的 **7 个基线 Actor**。

### 0.1b M2 阶段：LoL 动画管线打通（2026-09-22）
- **RTG 管线定稿**：`mirror` 配方（源 Root 世界 yaw180 + 26 条左右链交叉映射）
  + FK 腿链 `rotation_mode = ONE_TO_ONE`（原 INTERPOLATED 按链长比例重算旋转，是左右腿
  摆幅不对称 1.44~1.77 的元凶，改后 toe 降到 **1.16**）。46 条动画全量导出
  `Animations/LOL_Retarget/`（`A_LOL_Darius_x` → `A_Darius_x`）。
- **标准流水线（重导后必跑，顺序固定）**：
  `wp_60`（批量重导+删最外层假 scale 轨）→ `wp_50`（武器握法烘焙 43 条）→
  `wp_72`（产物朝向 180° 修正）→ `wp_103`（恒定落地抬升，中位数对齐 10cm）。
- **审计门禁**：`wp_94`（逐帧落地剖面）、`wp_102`（左右腿对称度）。
  ⚠️ **逐帧 root 吸附/骨盆压缩会破坏左右对称**（全局平移牵连两只脚）——贴地问题交给 Foot IK。
- **武器挂点定稿**：锚点 = **`weapon_jnt_l`**（父 `hand_l` = 解剖右手；本骨架 l/r 命名与解剖相反，
  禁止按命名判侧别）。46 条握法烘焙后 `|L_grip(t0)|` 与源 `Weapon↔R_Hand` 距离逐条精确吻合；
  BP `WeaponAxe` 相对变换 `loc=(0,-0.8383,0.1249)`、`rot=单位阵`、`scale=0.01`。
- **接入游戏**：`BS_Darius_Locomotion` 换 LoL 三条（Speed 0/220/440 → idle1/run/run_fast，
  原 Mixamo 版备份 `BS_Darius_Locomotion_M1_Mixamo`）；Shift 走 `IA_Sprint`（IMC 绑 LeftShift）
  切 `MaxWalkSpeed` 220↔440；ABP Idle 状态序列已换 `A_Darius_idle1`。
- **披风碰撞修复**：`SK_Darius_GodKing_Physics` 原本 12 个球全在骨骼原点（长骨两端 8~13cm 无覆盖、
  手臂无 body）⇒ 腿的 4 根长骨换成**沿骨全长胶囊**（`wp_101`，脚本库有）。
- **遗留与下一步（2026-09-22 下午更新）**：
  - ① ~~BP 的 Parent Socket 需手点~~ **已确认用户早已改好并保存在 BP 里**。
    ⚠️ **读 BP 组件属性的坑**：`get_default_object()`（CDO）上的组件在 SCS 改动未重新 Compile 前
    仍是旧值——wp_60/wp_51 读 CDO 打印出 `hand_rSocket` 是**假象**（PIE 用 SCS，实际已是
    `weapon_jnt_l`，`uasset` 字符串与 PIE 斧头位置双重验证）。**读用户改动必须走 SCS 节点**。
  - ② 对称度残余 1.16（源 0.92）待查 IK goal 与源/目标腿骨链长比例；
  - ③ **穿地（run 支撑脚 min -31.7，约 1/4 帧数）必须用 ABP 运行时 Foot IK 解决**。
    ⚠️ **数据侧四条路已全部实测证伪，禁止再试**：逐帧 root 平移（对称 1.16→1.92，全局平移牵连双脚）、
    骨盆压缩（1.22→1.68，左右相位不同）、绕髋刚性旋转（41cm 需 27°+ 打满上限不够）、
    两骨 IK 烘焙（蹬直帧 pole 向量退化，脚被甩到 113cm）。过程与恢复脚本见
    `wp_108_foot_ik_bake.py` / `wp_109_restore_tracks.py`（保留作教训与应急工具）。
    下一步实现要点：查 `ABP_Darius_Test` 里 `AnimGraphNode_ControlRig` 挂的 Rig →
    CR 加 Foot IK 或 ABP 加 `TwoBoneIK`+trace；平地可先不 trace（地面 z=0）；
    验收 = `wp_94`（min ≥ 0）+ `wp_102`（对称不回退）+ PIE 视觉。

### 0.2 下一阶段核心战役（战略跃迁）
**M2 动画管线已通（§0.1b），表现层仅剩 Foot IK 一项收尾（见 §0.1b 遗留③）。完成它之后，全面进入【基于现代 C++ 的核心战斗玩法框架】研发**：
1. **C++ 角色与输入框架**：创建 `AFightCharacter` 与 `AFightPlayerController`，基于 Enhanced Input 建立输入动作与机位控制；
2. **移动与身位派生**：继承 `UCharacterMovementComponent` 实现冲刺（Sprint）、闪避翻滚（Dodge/Roll）与无敌帧；
3. **战斗连招与输入缓冲器**：建立 C++ Input Buffer 预输入窗口、连招派生树、打击检测扫掠（Hitbox Sweep）；
4. **打击反馈与数值系统**：顿帧（Hit Stop）、受击硬直、镜头震动、外圈刮流血层数（Bleed Stacks）与 LOL 音效同步。

---

## 1. 核心铁律（违反 = 返工）

1. **相信数据，禁止主观臆断**：任何改动必须有客观数值测量（滑差率、伸缩量、粒子数、帧率、角度）。
2. **数字必须能证伪结论本身**：严禁报单动作掩盖双动作、严禁拿“链路打通”冒充“质量合格”。
3. **严选成熟轮子**：几何/网格优先使用 DCC (Blender / `bmesh`) 与 Python 科学库；引擎内批处理走 `ue_remote.py`；严禁徒手搓低效算法。
4. **验证必附视觉与客观门禁**：任何阶段宣告完成，必须附带 PIE 运行态探针数据或视口捕获自验截图，关卡 Actor 必须清零复位至 7。

---

## 2. 核心资产与工程契约（严禁破坏）

### 2.1 角色网格与材质契约 (`SK_Darius_GodKing`)
- **309 骨骼**（引擎内 310，含最外层 NULL 根）；主干对齐 UE Mannequin 命名；
- **最外层骨 scale = 100**：导致 `pelvis` 局部平移基线为 **1.0967**；所有挂接 Socket 的 `RelativeScale` 必须设为 **0.01**（正负相消，禁止改动最外层缩放）；**完整契约、常量源与门禁见 §2.4**；
- **7 材质槽**：Slot 0 为反向法线描边壳（整模复制品），披风与斧头几何已从 DCC 彻底剔除；
- **披风布料**：Chaos Cloth Asset `CA_Darius_Cape` 绑定至 Section 1；固定组名必须为纯文本 `SimVertices3D`，权重映射为 `MaxDistance`。

### 2.2 战斧武器契约 (`SM_Darius_GodKing_Axe`)
- **挂接点（2026-09-22 定稿）**：`BP_DariusCharacter` 的 `WeaponAxe` 组件，父 = `CharacterMesh0`，
  Parent Socket = **`weapon_jnt_l`**（父 `hand_l` = 解剖右手）；
  **relative_location = (0, -0.838344, 0.124911)**、relative_rotation = 单位阵、**relative_scale = 0.01**。
  该值 = 「axe mesh 原点对齐源 `Axe_Head` 骨」换算，配合 `weapon_jnt_l` 的烘焙握法轨使用。
  ⚠️ 旧的 `hand_rSocket` 配置（rot=(-13.7,-35.1,121.7) 等）已废弃 —— 那是挂在解剖左手上的错误锚点。
  ⚠️ Parent Socket **无 Python API** 只能编辑器手点（2026-09-22 确认用户已改好并保存在 BP；wp_60/wp_51 经 SubobjectData 读到的 hand_rSocket 是 CDO 旧值假象，勿据此重改）。
- **握法是动画数据**：46 条 LOL 线动画的 `weapon_jnt_l` 局部轨由 `wp_50` 从源 `R_Hand/Weapon`
  离线烘焙（`L_raw(t)=K∘(W_R_Hand⁻¹∘W_Weapon)`，K 只取旋转、平移置零）；
  验收硬指标：`|L_raw(t0)|` 必须等于源 `Weapon↔R_Hand` 距离（17.37/19.51/12.63 cm 逐条吻合）。
- 局部坐标朝向：**+Y = 大刃**（网格包围盒 21 × 172 × 77 cm，长轴 = 局部 Y）；
- **斧头网格战斗插槽（2026-09-21 补齐）**：
  已通过 `Scripts/asset/setup_axe_sockets.py`（使用 `StaticMesh.add_socket()` API）配置 5 个基准插槽：
  `Grip_Main` (0, 0, 0)、`Grip_Assist` (0, -25, -6.5)、`Pommel` (0, -83.4, -21.9)、`Blade_Tip` (0, -75.7, 50.1)、`Blade_Edge` (0, -45, 42)；
  门禁检查：`Scripts/anim/wp_20_weapon_audit.py`。
- **骨架里的武器锚点骨**：`weapon_jnt`（父 = `root`）、`weapon_jnt_r`（父 = `hand_r`）、`weapon_jnt_l`（父 = `hand_l`）。
  ⇒ 规范做法是把斧头改挂 `weapon_jnt`，让握法变成**动画数据**而不是 socket 常量。迁移偏移与步骤见
  `Saved/Attack/weapon_migrate_offset.json`；迁移前的完整性检查器：`Scripts/anim/wp_09_check_weapon_tracks.py`。

### 2.3 移动手感动力学契约 (`BP_DariusCharacter`)
- `SpringArmComponent`：`TargetArmLength = 380.0`，`SocketOffset = (0, 45, 20)`，`TargetOffset = (0, 0, 50)`，`bEnableCameraLag = True (Speed = 9.0)`，`bEnableCameraRotationLag = True (Speed = 12.0)`；
- `CharacterMovementComponent`：`MaxWalkSpeed = 220.0`，`MaxAcceleration = 1000.0`，`BrakingDecelerationWalking = 1400.0`，`GroundFriction = 6.0`；
- `BS_Darius_Locomotion`：Speed 轴范围 `[0, 220]`，满速 Walk 样本 `RateScale = 1.48`。

### 2.4 scale=100 契约：唯一常量源与门禁（2026-09-21 建档）

- **载体唯一**：骨架最外层骨 `darius_godking_mesh_LOD0_Skeleton` 的 `scale = 100.0`，位置恒为 0。
  其余全骨的 rest **局部平移是米级**（`pelvis` ≈ 1.0967），网格顶点是 **cm 级**（全高 202 cm）。世界 = 局部 × 100。
- **它溢出的四个地方**（每个都踩过）：
  1. **重定向产物**：重定向器会给最外层骨写一条 `scale = 1` 假轨道 ⇒ 角色缩成 **1.85 cm**、Chaos 披风被撑爆。
     每批重定向产物**必须**紧跟 `retarget/rtg_41_fix_outer_scale.py`（整条删轨，让它回落 reference pose）。
  2. **挂件**：Socket 的 `RelativeScale` 必须 `0.01`；`WeaponAxe` 组件的相对变换见 §2.2。
  3. **局部数字**：`pelvis` 基线 1.0967；`weapon_jnt` 烘焙时 17.37 cm 要写成 **0.1737**（写 17.37 斧头飞到 17 米外）。
  4. **布料与物理**：`CA_Darius_Cape` 约束距离、`SK_Darius_GodKing_Physics` 的 body 位置都活在 100× 空间里。
- **唯一常量源**：`Scripts/core/fight_scale.py`（`OUTER_BONE` / `OUTER_SCALE` / `cm_to_local()` / `SOCKET_SCALE`）。
  **禁止在任何脚本里再写裸 100 / 0.01 / 1.0967**，一律从它取。
- **门禁**：`Scripts/core/scale_audit.py`（只读）。扫全部目标骨架动画的最外层骨轨道 + `hand_rSocket` 缩放 + 活性检查，
  以 `VERDICT: PASS/FAIL` 结尾。重定向产物落盘后必跑。
- **为什么不清零这个 100**：数学上「最外层骨 scale→1、其余全骨局部平移 ×100」是世界等价的（网格顶点与 bind 零变化；
  引擎内有 `SkeletonModifier.set_bone_transform` + `commit_skeleton_to_skeletal_mesh` 可实施），但代价是
  60 条动画重写 + 布料/物理重标定 + M1 全量重验收 —— 在 M1 已验收、正要进战斗的节点上风险收益比不成立。
  真要动，先在副本上验证，不要直接上主资产。

---

## 3. 现役核心工具链索引 (`Scripts/`)

| 目录 | 职责 | 核心脚本（严禁随意改名或删除） |
| :--- | :--- | :--- |
| **顶层入口** | 引擎网关与编辑器运维 | `ue_remote.py`（★ 主网关：官方 Python 通道）、`ue_mcp.py`（MCP 客户端，见 §3.1）、`editor.deno.ts`（启动守护）、`editor_dialog.py`（弹窗处理）、`editor_focus.py`、`disable_throttling.py` |
| **`anim/`** | 移动、布料与动画生产线 | `loco_02_tune_character.py`（手感与机位调参）、`loco_03_tune_blendspace.py`（混合空间适配）、`loco_04_pie_verify.py`（PIE 物理探针）、`loco_05_cleanup.py`（关卡复位）、`cape_35_build_and_bind.py`（布料重绑定）、`cape_33_cloth_probe.py`（布料探针）、`axw_10_merge.py`（★ 分层合并）、`axw_17_phase.py`（相位分析）、`axe_42_tune.py`（持斧调参）、`idle_20_build2.py`（待机重建） |
| **`dcc/`** | DCC 无头数据处理 (Blender) | `blender_23_strip_cape_shell.py`（★ 剥离描边壳披风）、`blender_22_strip_all.py`（剔原模斧头）、`blender_split_weapon.py`（武器轴心重标定）、`blender_04_render.py`（离线渲染） |
| **`retarget/`** | 跨骨架重定向产线 | `ik_36_calibrate_retarget_pose.py`、`ik_37_verify_orientation.py`（朝向验收）、`ik_60_contact_audit.py`（落点审计）、`exp_cycle.py` |
| **`asset/` `core/`**| 资产提取与工程维护 | `extract_godking_assets.py`（一键提取 LOL 原版资产）、`import_weapon_asset.py`、`plan_99_clean_temp.py`、`list_engine_toolsets.py`（枚举引擎全部 toolset）、`list_mcp_tools.py`（枚举 MCP 已暴露工具）、**`fight_scale.py`（★ scale=100 契约唯一常量源）**、**`scale_audit.py`（★ scale 契约只读门禁）** |
| **武器契约（`anim/wp_*`）** | 武器挂点与门禁 | `wp_20_weapon_audit.py`（★ **一键门禁**：动画轨道 + 装配参数 + 几何 socket + 契约快照 diff）、`wp_12_set_rel_v2.py`（挂到 `weapon_jnt` 的相对变换，含带缩放的自检）、`wp_09_check_weapon_tracks.py`（动画轨道专项） |
| **`archive/`** | 历史踩坑证据链 | 归档探针存放于 `archive/anim/`、`archive/retarget/`、`archive/misc/` |

### 3.1 选哪条通道？—— MCP vs UE 官方 Python（**动手前先看这条**）

两条通道**互相独立、都要编辑器在跑**，但能力边界差得很远：

| | **MCP**（`Scripts/ue_mcp.py`） | **官方 Python**（`Scripts/ue_remote.py`） |
| :--- | :--- | :--- |
| 入口 | `http://127.0.0.1:8000/mcp`（编辑器启动自开） | UDP `6766` 发现 → TCP 命令通道 |
| 本质 | **白名单工具**：3 个元工具（`list_toolsets` / `describe_toolset` / `call_tool`）+ 已注册 toolset | **任意 Python**，完整 `unreal.*` API |
| 失败方式 | JSON Schema 调用前校验，参数错会提前告诉你 | 运行时才炸；崩了编辑器就崩了 |
| 本工程用量 | 低 | **≈ 全部现役脚本** |

**决策规则 —— 看「碰不碰这三样」：**

| 你的任务 | 走哪条 | 原因 |
| :--- | :--- | :--- |
| 读写 **`AnimSequence` 骨骼轨道**（分层合并、`weapon_jnt` 重解算、重定向） | **Python** | MCP 没有动画轨道工具 |
| 跑 **PIE 探针** / 读运行时姿态与物理 | **Python** | MCP 不碰运行时 |
| `IKRetargeterController` / `SkeletalMeshEditorSubsystem` / `UAnimationDataController` | **Python** | MCP 未暴露 |
| 需要**批量 + 前置门禁 + 后置数字验收**、循环、异常处理 | **Python** | MCP 是单次调用，没有脚本能力 |
| 单根骨的 **socket 增删改** / 读骨架层级 / 挂物理资产 | **MCP** `SkeletalMeshTools`(22) | 类型化、有 schema、不用写代码 |
| 查**资产引用** / 找资产 / 复制 / 删除 / 建目录 | **MCP** `AssetTools`(21) | 同上 |
| 改**蓝图图**（加变量 / 节点 / 连线 / 编译） | **MCP** `BlueprintTools`(53) | 同上 |
| 关卡里**摆 actor** / 查 actor 组件与变换 | **MCP** `SceneTools`(20) / `ActorTools`(17) | 同上 |
| **Sequencer / Control Rig** 编辑 | **MCP** `AnimationAssistantToolset`(319) | 同上 |
| 物理资产 body/shape/constraint、布料绑定、Dataflow 图 | **MCP**（本工程已启用） | 同上 |

**一句话**：**碰动画骨轨道 / PIE / 批量门禁 → Python；编辑器里一次明确的读写 → 先查 MCP。**

- ⚠️ 编辑器没开时端口 8000 不监听，`list_toolsets` 会失败。
- ⚠️ 可用 toolset **随启用的插件变化** —— 改 `.uproject` 后**必须重启编辑器**才生效（实测不热生效）。
- 本工程已在 `Fight.uproject` 启用 **`AllToolsets`** 聚合插件，可用 toolset 实测 **4 → 53 个**
  （约 630 个工具）。**调之前先 `list_toolsets` 抄准确名字** —— C++ 实现的是 `<Module>.<Class>`，
  Python 实现的是模块路径（如 `editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools`），猜名字会 `not found`。
- 详细清单与实测记录见 `Docs/Architecture/工具链能力边界与架构选型.md`。

---

## 4. 工业级防坑红线速查（踩过才写，违者必崩）

| 陷阱 | 表现与防护红线 |
| :--- | :--- |
| 🔴 **在 slate post-tick 回调中 `destroy_actor`** | 会引发 `EXCEPTION_ACCESS_VIOLATION` 崩溃编辑器！清理逻辑必须移至独立脚本或主线程执行。 |
| 🔴 **`ue_remote.py` 脚本内含 `.py` 字样** | UE Remote 嗅探机制会误判为路径导致**静默不执行**！严禁在代码或 docstring 里写入自身的脚本名。 |
| 🔴 **Slate 模态弹窗挂死游戏线程** | 导致 Remote Execution 彻底无响应。必须用 `editor_dialog.py --auto`（先发 `WM_CLOSE 0x0010` 消息）。 |
| 🔴 **编辑器后台节流假帧** | 视口非前台不 tick 导致 `capture_scene()` 拍出一模一样的假帧。测量前调前台或使用离屏 RT 渲染。 |
| 🔴 **骨架最外层 scale=100 轨道污染** | 重定向器会给最外层骨写一条 `scale=1` 轨道 ⇒ 角色瞬间缩到 1.85cm、Chaos 披风撑爆；武器 Socket scale 必须保持 0.01 抵消。**每批重定向产物落盘后必跑 `Scripts/core/scale_audit.py`；修法是 `retarget/rtg_41_fix_outer_scale.py`（整条删轨）。完整契约见 §2.4。** |
| 🔴 **`unreal.Rotator` 参数传错** | Python API 位置参数顺序为 `(roll, pitch, yaw)` 与常识相反！一律使用关键字参数 `unreal.Rotator(pitch=..., yaw=..., roll=...)`。 |
| 🔴 **Interchange 导入静默跳过工厂** | 目标资产名已存在时 Interchange 会静默跳过创建。重导入前必须先通过脚本或资产库彻底清除。 |
| 🔴 **并行修改同一文件** | 导致状态覆盖，多步自动化必须严格串行。 |
| 🔴 **交付物放进 `Saved/`** | `Saved/` 目录不进版本控制，正式交付成果与配置一律落入 `Content/` 或 `Source/`。 |
| 🔴 **新动画漏 `weapon_jnt` 键** | 斧头从 2026-09-21 起挂在 **`weapon_jnt` 骨**上。动画没有该骨的键时它会掉回 **rest 姿势**（骨盆附近的地上）⇒ 斧头飞走。**每条新动画（含重定向/分层合并产物）都必须有 `weapon_jnt` 轨道且逐帧有行程。** 门禁：`Scripts/anim/wp_20_weapon_audit.py`。 |
| 🔴 **挂到本骨架的组件忘写 `relative_scale = 0.01`** | 骨架最外层骨 `darius_godking_mesh_LOD0_Skeleton` 的 scale = **100** ⇒ 该骨架**所有骨的世界缩放都是 100×**。任何挂上去的组件（武器、特效、附加网格）都必须 `relative_scale = 0.01` 抵消，否则放大 100 倍。门禁同上。 |
| 🔴 **用 `get_attach_socket_name()` 判断挂点** | 它读的是**组件模板**，与 **SCS 节点**上的挂接信息**可能不同步**（实测：编辑器里已改成 `weapon_jnt`，函数仍返回 `hand_rSocket`）。**判断挂点以编辑器 Details 栏为准。** |
