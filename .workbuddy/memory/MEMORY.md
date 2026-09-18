# Fight 项目长期笔记

## 硬性约定
- **代码规范**：Python 走 `uv`（`uv run --no-project python`），JS/TS 走 `deno`。
- **Bash 工具 PATH 残缺**：每条命令前加 `export PATH="/usr/bin:/bin:/mingw64/bin:$PATH"`；`/tmp` 在 git-bash 与 python 之间不互通，临时脚本写成项目内文件。
- **改资产前先备份**到 `Saved/Backup_*/`。
- **动资产前先 git 提交检查点**（根 `MEMORY.md` §8 有目录契约表）：
  报告/文档 → `Docs/<主题>/`；截图/日志/中转 FBX/导出 OBJ → `Saved/`（**不进 git**）；
  管线脚本 → `Scripts/`。**交付物严禁放 `Saved/`**（已二次复发，写报告前先看契约表）。
- **关卡基线 actor 只有 7 个**：`StaticMeshActor_1` / `DirectionalLight_0` / `RectLight_1` / `SkyLight_1` /
  `ExponentialHeightFog_0` / `PostProcessVolume_1` / `PlayerStart_0`。任何脚本跑完必须清理临时 actor 回到这个基线
  （用 `Scripts/axe_22_cleanup.py` 的清理模式）。临时 UE 资产也别留在 `Content/`（已 gitignore `Content/Temp/`）。

## UE 自动化（踩坑固化）
- **编辑器截图**：`HighResShot` 不可靠（静默失败、一次只认最后一条、落地延迟 1~4 分钟）。
  首选 **`SceneCapture2D` + `RenderingLibrary.export_render_target`**，输出是无扩展名 HDR，
  用 `ffmpeg -vf "zscale=t=linear,tonemap=hable,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"` 转 PNG 才能看。
- **`unreal.Rotator` 位置参数顺序 = (roll, pitch, yaw)**。一律用关键字参数。
- **socket 相对旋转组合顺序 = `World = Compose(Rel, Parent)`**（实测标定，与直觉相反）。
- **`MathLibrary` 缺 `invert_rotator` / `rotate_vector` / `quat_from_rotator` / `rotator_from_quat`**。
  需要逆旋转时用「坐标下降 + `compose_rotators` + `get_forward/right/up_vector`」纯数值求解（残差可到 1e-7）。
- **不要直接改组件的 `relative_location`**：会让组件脱离 socket 挂载。握持偏移写在 socket 上。
- `EditorAssetLibrary.unload_asset` 不存在；复核存盘值重新 `unreal.load_asset` 再读属性。
- `ue_remote.py` 是唯一可靠的编辑器执行网关：`uv run --no-project python Scripts/ue_remote.py <script.py>`。

## 资产关键契约
- 角色 `SK_Darius_GodKing`：309 骨，**7 个材质槽**（Slot 0 = 描边壳 Outline，Slot 7 原斧头槽已在 DCC 删除）。
  根骨骼 `darius_godking_mesh_LOD0_Skeleton` 带 **100× 米→厘米** 缩放。
- 武器 `SM_Darius_GodKing_Axe`：5668 顶点 / 1 section / 材质 `MI_Darius_Axe`，
  世界尺寸 **21 × 172 × 77 cm**，世界缩放 1.0。
  **UE 局部 +Y 端 = 大刃**（FBX 里是 −Y，符号翻转）。
- `hand_rSocket`（父骨 `hand_r`）：`relative_scale = (0.01,0.01,0.01)`，
  `relative_rotation = (-106.334, -70.982, 9.342)`，
  `relative_location = (0.18965, 0.10080, 0.00982)`（bone 空间，≈21.5cm 世界）。
  完整说明见 `AGENTS.md` §2.3 与 `Docs/Axe/Axe_Display_Fix_Report.html`。
- 源资产库：`E:\UE\Assets\Darius_God_king\God King Darius 2XKO.fbx`（含斧头对象 `.007`）；
  LOL 原版解包在 `E:\UE\Assets\Darius_GodKing_LOL_Original\`。

## 排查方法论（本项目的铁律）
「看起来被删了」和「被身体挡住了」在单张截图上无法区分。定位顺序固定为四步：
1. **顶点/面计数**（源 vs 导出 vs UE 三方对齐）
2. **材质链路**（混合模式 / 是否 Opaque / 有无 OpacityMask）
3. **同变换无遮挡对照**（把可疑对象单独摆到场里，用同一世界变换渲染）
4. **世界坐标核算**（UE 自己算关键点世界坐标，和骨骼坐标对照）

只有四步都排除后，才去动资产。

## 重定向管线（LOL 俯视角动画 → 2XKO 第三人称）
**最终计划（定稿，取代此前所有版本）：`Docs/Retarget/FINAL_Retarget_Plan.html`**
历史复盘：`Retarget_Attempt_Report.html`；两份外部方案评审：`LOL_to_TP_Retarget_Plan.html` / `Gemini_Plan_Review.html` / `Round2_Review_Recheck.html`

**定稿管线**：`DCC 净化 → UE IK Retargeter → Control Rig 运行时层 → 门禁验收`
**里程碑**：M0 尺子与基线(0.5d) → M1 垂直切片 idle+run 走通(3.5d) → M2 全量动作与风格(4d)，合计 8 天。

**去倾斜 = 速度连续偏置曲线（核心架构，不是逐动作离散常量）**
| 自变量 v (cm/s) | 躯干偏置 | 颈部偏置 |
|---|---|---|
| 0 (idle) | +5.2° | **+21°**（只还原 70%，保留睥睨气质） |
| v_run | −8.7° | −37.5° |
| v_fast | −32.3° | −46.0° |

- 颈部补偿 idle↔run **相差 67.4°**，离散常量 + 0.2s 淡化会造成肉眼可见的"折颈暴冲"；速度是连续量 ⇒ 偏置连续 ⇒ 根治。
- **必须在运行时层**（Control Rig/ABP Post-Process）的真正理由：自变量是**运行时速度**，离线烘焙会失去该自由度。
  ⚠️ 网上流传的"烘焙会抽搐、运行时层不会"**不成立**——淡化插值的是姿态，差 67° 就是 67°，与偏置来源无关；运行时层只多给了阻尼钩子。
- attack/spell/dance/recall **不做去倾斜**，只做生理限位软压缩（幅度保留 ≥85%）。
- 去倾斜到**绝对目标角**（在目标自身坐标系里），自动吸收「目标颈骨长 84%」造成的旋转放大。

**门禁（一票否决）**：G1 朝向(均值<8°/P90<20°/max<35°) · **G2 关节世界位置误差(中位<1.5%身高、P90<4%)** ·
**G3a 支撑相脚滑<2cm** · **G3b 动画隐含速度 vs MaxWalkSpeed 误差<5%** · G4 视线(只约束慢变基线 + 相对躯干偏置标准差<4°，
**禁止逐帧 |Pitch|≤5°** 硬约束) · G5 生理限位且幅度保留≥85% · **G6 融合平滑(角速度连续、峰值<600°/s)** · G7 双手握斧≤2cm+无穿模

**明确不做**：不用全局比例去倾斜 · 不烘焙去倾斜进 FBX · 不用逐帧头部硬约束 · 不把 2XKO 官方动画当前置 · 不引入 Cascadeur ·
**不做 root motion 提取**（源本就是 in-place）· 不手填补偿魔数（全部由实测反解）

**源侧契约（LOL skin15 神王，`Animations_GLB/standalone/*.glb`）**
- 179 骨，但身体形变链仅 ~30；必须**白名单裁剪**才能用（剔 `Lion_*` 四足 / `Throne|Gem|Piece_*` 王座道具 / `*Buffbone*` VFX 挂点）。
- 纯 FK 形变骨（无 twist / ik / ctrl）。
- **坑 1（方向勿搞反）**：膝/肘是**几何完全重合的孪生双骨**（head 坐标逐位相同）。实测 run 的 matrix_basis 漂移：
  `L_KneeUpper` 旋转恒 **0.000°**（只有 8.94 平移），`L_KneeLower` 旋转 **60.9°**（R 侧 103.5°）
  ⇒ **删 `*Upper`、保 `*Lower`**。反了会丢掉整条腿 60~103° 的膝弯。
- **坑 2（2026-09-18 实测更正）**：`L_Foot`/`L_Toe` 是 0.014 微骨。
  **踝关节 = `L_Foot.head`（z=16.93）**、趾 = `L_Toe.head`（z=8.05）；
  而 `L_KneeLower.tail` 的 z=**56.54**，**不是踝**（差 39.6 单位 ≈半条小腿，旧笔记写反了）。
  **`bone.tail` 与 `bone.length` 在 glTF 导入后一律不可信**（`L_Hip.tail` 指向 −Y 前方，真实髋→膝是 −Z 下方）
  ⇒ **关节真值只能取 `head_local`**。
- 30fps、in-place、46 个动作。实测帧数：run 0~35、run_fast 0~39、attack1 0~73、spell1 0~16、idle1 0~65；**没有 walk**。
- **俯视补偿的真相（实测，勿信"脊柱后仰"的流行说法）**：
  先锚定 forward = **−Y**（披风在 +Y、斧刃在 −Y）。相对 bind pose 的偏离：

  | 动作 | 躯干轴 | 颈段 | 头骨轴 |
  |---|---|---|---|
  | idle1/idle2 | **≈0°** | **−32°/−35°** | **−12°/−15°** |
  | run | **+34°** | +52° | +11° |
  | run_fast | **+62°** | +64° | +22° |

  ⇒ **后仰只发生在 `Neck` + `Head`（≈44°），脊柱零位移**；而 **run 家族是大幅前倾**（累计 86°~126°）。
  ⇒ 去倾斜必须逐动作反解：idle 只动 neck/head；run 家族动 spine(−15~−45°)+neck(−25~−55°)；attack/spell 不做去倾斜。**固定百分比权重（45/35/20/−60）是错的。**
- **身高**：目标网格 z 上限 **2.06 m**（不是 2.47 m）。
- **体型方向**：腿长/身高 LOL 0.5281 **>** 目标 0.5050 —— LOL 腿相对更长；真正的陷阱是**髋宽 −22%、颈长 +84%**。
- 风格：为俯视可读性**整体前倾 + 夸张幅度 + 两姿态** → 第三人称「不自然」的主因。

**目标侧契约（2XKO，`SK_Darius_GodKing`）**
- 309 骨；主干**兼容 UE Mannequin 命名** → UE IK Retargeter 自动映射可用。
- 24 根 twist 骨（源无对应，需程序化驱动）、~150 面部骨、`cape_chain_*`、辅助骨 `kneepad_jnt_*`/`ankle_front|back_jnt_*`/`shoulderpad_jnt_*`。

**比例补偿表（全局缩放 = 0.009883 = 1.8502/187.2095）**

| 度量 | 比值 | 相对全局偏差 | 对策 |
|---|---|---|---|
| 腿长/身高 | 0.0094 | −4.4% | Leg 链 Chain Scaling ≈ 0.951 |
| 上臂 / 前臂 | 0.0087 / 0.0114 | −12% / +15% | Arm 链关缩放，改 Rotation Offset |
| 髋宽 | 0.0077 | **−22%** | thigh 加 6°~8° 外展偏移（反解膝间距） |
| 颈长 | 0.0182 | **+84%** | spine 关缩放；neck 不重定向平移；head 下压偏移 |
| 臂长/身高 | 0.0099 | +0.1% | 无需处理 |

**M1-① 净化产物（2026-09-18 完成，可直接喂 UE IK Rig）**
- 文件 `Saved/Retarget/Clean/Darius_SrcClean.fbx`：**59 骨 / 46 动作 / 30fps / 25.26 MB**，bind pose 正确。
- 报告 `Docs/Retarget/M1-1_Source_Clean_Report.html`；主管线 `Scripts/plan_10_src_clean.py`。
- 保留链：`Root→Pelvis→{L/R_Hip→KneeLower→Foot→Toe}`、`Root→Spine1→Spine2→{Neck→Head→Jaw}`
  `→{L/R_Clavicle→Shoulder→Elbow→Hand→5×2 手指}`、`Root→Cape→(C|L|R)_Cape1~5`。
- **四层验收**：L1 结构 OK ｜ L2 会话内 46×3078 帧×27 关节（旋转偏差 **0.000000°**、位置 0.0135 单位）｜
  L3 **跨会话端到端**（关节间距相对差 **5.353e-07**、46/46 帧数一致、轨迹偏差 **7.130e-05**）｜
  **L4 UE 侧消费者验证**（导入产出 **48 资产** = 1 Skeleton + 1 Mesh + **46 AnimSequence**，帧数逐个对应）。
- 残留：`R_Foot` rest `matrix_local` 偏 2.68e-04（= 世界 0.135mm，G2 阈值的 1/214，已接受）。

**UE 侧契约（本产物导入 UE 后实测）**
- 骨架 **60 骨**（Blender 读 FBX 是 59）：多出的 1 根是 Blender `armature_nodetype='NULL'`
  造的 NULL 根节点被 UE 当成骨，在原点、单位变换，**不引入偏移** ⇒ 建 IK Rig 时忽略最外层。
- action 名带前缀 `SrcCleanskinned_mesh_darius_skin15_*`（= UE destination_name + Blender
  armature 对象名 + action 名），正式导入时统一重命名。
- 帧数换算：`sequence_length`(秒) × 30 + 1 = 帧数（attack1 2.4333s → 74 帧）。

**🔴 DCC / 网关侧三条硬坑（已写入 `AGENTS.md` §5）**
1. **FBX 导出前必须复位 rest pose，且必须用 `bake_anim_use_all_actions=True` 单文件多 take 导出。**
   `plan_17` 探针三选一实测：挂 action 导出 **5.843e-02 BROKEN** ／ 清 pose + `all_actions=False`
   1.198e-07 但**只含 1 个动画** ／ 清 pose + `all_actions=True` **1.198e-07 且 46 个动画全保真**。
   ⇒ **逐 action 导出无法保证 bind pose，只能选第三种。**
   **`blender_51_retarget_v4.py` / `blender_30` / `blender_50` / `blender_10` 四个脚本已于
   2026-09-18 全部修复**；输出契约变为**单文件多 take**（`A_Darius_All_TP.fbx`，UE 一次导入即建全部 AnimSequence）。
   `plan_16` 审计：`Saved/Retarget/` 旧产物 17 个中 **15 个 BROKEN**（关节间距偏差最高 **15.4%**，
   TurnL/TurnR 最差）⇒ **`Batch/` 与 `V4/` 下的旧产物已废弃，勿再导入 UE**；
   修复后产物见 `Saved/Retarget/V5/`（实测 **5.926e-07** OK）。
   新增审计工具：`plan_16_audit_fbx.py`（批量扫目录给 OK/WARN/BROKEN）、
   `plan_17_export_probe.py`（改导出逻辑前先跑，3 分钟定死正确做法）。
2. **改 `edit_bone.parent` 会触发 `Bone.matrix_local` 重建**，对短骨有数值损失。
   删骨后要用快照写回 `head/tail/roll`，且**先用两趟循环把全部 `use_connect=False` 再写**
   （否则设父骨 tail 时会拉走子骨 head）。
3. **纯骨架 FBX 在 UE 侧产出 0 资产**（不报错）。UE 需要至少一个 SkeletalMesh 作骨架载体 ⇒
   导出时保留源网格（清空材质槽 + 删失效顶点组），选择集 = armature + 网格。
4. **`ue_remote.py` 的 `.py` 字样陷阱**（已在网关修复）：传「内容」时 UE 会嗅探 `xxx.py`
   并误判为路径 ⇒ 脚本 docstring/注释里写自己的文件名就**静默不执行**。
   已改为落盘后传路径、失败回退传内容。

**UE 侧 IK Rig / Retargeter 契约（2026-09-18 打通，`/Game/Character/Darius/Retarget/`）**
- `IK_LOL_Source`（59 骨 / 9 链 / root=`Root`）· `IK_Darius_Target`（309 骨 / 29 链 / root=`pelvis`）
  · `RTG_LOL_to_Darius`（5 个默认 op，**9/9 链已映射**）
- 源链：`Spine: Spine1→Spine2` · `Neck: Neck→Neck` · `Head: Head→Head` ·
  `Left/RightLeg: L/R_Hip→L/R_Foot` · `Left/RightClavicle: L/R_Clavicle→自身` ·
  `Left/RightArm: L/R_Shoulder→L/R_Hand`
- 🔴 **UE 5.8 的 Retargeter 是 Op Stack 架构**：必须先 `ctrl.add_default_ops()`，
  否则 `auto_map_chains` **静默不生效**（返回 None、映射 0，不报错）。旧属性
  `chain_settings`/`global_settings`/`root_settings`/`chain_map` 全废弃。
- API 签名：`add_retarget_chain(name, start, end, goal_name)`（4 参）·
  `set_ik_rig(source_or_target, rig)`（**枚举在前**）· `auto_map_chains(type, force_remap)`（2 参）·
  批量用 `IKRetargetBatchOperation.run_batch_retarget(inputs)`。
- 🔴 **`list_assets()` 返回 `package.object`**，而 `find_asset_data`/`rename_asset` 要**纯 package 路径**。
  混用会让编辑器 **EXCEPTION_ACCESS_VIOLATION 崩溃**。一律 `pkg = a.split(".")[0]`。
  且 `rename_asset` **未 save 会回退** ⇒ 不改源资产名，输出名用 batch inputs 的 `search`/`replace`。

**验证器两条硬规矩**：① **跨会话**比对（源与产物各导入一次），同进程自比发现不了导出/导入损失；
② 标尺用**固定骨集合 + 只用 `head`**（用「全部骨」会因道具骨 `Gem`(z=836)/`Axe_Handle`(z=−90.8)
算出 927 的荒谬身高，两侧骨集合不同时还会得出 2.36 倍的假缩放因子）。优先用**缩放不变量**（关节间距）作判据。

**工具选型**
- 主力：**UE5 IK Retargeter**（Retarget Pose / Chain Scaling / Stride Warping / Speed Planting）。
  经验法则：FK Translation Mode 用 **Globally Scaled**；腿链**只到踝不到 ball**、Chain Depth=2；Pelvis 的 Blend to Source Translation=1.0 但 **Z 权重设 0**。
- 源侧保真：**Aventurine: League Tools**（Blender 4.0+，原生 .anm + LoL Retarget + Wiggle2 物理；本机 Blender 5.2 兼容性待验）。
- 动作清理：**Cascadeur**（AutoPhysics / fulcrum 脚锁 / Unbaking；免费档限 120 关节，只能用在裁剪后的源骨架上）。
- 降维打击：**2XKO 本体可解包（UE5.4）**，Darius 官方第三人称动画真实存在（`darius_base_nav_std_*`）→ locomotion 用它可零重定向误差。

**验收指标（比「朝向误差」更贴近「自然」）**
V1 朝向误差均值 <8° / 最大 <30°；**V2 关节世界位置误差 中位 <1.5%身高、P90 <4%**；
**V3 支撑相足漂移 <2cm**；**V4 隐含速度 vs MaxWalkSpeed 误差 <5%**；V5 Idle 躯干前倾 2°~6°；V6 生理限位且幅度保留 ≥75%。
