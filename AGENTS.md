# Fight 项目 Agent 开发上下文与工程全景 (AGENTS.md)

本文件是为接入本项目的 AI Agent（如 WorkBuddy、Antigravity、Qoder CN 等）定制的全局上下文。接手本项目的 Agent 必须在开启新会话时首先阅读本文档。

---

## 0. ⚠️ 美术资产处理铁律（最高优先级，任何 Agent 必读）

> 本节由 2026-09-18 的一次真实翻车事故沉淀而来，**违反本节 = 返工**。

### 0.1 相信数据，禁止主观臆断

**绝对禁止**在没有客观量化指标的情况下，凭"看起来差不多"就宣布美术资产处理完成。

- ❌ **反面教材（真实发生）**：把 LOL 俯视角动画重定向到 2XKO 骨架时，
  仅验证了「骨骼名能对上 / 动画能导入 / 脚不穿地」就交付，
  结果整套动画存在**系统性角度偏斜**（实测平均朝向误差 **26.8°**），被用户一眼看出。
- ✅ **正确做法**：先写**数值验证器**，再动资产。每次改动都要有可复现的数字验收。

**任何美术资产改动的标准流程**：
```
1. 建立客观指标  →  2. 基线测量  →  3. 提出假设  →  4. 用数据检验假设
   →  5. 假设被否就立刻换方向（不许硬撑）  →  6. 改动  →  7. 复测对比  →  8. 记录数字
```

### 0.2 用现成工具和轮子，不要自己造

| 场景 | 用什么 | 不要用 |
| :--- | :--- | :--- |
| 网格几何筛选 / 顶点空间查询 | Blender `mathutils.kdtree.KDTree` | 自己写 O(n²) 双重循环 |
| 网格面删除 / 拓扑编辑 | Blender `bmesh` | 手工改顶点数组 |
| 骨骼朝向 / 旋转插值 | `mathutils.Matrix` / `Quaternion` / `Vector.rotation_difference` | 自己推欧拉角 |
| 图片拼接 / 转码 / 逐帧合成 | `ffmpeg`（本机 `C:\ffmpeg\bin\ffmpeg.exe`） | PIL 手写 |
| 引擎内批处理 / 资产操作 | UE Python（`ue_remote.py` 网关） | 手点编辑器 |
| 数据解析（GLB/FBX 结构） | 直接解析 glTF JSON chunk（见 `glb_list_anims.py`） | 猜二进制布局 |

### 0.3 数值验证器的写法规范

验证器必须满足：**与"被验证对象的先验假设"无关**。

- ❌ 坏的指标：`angle(源骨朝向矩阵, 目标骨朝向矩阵)` —— 依赖各自的绑定朝向约定，会把"约定差异"误判成"错误"
- ✅ 好的指标：`angle(Q·源骨方向, 目标骨方向)` —— 只用**关节坐标**（两套骨架都精确可测），
  与骨骼朝向矩阵、静止姿态、绑定约定全部无关

**本项目已沉淀的验证器**（`Scripts/`，可复用，勿重复造）：

| 脚本 | 用途 |
| :--- | :--- |
| `blender_41_axis_audit.py` | 骨骼朝向自检：`bone.matrix_local` 的 Y 轴 vs 真实关节几何方向 |
| `blender_42_fidelity.py` | Swing 保真度：`angle(Q·Swing_src·Q⁻¹, Swing_tgt)` |
| `blender_70_joint_audit.py` | 逐关节弯曲角逐帧对比表 |
| **`blender_80_orient_verify.py`** | **★ 绝对朝向误差（最终判据，推荐首选）** |
| `blender_60/61/62_ab*.py` | A/B 并排渲染（同相机同帧） |
| **`plan_13_verify_fbx.py`** | **★ 跨会话端到端验收**：源与产物**各导入一次**再比。判据用「关节间距（缩放不变量）」+「逐帧关节轨迹」+「帧数」。**导出/导入环节的损失只有它能发现** |
| `plan_12_rest_stability.py` | **归因用对照实验器**：分层加压（零修改 → 删无关骨 → 全量手术），把「工具固有行为」与「本次操作引入」分开 |
| **`plan_16_audit_fbx.py`** | **★ 批量审计 FBX 的 bind pose**：与参考骨架比对关节间距。一条命令扫一个目录，直接给出 OK / WARN / BROKEN。**任何批量重导后都应先跑它** |
| **`plan_17_export_probe.py`** | **导出行为探针**：同一场景用三种方式各导一个 FBX 再回读，回答「怎样导出才能保证 bind pose 正确」。修导出逻辑前先跑它 |

**验证器的三条硬规矩（2026-09-18 从本轮实践提炼）**
1. **跨会话，不在同一会话内自比** —— 同进程自比永远发现不了导出/导入环节的损失。
2. **标尺必须用固定的同一组骨 + 只用关节 `head`** —— 源骨架混有道具骨（`Gem` tail z=836、
   `Axe_Handle` z=−90.8），用「全部骨」会算出 927 这种荒谬身高，两侧骨集合不同时还会得出 2.36 倍的假缩放因子。
3. **优先选缩放不变量作判据**（关节间距），它同时免疫单位换算与朝向约定差异。

### 0.4 假设必须可证伪，被否掉立刻换方向

本次事故中被数据否掉的假设（**留作教训，别再试**）：

| 假设 | 检验结果 | 结论 |
| :--- | :--- | :--- |
| Blender glTF 导入的 `matrix_local` 不可靠导致偏斜 | 确实不可靠（平均差 84.9°），但改成纯几何帧驱动后误差**反而没改善**（35.5°→37.1°） | **假设被否**，真因在别处 |
| 帧没对齐导致误差 | 对齐后数字不变 | **假设被否** |

**真因**：两套骨架的**静止姿态基准差**（源 A-Pose 与目标 A-Pose 的骨骼方向本来就不同，
前臂差 39°、锁骨 43°、骨盆-胯 41°）。旋转增量法只能搬"增量"，搬不动"基准差"。

---

## 1. 项目基础信息

- **项目名称**: `Fight`
- **引擎版本**: Unreal Engine 5.8
- **工程根路径**: `E:\UE\Fight`
- **主要主关卡**: `/Game/Level/Lv-FIght.umap`
- **代码与脚本**: C++ 模块 (`Source/Fight/`) + 自动化管线工具库 (`Scripts/`)
- **Git 远程仓库**: [d3intran/Fight](https://github.com/d3intran/Fight)（主分支：`main`）
- **开发规范**: Python 走 `uv`，JS/TS 走 `deno`，**严禁未自验交付**（见第 0 节）。

---

## 2. 核心架构与各系统当前落地状态

### 2.1 训练场与视觉基座 (Stellar Blade 风格)
- **关卡**: `/Game/Level/Lv-FIght`
- **关卡 Actor 清单**（**基线，7 个，勿动**。以下为 **actor label**，脚本里 `get_actor_label()` 读到的就是这些；
  内部名 `StaticMeshActor_1` / `DirectionalLight_0` / … 是另一套，别拿来做匹配）：
  `TrainingGround_Floor`(六边形地砖) / `TrainingGround_KeyLight` / `TrainingGround_Softbox` /
  `TrainingGround_SkyLight` / `TrainingGround_Fog` / `TrainingGround_PostProcess` / `PlayerStart`
- **清理**：`Scripts/plan_99_clean_temp.py` 会删 UE 临时目录（`/Game/Temp*`）并清除
  `SIM_*` / `ABTest_*` / `XYZ_*` / `DBG_*` 等前缀的临时 actor，跑完打印 actor 清单供复核。
  **每次做完 UE 侧验证都要跑它**（2026-09-18 曾残留一个 `SIM_Darius`）。
- **科技地砖**: 六边形程序化材质 `M_TrainingGround_Grid`（《剑星》风格高质感浅灰）。
- **环境光照**: 远景雾霭虚化地平线，消除死黑。

### 2.2 角色系统：神王 德莱厄斯 (God-King Darius)
- **蓝图类**: `/Game/Character/Darius/Blueprints/BP_DariusCharacter` (基于 `ACharacter`)
- **高模来源**: `2XKO`（原 Project L）次时代写实高模。
- **骨骼网格体**: `/Game/Character/Darius/SK_Darius_GodKing`
  - **309 根骨骼**，人体主干兼容 UE Mannequin 命名（`pelvis` / `spine_01` / `thigh_l` …），
    另含 ~150 根面部表情骨、披风链 `cape_chain_*`、武器骨 `weapon_jnt`。
  - **材质槽 7 个**（2026-09-18 由 8 个减为 7 个，见下方"描边壳陷阱"）。
- **PBR 材质体系**: `/Game/Character/Darius/Materials/`
  - `M_Darius_Master` + 贴图解包 Albedo / MPO 金属粗糙度遮罩 / Emissive。
  - 肩甲狼头眼睛与胸甲菱石配置了橙红狂怒微光（Emissive）。

#### ⚠️ 描边壳陷阱（2026-09-18 实测，极高危）
2XKO 模型的 **Slot 0「描边壳」`darius_godking_mesh_LOD0`（50827 顶点）是整个模型的完整复制品**，
里面**也复制了一份插地待机斧**。只把斧头槽位设为透明材质 `M_Invisible` 是挡不住的 ——
描边材质是反向外壳着色，渲染出来是**纯黑斧头剪影**。

- **根因**：`M_Invisible` 只能挡住槽 7 的斧头本体，挡不住槽 0 描边壳里的副本。
- **正确解法**：**必须在 DCC 阶段真正删除几何**，不能只靠材质隐藏。
  `Scripts/blender_22_strip_all.py`：以斧头本体顶点建 `KDTree`，把描边壳中距离 < 5cm 的顶点判为斧头并删面，
  再把斧头本体网格对象整体删除。实测距离分布**完美双峰**（斧头顶点 p10 = 3.3mm，其余 p20 已有 684mm）。
- **验收指标**：全部网格 `z < -0.02` 的顶点数必须为 **0**。
- **附带发现**：`M_Invisible.cast_dynamic_shadow_as_masked` 默认 `False` ——
  masked 材质自身不可见，**却仍按实体投出完整阴影**。已改 `True`。
  （Python 属性名是 `cast_dynamic_shadow_as_masked`，**没有 `b_` 前缀**）

### 2.3 武器管线：神王战斧 (SM_Darius_GodKing_Axe)
- **静态网格体**: `/Game/Character/Darius/Weapons/SM_Darius_GodKing_Axe`（从 2XKO 中无头 Blender 剥离）。
- **插槽埋点**: `Socket_Blade_Tip` / `Socket_Blade_Edge` / `Socket_Pommel`，为近战 Box Trace 预留。
- **角色装配**: `BP_DariusCharacter` 中注册 `WeaponAxe` (StaticMeshComponent)，挂接到 `hand_rSocket`。
- **尺度契约**: `hand_rSocket` 的 `RelativeScale = (0.01, 0.01, 0.01)`，
  抵消根骨骼 `darius_godking_mesh_LOD0_Skeleton` 的 100× FBX 米→厘米换算。
  战斧世界尺寸应为 **21 × 172 × 77 cm**，世界缩放 **1.0**。

#### ⚠️ 战斧握持姿态契约（2026-09-18 修复，勿随意回改）
- **`hand_rSocket.relative_rotation = (-106.334, -70.982, 9.342)`**
- **`hand_rSocket.relative_location = (0.18965, 0.10080, 0.00982)`**（bone 空间；≈21.5cm 世界偏移）
- 语义：斧头 **UE 局部 +Y 端 = 大刃**（不是尾钩！），XY 轴与 FBX 的符号相反。
  当前姿态 = 大刃朝上（与世界上向夹角 15°，前倾）、刃面法线朝世界 ±X、握柄中部落于手心、尾钩朝下。
- **修复前状态**：`relative_rotation = (90,0,0)`、`relative_location = (0,0,0)`，
  导致**整块 77cm 大刃插进角色胸腔内部被遮挡**，外部只剩握柄 + 尾钩 —— 视觉上等价于「斧刃被删了」。
- **原始缺陷**：`blender_split_weapon.py` 里 `grip_z = min_v.z + size_v.z * 0.35` 用错了轴
  （斧头长轴是 **Y**，不是 Z），pivot 实际落在**刃根**而非握柄。当前 21.5cm 偏移是对它的临时补偿。
- **验收脚本**：`Scripts/axe_21_apply_and_verify.py`（8 条指标），完整复盘见
  `Docs/Axe/Axe_Display_Fix_Report.html`。

### 2.4 神王原版资产备用库 (`E:\UE\Assets\Darius_GodKing_LOL_Original`)
从本地《英雄联盟》客户端全量解包与格式转换完毕的官方原版资产：
- `Animations_GLB/`: `darius_skin15_all_anims.glb`（**46 个动作全集成**）+ 10 个独立动作 GLB。
- `Audio_SFX/`: 56 个无损 `.wav` 打击/狼嚎/断头台挥斩音效。
- `Audio_VO_zh_CN/` `Audio_VO_en_US/`: 各 225 个无损语音。
- `Particles_VFX/`: 107 个技能特效网格（`.scb`）、贴图与粒子定义。

---

## 3. 自动化与开发工具库 (`E:\UE\Fight\Scripts`)

### 3.1 引擎网关与解包

| 脚本 | 作用 |
| :--- | :--- |
| **`ue_remote.py`** | **UE Python 远程执行网关**。UDP 组播发现 + TCP JSON，无需插件向活跃 Editor 发代码。
`uv run python Scripts/ue_remote.py <script.py>` |
| `extract_godking_assets.py` | 一键扫描 LOL WAD 包，`cdtb` + `lol2gltf` + `vgmstream` 提取动画/音效/语音。 |
| `glb_list_anims.py` | 直接解析 GLB 的 glTF JSON chunk，列出全部动画名与时长（无需 3D 库）。 |

### 3.2 DCC 资产处理（Blender 无头）

| 脚本 | 作用 |
| :--- | :--- |
| `blender_split_weapon.py` | 从合体 FBX 剥离武器网格、Pivot 校准至握柄。 |
| **`blender_22_strip_all.py`** | **剔除描边壳中的斧头副本 + 删除斧头本体对象**（见 2.2 描边壳陷阱）。 |
| `blender_04_render.py` | 通用动画预览渲染（人形骨骼定框 + 标准 look-at 相机）。 |
| `blender_60/61/62_ab*.py` | A/B 并排 / 同机位对比渲染。 |

### 3.3 ★ 动画重定向管线（核心）

| 脚本 | 作用 |
| :--- | :--- |
| **`blender_51_retarget_v4.py`** | **★ 正式版重定向器**。纯几何帧驱动 + 逐骨骼静止基准对齐矩阵 K。
`blender -b -P ... -- <SRC_GLB> <TGT_FBX> <spine_pitch> <OUTDIR> <anim1,anim2,...>`。
**输出契约（2026-09-18 已变更）**：导出前清 rest pose + `bake_anim_use_all_actions=True`
⇒ 产出**单文件多 take**（`A_Darius_All_TP.fbx`），不再是「每动作一个 FBX」 |
| `blender_30_batch_retarget.py` | 批量版（v3 逻辑，已由 v4 取代，保留作对照）。**导出段已同步修复** |
| `blender_50_retarget_v3.py` / `blender_10_retarget.py` | 更早版本，仅作对照；导出段已补 rest 复位，但 `blender_10` 的输出契约未经验证，**勿用于新工作** |
| `blender_41/42/70/80_*.py` | 验证器组（见 0.3） |

**M1-① 源骨架净化组（2026-09-18 新增，`plan_*` 前缀）**

| 脚本 | 作用 |
| :--- | :--- |
| **`plan_10_src_clean.py`** | **★ 源骨架白名单净化主脚本**。采样 → 重挂父级 → 删 120 骨 → 回写世界矩阵 → 三层验收 → rest 复位 → 导出多 take FBX。`blender -b -P ... -- <SRC_GLB> <OUT_FBX> <OUT_REPORT>` |
| `plan_10_probe_src.py` | 源骨架全量实测：骨名/父级/长度/层级树/前缀分组/46 action 清单/腿臂链深挖 |
| `plan_11_action_probe.py` | 前置可行性验证：slotted action 可否逐 action 绑定 + 孪生骨活动性 + frame_set 是否真求值 |
| `plan_12_rest_stability.py` | **三组对照实验**（A 零修改 / B 删无关骨 / C 全量手术），用于把「工具固有行为」与「我的操作引入」分开 |
| **`plan_13_verify_fbx.py`** | **★ 跨会话端到端验收器**（源 vs 产物各导入一次再比）。**后续所有 FBX 产物都应过这一关** |
| `plan_01_skel_audit.py` / `plan_02_proportion.py` / `plan_03_lean_audit.py` / `plan_04_facing.py` / `plan_05_headpitch.py` | 骨架结构审计 / 源目标比例对照 / 逐动作躯干倾角 / 前后方向锚定 / 头颈俯仰偏离 |
| `plan_99_clean_temp.py` | 清理 UE `/Game/Temp` 诊断期临时资产 |

### 3.4 UE 侧导入 / 诊断

| 脚本 | 作用 |
| :--- | :--- |
| `anim_10_import_batch.py` | 批量导入 FBX 动画到指定骨架（`FbxImportUI.skeleton` 必须显式指定） |
| `anim_12_import_snap.py` | 同上，但开启 `snap_to_closest_frame_boundary`（30fps 帧边界对齐） |
| `disable_throttling.py` | 关闭视口后台节流（`t.IdleWhenNotForeground 0`），解决截图冻结假帧。 |
| `ik_01_import_source.py` | 把净化后的 LOL 源骨架（59 骨 + 46 动画）导入 `/Game/Character/Darius/LOL_Source/` |
| `ik_03_target_rig.py` / `ik_04_src_rig.py` | 建目标 / 源 IK Rig（含链定义） |
| `ik_05_retargeter.py` / `ik_06_verify_map.py` / `ik_07_default_ops.py` | 建 IK Retargeter、加 op 栈、自动映射链 |
| **`ik_11_batch_retarget.py`** | **★ 批量重定向**（`IKRetargetBatchOperation`） |

### 3.5 IK Rig / IK Retargeter 的 Python 自动化（2026-09-18 打通）

**已建成资产**（`/Game/Character/Darius/Retarget/`）：

| 资产 | 内容 |
| :--- | :--- |
| `IK_LOL_Source` | 源 IK Rig。骨架 `SK_LOL_Darius`（59 骨）；**9 条链**；retarget root = `Root` |
| `IK_Darius_Target` | 目标 IK Rig。骨架 `SK_Darius_GodKing`（309 骨）；**29 条链**（`apply_auto_generated_retarget_definition()` 生成）；retarget root = `pelvis` |
| `RTG_LOL_to_Darius` | IK Retargeter。5 个默认 op；**9/9 链已自动映射** |

**源链定义**（链名必须与目标一模一样，Retargeter 才能配对）：

| 链名 | 源 start → end | 目标 start → end |
| :--- | :--- | :--- |
| `Spine` | `Spine1` → `Spine2` | `spine_01` → `spine_03` |
| `Neck` | `Neck` → `Neck` | `neck_01` → `neck_01` |
| `Head` | `Head` → `Head` | `head` → `head` |
| `LeftLeg` / `RightLeg` | `L_Hip` → `L_Foot` | `thigh_l` → `foot_l` |
| `LeftClavicle` / `RightClavicle` | `L_Clavicle` → `L_Clavicle` | `clavicle_l` → `clavicle_l` |
| `LeftArm` / `RightArm` | `L_Shoulder` → `L_Hand` | `upperarm_l` → `hand_l` |

⚠️ 注意目标侧 `LeftArm` **从 `upperarm_l` 起**（不含 clavicle）；`Neck`/`Clavicle` 是**单骨链**。
⚠️ `Spine` 链目标 3 骨、源 2 骨（源骨架脊椎只有 `Spine1/Spine2`）—— 数量不等，待评估影响。

**API 速查（全部实测签名）**

| 步骤 | 调用 |
| :--- | :--- |
| 建 IK Rig | `at.create_asset(name, dir, unreal.IKRigDefinition, unreal.IKRigDefinitionFactory())` |
| 取控制器 | `unreal.IKRigController.get_controller(rig)` |
| 指定骨架 | `ctrl.set_skeletal_mesh(mesh)` —— 要 **SkeletalMesh**，不是 Skeleton |
| 自动建链 | `ctrl.apply_auto_generated_retarget_definition()`（Mannequin 命名有效） |
| 手动建链 | `ctrl.add_retarget_chain(chain_name, start_bone, end_bone, goal_name)` —— **4 参** |
| 设 root | `ctrl.set_retarget_root(bone_name)` |
| 建 Retargeter | `at.create_asset(name, dir, unreal.IKRetargeter, unreal.IKRetargetFactory())` |
| 绑定 IK Rig | `ctrl.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, rig)` —— **枚举在前** |
| 🔴 **加 op 栈** | `ctrl.add_default_ops()` ← **必须先做，否则 `auto_map_chains` 静默不生效** |
| 自动映射链 | `ctrl.auto_map_chains(unreal.AutoMapChainType.EXACT, True)` |
| 查映射 | `ctrl.get_source_chain(target_chain_name)` |
| 批量重定向 | `unreal.IKRetargetBatchOperation.run_batch_retarget(inputs)`，`inputs` 是 `IKRetargetBatchOperationInputs` 结构（字段：`assets_to_retarget` / `ik_retarget_asset` / `target_path` / `search` / `replace` / `prefix` / `suffix` / `overwrite_existing_files` / `include_referenced_assets`） |

**UE 5.8 的架构变化**：IK Retargeter 已改为 **Op Stack**。`add_default_ops()` 会加入
`Pelvis Motion / FK Chains / Run IK Rig / Root Motion / Remap Curves` 五个 op。
旧属性 `chain_settings` / `global_settings` / `root_settings` / `chain_map` **全部废弃**
（读它们只会得到 DeprecationWarning，且 `chain_map` 已不可读）。

**🔴 资产路径格式陷阱（会让编辑器崩溃）**
`EditorAssetLibrary.list_assets()` 返回的是 **`package.object`** 形式
（`/Game/X/A.A`），而 `find_asset_data()` / `rename_asset()` 需要**纯 package 路径**
（`/Game/X/A`）。把带 `.object` 的串拼进路径交给 `rename_asset()` ⇒
**EXCEPTION_ACCESS_VIOLATION，编辑器整个挂掉**（2026-09-18 实测崩溃一次）。
⇒ 一律先 `pkg = a.split(".")[0]`。
⇒ 另外 `rename_asset()` 即使传对路径，**未 save 前效果会回退**（实测返回 True 但列表未变）。

---

## 4. 动画绑定计划

> ⚠️ **本节的 A1~A4 是历史记录（2026-09-18 上半场）。**
> **正式执行计划已定稿到 `Docs/Retarget/FINAL_Retarget_Plan.html`**，管线为
> `DCC 净化 → UE IK Retargeter → Control Rig 运行时层 → 门禁验收`，
> 里程碑 **M0 尺子(0.5d) → M1 垂直切片 idle+run(3.5d) → M2 全量动作与风格(4d)**。

### M1-① 源骨架净化 —— ✅ 已完成（2026-09-18）

**产物**：`Saved/Retarget/Clean/Darius_SrcClean.fbx`（**59 骨 / 46 动作 / 30 fps / 25.26 MB**）
**报告**：`Docs/Retarget/M1-1_Source_Clean_Report.html`
**脚本**：`plan_10_src_clean.py`（主管线）、`plan_13_verify_fbx.py`（可复用的跨会话验收器）

**三条被实测推翻的既有认知（重要，勿再沿用旧说法）**

| 旧说法 | 实测 |
| :--- | :--- |
| 踝关节 = `L_KneeLower.tail` | ❌ 那里 z=56.54；真正踝 = `L_Foot.head`，z=**16.93**，差 39.6 单位 |
| 删 `L_KneeLower` 保 `L_KneeUpper` | ❌ **方向反了**。实测 run：`KneeUpper` 旋转恒 **0.000°**（只有 8.94 平移），`KneeLower` 旋转 **60.9°** ⇒ 必须**删 Upper 保 Lower** |
| 用 `bone.tail` / `bone.length` 判断走向 | ❌ `L_Hip.tail` 指向 −Y（前方），真实髋→膝是 −Z（下方）⇒ **关节真值只能用 `head_local`** |

**手术**：179 → 59 骨。剔除 `Lion_*` 四足子树(70)、`Weapon` 子树(15)、`Throne/Gem/Piece_*`(7)、
`*Buffbone*`/`*_Loc` 挂点(≈20)、四根孪生 `*Upper` 占位骨、肩甲/背包/SnapWeapon。
腿链压成 `L_Hip → L_KneeLower → L_Foot`（与目标 `thigh_l → calf_l → foot_l` 一一对应）。
消失父级的贡献用**世界矩阵采样-回写**补偿（`pose_bone.matrix` setter 自行反解 basis，
比手推四元数公式可靠）。回写必须**同时写 location / rotation_quaternion / scale 三通道**。

**验收（三层，全 PASS）**
- L1 结构：59 骨、无残留、无误删、fcurve 清理 49,460 条
- L2 会话内：46 动画 × **3,078 帧** × 27 关节逐帧比对 — 最大旋转偏差 **0.000000°**，最大位置偏差 0.0135 单位（相对身高 7.0e-05）
- L3 跨会话端到端（源 GLB vs 产物 FBX 各导入一次）：关节间距相对差 **3.53e-07**、46/46 帧数一致、轨迹归一化偏差 **7.14e-05**

**残留（已评估，接受）**：`R_Foot` 的 rest `matrix_local` 偏 2.680e-04 ⇒ 世界位置 0.0135 单位 = 0.135 mm。
成因：改 `edit_bone.parent` 触发 `Bone.matrix_local` 重建，对 0.014 单位微骨有数值损失（对照实验见 §5）。
量级是 G2 门禁阈值（1.5% 身高）的 **1/214**。

### 历史记录：自研几何帧管线（现已降级为「离线数值验证器」）

**A1. 已完成** —— 建立可量化管线，误差从 26.8° 降到 9.7°
- 核心算法（`blender_51_retarget_v4.py`）：
  ```
  D_src = F_src_pose · F_src_rest⁻¹          # 源骨骼世界旋转增量（F = 关节坐标构造的几何朝向帧）
  D'    = Q · D_src · Q⁻¹                     # Q = 两套骨架基准系对齐矩阵（实测绕 Z 180°）
  K     = u_tgt.rotation_difference(u_src)    # 逐骨骼「静止基准对齐」最小弧旋转
  W_tgt = D' · K · R_tgt_rest                 # 目标骨骼世界朝向
  ```
- ⚠️ K **必须**用最小弧旋转，不能用整个矩阵 `Q·F_src·F_tgt⁻¹`（滚转参考差 180°，会翻转骨骼）。
- 实测（run 动画，504 样本）：均值 **9.7°** / 中位 **6.0°** / P90 24.2°
- ⚠️ **该结果已不足以交付**：只验了朝向，没验关节位置/脚滑/速度闭环。v4 的
  `SPINE_PITCH` 权重（spine_01 45%/spine_02 35%/spine_03 20%/neck_01 −60%）是**无出处魔数，已作废**。

**A2. 腿部 17°~22° 残留的真因（2026-09-18 定位）**
- 元凶是**源骨架的膝/肘 Upper-Lower 等长双骨**：
  `L_Hip 48.84 → L_KneeUpper 48.84 → L_KneeLower 50.63`，`L_Shoulder 40.54 → L_ElbowUpper 40.54 → L_Elbow 22.04`
  —— 三点链共线 ⇒ 几何帧的 `cross(y, ref)` 退化，极限帧误差放大到 63°。
- 修正：链中**只用 `L_KneeLower`**（膝 = `L_KneeLower.head`），彻底不出现 `L_KneeUpper`。

**A3. 足部锁地 与 比例真相（2026-09-18 实测修正）**
- 目标网格 z 上限 = **2.06 m**（不是 2.47 m）；源 LOL 腿长/身高 = **0.5281** > 目标 **0.5050**
  ⇒ LOL 的腿**相对更长**，"短腿对长腿"的说法**方向反了**。
- 滑步真因 = **动画隐含速度 ≠ `CharacterMovement` 速度**。
- 比例偏差的正确表述：**髋间距/身高** LOL 0.1418 vs 目标 0.1107（目标窄 22% ⇒ 旋转照搬后膝间距比源窄约 5.7cm，观感"夹腿"）；
  **颈骨长/身高** 目标长 84% ⇒ ⚠️ **不是"头浮高"**（旋转传递下头高由目标骨架决定），
  **真实后果是同样大小的颈部旋转令目标头部前后位移放大 1.84 倍**。
- 方案：UE 官方 **Speed Planting**（源动画加 `MotionExtractorModifier` 生成脚速曲线）+ **Stride Warping**。
- **验收**：① 支撑相脚掌漂移 < 2cm；**② 动画隐含速度 vs `MaxWalkSpeed` 误差 < 5%**（只测①会漏掉世界空间滑步）。

**A4. 根运动 —— 已定为「不做」**
- 源 LOL 动画**本就是 in-place**（位移交给游戏代码）。选 in-place + `CharacterMovement` 驱动，
  "提取 root motion"是白做工作。

### 落地要点（并入 M1/M2）
- `anim_12_import_snap.py` 批量导入（30fps 帧边界对齐是硬要求）
- `BS_Darius_Locomotion`（Speed 0~600 / Direction ±180）—— ⚠️ **LOL 没有 walk**，需从 `run` 降速重采样生成
- `ABP_Darius`：duplicate `ABP_Unarmed` → 改 `target_skeleton` → 改写 `sequence` 引用 → 编译
  - ⚠️ Python **无法新增** AnimGraph 节点（`EdGraph` 无 `add_node`），只能改写已有节点
  - Idle↔Run 用 **Inertialization** 而非 Crossfade
  - **去倾斜偏置必须放在运行时层**，且定义为 `offset(speed)` **连续曲线**（自变量 = 实测的动画隐含速度）
- `BP_DariusCharacter.anim_class` 指向 `ABP_Darius`（当前是骨架不匹配的 `ABP_Unarmed`）

### 阶段 C：战斗与技能（原路线图顺延）

1. **攻击连招与打击判定**：战斧 3 个 Socket 做 Box/Sphere Trace；刀光 Ribbon Trail；接 `attack1` + 打击音效。
2. **GAS 技能全复刻**：
   - 被动：流血 1~5 层 + 血怒爆发与狼灵特效
   - Q 大杀四方（内外圈双判定）/ W 致残打击 / E 无情铁手 / R 诺克萨斯断头台

---

## 5. 已知环境陷阱速查（补充）

| 陷阱 | 表现 | 规避 |
| :--- | :--- | :--- |
| **GameThread 自锁** | `while is_in_play_in_editor(): sleep()` 会让编辑器永久 Not Responding | 只发一次 `editor_request_end_play()`，外部 shell sleep |
| **PIE 中导入 SkeletalMesh** | Interchange 报 `Cannot import SkeletalMeshNode asset at runtime`，静默只建材质不建网格 | 导入前必须先退出 PIE |
| **30fps 帧边界** | `Animation length ... is not compatible with import frame-rate 30 fps` | Blender 场景 fps 设 30，或导入时开 `snap_to_closest_frame_boundary` |
| **`EditorAssetLibrary.load_asset` 返回 None** | 资产明明存在却拿不到 | 改用 `unreal.load_asset(path)` |
| **重导 SkeletalMesh** | 担心丢材质/插槽 | 实测：材质覆盖按槽名完整保留，`hand_rSocket` 连同 0.01 缩放自动保留；槽位数会随 FBX 材质数变化 |
| **编辑器视口截图** | HighResShot 静默失败或延迟数十秒 | 优先用 PIE（独立窗口渲染）；`AutomationLibrary.take_high_res_screenshot` 第 4 参是 **CameraActor 对象**不是 bool |
| **导入动画到已有骨架** | 会另建一个同名后缀骨架，动画挂不上 | 必须显式设 `FbxImportUI.skeleton` |
| **`unreal.Rotator` 位置参数顺序** | 是 **(roll, pitch, yaw)**，不是 (pitch, yaw, roll)。历史上多张「拍歪」的截图都因此 | 一律用关键字：`unreal.Rotator(pitch=.., yaw=.., roll=..)` |
| **改 socket 相对旋转无效果** | 组合顺序实为 `World = Compose(Rel, Parent)`，与直觉相反（实测残差 0.000000 vs 5.508537） | 改 socket 前先用 `(0,0,0)` / `(0,90,0)` 两点标定组合顺序 |
| **`MathLibrary` 函数缺失** | 该版本没有 `invert_rotator` / `rotate_vector` / `quat_from_rotator` / `rotator_from_quat` | 改用「坐标下降 + `compose_rotators` + `get_forward/right/up_vector`」纯数值求解（残差可到 1e-7） |
| **`HighResShot` 截图不落地** | 静默失败无日志；**一次运行只认最后一条**；文件落地延迟 1~4 分钟 | 改用 `SceneCapture2D` + `RenderingLibrary.export_render_target`（离屏稳定、一次可拍多张）。输出是无扩展名 HDR，用 ffmpeg 转 LDR |
| **直接改组件的 `relative_location`** | 组件会脱离 socket 挂载，世界变换退化成单位矩阵 | 握持偏移一律写在 **socket** 上，组件相对变换保持单位值 |
| **`EditorAssetLibrary.unload_asset`** | 该版本不存在 | 复核存盘值重新 `unreal.load_asset` 再读属性即可 |
| **FBX↔UE 局部轴语义翻转** | Blender 直方图显示大刃在 −Y，UE 里实际在 **+Y**；包围盒 Y 对称，数值上分辨不出 | 用「无遮挡渲染 + 已知机位」反证，别靠数值推断轴的正负 |
| **"物体好像被删了"** | 单张截图上「真被删」与「被身体挡住」无法区分 | 四步收敛：①顶点计数 ②材质链路 ③同变换无遮挡对照 ④世界坐标核算 |
| 🔴 **FBX 导出前未复位 rest pose** | Blender 把**导出瞬间的 pose**写成骨架的节点变换 ⇒ 产物 **bind pose 完全错误**。对 IK Retargeter 是致命伤 | **导出前**：`arm.animation_data.action = None` + 逐个 `pb.matrix_basis = Matrix.Identity(4)` + `view_layer.update()`；**同时必须用 `bake_anim_use_all_actions=True` 单文件多 take 导出** |
| 🔴 **逐 action 导出无法保证 bind pose**（同上一条的推论） | `plan_17` 探针实测（同一场景三种方式各导一个 FBX 再回读）：<br>**A** 挂 action + `frame_set` 后导出（历史做法）→ 间距偏差 **5.843e-02 BROKEN**<br>**B** 清 pose，`all_actions=False` → **1.198e-07 OK**，但**只含 1 个动画**<br>**C** 清 pose，`all_actions=True` → **1.198e-07 OK**，46 个动画全保真 | 要导多个动作**只能选 C**。`all_actions=False` 时挂回 action 必然污染；而清 pose 后该模式导哪个动画不确定 ⇒ 不可用 |
| 🔴 **历史产物规模（`plan_16` 审计）** | `Saved/Retarget/` 下 17 个 FBX，**15 个 BROKEN**：关节间距偏差 1.4%~**15.4%**（TurnL/TurnR 最差、Attack1 12.8%、RunFast 9.8%）。同一动作在 Batch 与 V4 两批里偏差还不同 ⇒ 每个文件记录的是「导出那刻 frame 停在哪」 | `blender_51_retarget_v4` / `blender_30` / `blender_50` / `blender_10` **四个脚本已全部修复**。**Batch/ 与 V4/ 下的旧产物已废弃，勿再导入 UE**；修复后的产物见 `Saved/Retarget/V5/`（实测 5.926e-07 OK） |
| **改导出逻辑前先跑 `plan_17_export_probe.py`** | 目测/推理判断不了 Blender 的导出器行为 | 探针成本约 3 分钟，能一次定死「哪种导出方式正确」，比改完再验证省得多 |
| **改 `edit_bone.parent` 会触发 rest 重建** | `Bone.matrix_local` 被重算，对短骨有数值损失（`R_Foot` 0.014 单位 ⇒ 2.68e-04 偏差，经骨链放大成 0.0135 单位世界偏差）。对照实验：零修改进出 edit mode 与「只删骨不改 parent」均为 **0 偏差** | 删除骨后**用快照写回** `head/tail/roll`；先用两趟循环把全部 `use_connect=False` 再写，否则设父骨 tail 时会拉走子骨 head。若仍残留 ~1e-4，量级可忽略，如实记录即可 |
| **Blender 5.x 的 `Action.fcurves` 已移除** | 4.4 起改用 slotted action：`action.layers[].strips[].channelbags[].fcurves`，直接访问 `action.fcurves` 抛 `AttributeError` | 写兼容读取函数；action 名在 FBX 导入后会带前缀（`skinned_mesh\|skinned_mesh\|xxx`），比对前 `name.split("\|")[-1]` |
| **身高/标尺类指标不能用「全部骨」** | 源骨架混有道具骨（`Gem` tail z=836、`Axe_Handle` z=−90.8），算出的「身高」是 927 而非 191.6；两侧骨集合不同时会得出 2.36 倍的假缩放因子 | 用**固定的同一组骨** + 只用 `head_local` 算标尺；优先选**缩放不变量**（关节间距）作判据 |
| 🔴 **`ue_remote.py` 的「`.py` 字样」陷阱** | `MODE_EXEC_FILE` 下若向 UE 传脚本**内容**，UE 会在内容里嗅探形如 `xxx.py` 的字样并误判为文件路径 ⇒ **只要 docstring / 注释里写了自己的文件名（如用法示例），整个脚本静默不执行**，报 `Could not load Python file '<整段内容>'` | **已在网关修复**：一律先落盘到 `Scripts/_ue_remote_run.py` 再传**路径**，失败时回退传内容。二分定位过程见 `Docs/Retarget/M1-1_Source_Clean_Report.html` §4.C（5 组对照实验，已排除长度因素） |
| **纯骨架 FBX 导进 UE 产出 0 资产** | 只含 armature 的 FBX，UE 报「导入成功」但 `imported_object_paths = 0`，不报错、不生成任何东西 | UE 需要**至少一个 SkeletalMesh** 作骨架载体。导出时保留源网格（清空材质槽 + 删除失效顶点组），`use_selection` 同时选中 armature 与网格 |
| **UE 侧骨架比 FBX 多 1 根骨** | Blender 读 FBX 得 59 骨，UE 得 60 | Blender `armature_nodetype='NULL'` 造的 NULL 根节点被 UE 当成一根骨（在原点、单位变换，不引入偏移）。建 IK Rig 时从 `Root`/`L_Hip` 起链，忽略最外层 |
