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

### 0.2 下一阶段核心战役（战略跃迁）
**资产与表现打样已经稳定，从本阶段起，全面进入【基于现代 C++ 的核心战斗玩法框架】研发**：
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
- **最外层骨 scale = 100**：导致 `pelvis` 局部平移基线为 **1.0967**；所有挂接 Socket 的 `RelativeScale` 必须设为 **0.01**（正负相消，禁止改动最外层缩放）；
- **7 材质槽**：Slot 0 为反向法线描边壳（整模复制品），披风与斧头几何已从 DCC 彻底剔除；
- **披风布料**：Chaos Cloth Asset `CA_Darius_Cape` 绑定至 Section 1；固定组名必须为纯文本 `SimVertices3D`，权重映射为 `MaxDistance`。

### 2.2 战斧武器契约 (`SM_Darius_GodKing_Axe`)
- 挂接点：`SK_Darius_GodKing` 的 `hand_rSocket`（`rot=(-106.334, -70.982, 9.342)`, `loc=(0.18965, 0.10080, 0.00982)`, `scale=0.01`）；
- 局部坐标朝向：**+Y = 大刃**；打击判定 Socket：`Blade_Tip` / `Blade_Edge` / `Pommel`。

### 2.3 移动手感动力学契约 (`BP_DariusCharacter`)
- `SpringArmComponent`：`TargetArmLength = 380.0`，`SocketOffset = (0, 45, 20)`，`TargetOffset = (0, 0, 50)`，`bEnableCameraLag = True (Speed = 9.0)`，`bEnableCameraRotationLag = True (Speed = 12.0)`；
- `CharacterMovementComponent`：`MaxWalkSpeed = 220.0`，`MaxAcceleration = 1000.0`，`BrakingDecelerationWalking = 1400.0`，`GroundFriction = 6.0`；
- `BS_Darius_Locomotion`：Speed 轴范围 `[0, 220]`，满速 Walk 样本 `RateScale = 1.48`。

---

## 3. 现役核心工具链索引 (`Scripts/`)

| 目录 | 职责 | 核心脚本（严禁随意改名或删除） |
| :--- | :--- | :--- |
| **顶层入口** | 引擎网关与编辑器运维 | `ue_remote.py`（★ 唯一网关）、`ue_mcp.py`（MCP 客户端）、`editor.deno.ts`（启动守护）、`editor_dialog.py`（弹窗处理）、`editor_focus.py`、`disable_throttling.py` |
| **`anim/`** | 移动、布料与动画生产线 | `loco_02_tune_character.py`（手感与机位调参）、`loco_03_tune_blendspace.py`（混合空间适配）、`loco_04_pie_verify.py`（PIE 物理探针）、`loco_05_cleanup.py`（关卡复位）、`cape_35_build_and_bind.py`（布料重绑定）、`cape_33_cloth_probe.py`（布料探针）、`axw_10_merge.py`（★ 分层合并）、`axw_17_phase.py`（相位分析）、`axe_42_tune.py`（持斧调参）、`idle_20_build2.py`（待机重建） |
| **`dcc/`** | DCC 无头数据处理 (Blender) | `blender_23_strip_cape_shell.py`（★ 剥离描边壳披风）、`blender_22_strip_all.py`（剔原模斧头）、`blender_split_weapon.py`（武器轴心重标定）、`blender_04_render.py`（离线渲染） |
| **`retarget/`** | 跨骨架重定向产线 | `ik_36_calibrate_retarget_pose.py`、`ik_37_verify_orientation.py`（朝向验收）、`ik_60_contact_audit.py`（落点审计）、`exp_cycle.py` |
| **`asset/` `core/`**| 资产提取与工程维护 | `extract_godking_assets.py`（一键提取 LOL 原版资产）、`import_weapon_asset.py`、`plan_99_clean_temp.py` |
| **`archive/`** | 历史踩坑证据链 | 归档探针存放于 `archive/anim/`、`archive/retarget/`、`archive/misc/` |

---

## 4. 工业级防坑红线速查（踩过才写，违者必崩）

| 陷阱 | 表现与防护红线 |
| :--- | :--- |
| 🔴 **在 slate post-tick 回调中 `destroy_actor`** | 会引发 `EXCEPTION_ACCESS_VIOLATION` 崩溃编辑器！清理逻辑必须移至独立脚本或主线程执行。 |
| 🔴 **`ue_remote.py` 脚本内含 `.py` 字样** | UE Remote 嗅探机制会误判为路径导致**静默不执行**！严禁在代码或 docstring 里写入自身的脚本名。 |
| 🔴 **Slate 模态弹窗挂死游戏线程** | 导致 Remote Execution 彻底无响应。必须用 `editor_dialog.py --auto`（先发 `WM_CLOSE 0x0010` 消息）。 |
| 🔴 **编辑器后台节流假帧** | 视口非前台不 tick 导致 `capture_scene()` 拍出一模一样的假帧。测量前调前台或使用离屏 RT 渲染。 |
| 🔴 **骨架最外层 scale=100 轨道污染** | 最外层骨多一条 scale=1 轨道会导致角色瞬间缩小到 1.85cm；武器 Socket scale 必须保持 0.01 抵消。 |
| 🔴 **`unreal.Rotator` 参数传错** | Python API 位置参数顺序为 `(roll, pitch, yaw)` 与常识相反！一律使用关键字参数 `unreal.Rotator(pitch=..., yaw=..., roll=...)`。 |
| 🔴 **Interchange 导入静默跳过工厂** | 目标资产名已存在时 Interchange 会静默跳过创建。重导入前必须先通过脚本或资产库彻底清除。 |
| 🔴 **并行修改同一文件** | 导致状态覆盖，多步自动化必须严格串行。 |
| 🔴 **交付物放进 `Saved/`** | `Saved/` 目录不进版本控制，正式交付成果与配置一律落入 `Content/` 或 `Source/`。 |
