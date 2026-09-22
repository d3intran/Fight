# Fight 项目长期硬约束 (MEMORY.md)

> 全景契约见 `AGENTS.md`；手感调优见 `Docs/Locomotion/`；每日日志见 `memory/YYYY-MM-DD.md`。
> 本文件只存**不遵守必返工、不看必踩坑**的长期硬约束。

## 1. 运行环境与执行通道
- Python 一律 `uv run --no-project python`；JS/TS 一律 `deno`。
- UE 远程命令一律走 `Scripts/ue_remote.py`（唯一网关）。编辑器启停用 `deno task editor:up -- --hold`。
- 编辑器是否在线：UDP 6766 广播自动发现，无实例时脚本会直接报「未发现实例」。
- 关卡基线 **7 个 Actor**：跑完测试必须用 `loco_05_cleanup.py` / `plan_99_clean_temp.py` 复位。

## 2. 核心资产物理与几何契约（严禁破坏）
- **`SK_Darius_GodKing`**：310 骨骼；最外层 `scale=100`；`pelvis` 局部平移基线 `1.0967`。
- **战斧 Socket**：`hand_rSocket` 缩放必须为 **`0.01`**（抵消外层 100×）；局部 `+Y` 为大刃。
- **Section 0 描边壳**：为反向法线整模复制品，披风面与战斧几何已从 DCC 彻底剥离（材质隐藏无效）。
- **披风布料**：`CA_Darius_Cape` 绑定 Section 1；固定组名必须为纯文本 `SimVertices3D`，权重映射 `MaxDistance`。
- **移动动力学真值**：CMC `MaxWalkSpeed=220` / `MaxAcceleration=1000` / `BrakingDecelerationWalking=1400` / `GroundFriction=6.0`；
  `SpringArm` `ArmLength=380` `SocketOffset=(0,45,20)` `TargetOffset=(0,0,50)` `CameraLag=9` `RotLag=12`；
  `PlayerStart` pitch `-12.0°`。
- **⚠️ 2026-09-22 起 `BS_Darius_Locomotion` 已换成 LoL 线**（不再是 M1 的 Mixamo 配置）：
  Speed 轴 `[0,**440**]`，样本 `0→A_Darius_idle1` / `220→A_Darius_run` / `440→A_Darius_run_fast`
  （Direction −180/0/+180 各一份）。原 Mixamo 版（含 `RateScale=1.48`）已备份为 **`BS_Darius_Locomotion_M1_Mixamo`**。
  按住 Shift 走 `IA_Sprint`（Boolean，`IMC_Default` 绑 `LeftShift`）把 `MaxWalkSpeed` 220 → **440**。
  `ABP_Darius_Test` 的 **Idle 状态**序列也已换成 `A_Darius_idle1`（Jump/Fall/Land 三条未动）。
- **scale=100 契约治理（2026-09-21，完整账本 `AGENTS.md §2.4`）**：
  - **唯一载体** = 骨架最外层骨 `darius_godking_mesh_LOD0_Skeleton`（scale **100**、位置恒 0）；
    其余全骨 rest 局部平移是**米级**（pelvis ≈ 1.0967），网格顶点是 **cm 级**（bounds 全高 **202.4cm**）。世界 = 局部 × 100。
  - **常量源** `Scripts/core/fight_scale.py`（`OUTER_BONE`/`OUTER_SCALE`/`cm_to_local()`/`SOCKET_SCALE`）。
    **禁止再写裸 `100` / `0.01` / `1.0967`。**
  - **门禁** `Scripts/core/scale_audit.py`（只读，输出 `VERDICT: PASS/FAIL`）：最外层骨轨道 + `hand_rSocket` 缩放 + 活性检查
    （多骨 × 真实帧长、跨帧最大旋转差 <0.5° 判疑似静止）。**每批重定向产物落盘后必跑。**
  - **不消灭这个 100 的理由**：「最外层骨 scale→1 + 其余局部平移 ×100」数学上世界等价
    （bind matrix 由 Skeleton rest 实时算出、不烘在网格里；引擎内可用 `SkeletonModifier` 实施），
    但代价 = 60 条动画重写 + 布料/物理重标定 + M1 全量重验收 ⇒ 风险收益比不成立。
    **真要动，先复制骨架+网格+2 条动画做副本验证，不要直接上主资产。**
  - 只读探针：`Scripts/retarget/rtg_60_scale_anatomy.py`、`rtg_63_evidence.py`。

## 3. 动画与分层合并
- 上下半身合并走 UE 骨骼轨道改写（`AnimationDataController`），不走 Blender。
- 必须校验腿-臂摆动相位（一阶谐波，自然走路 ≈180°，合并产物已过 185.3°）。
- `AnimationLibrary.get_raw_track_data` 对压缩动画返回空 ⇒ 一次性获取必须用 `get_bone_poses_for_frame`。
- 动画改写三铁律：改完必须验数值 + 验是否在动；改写前先备份；严禁在 slate post-tick 回调里 `destroy_actor`。

## 4. 动画/重定向验证铁律（2026-09-21 血亏换来）
- 🔴 **远程脚本严禁「spawn Actor + destroy Actor + 后续可能抛异常」的组合**。实测：先 `destroy_actor(×3)` 再
  `spawn_actor_from_class(SkeletalMeshActor)` 并在后面抛 `AttributeError`，17 秒后编辑器 `EXCEPTION_ACCESS_VIOLATION`。
  **验证一律用纯求值路线，不生成任何 Actor。**
- ✅ 纯求值正解：`AnimPoseExtensions.get_anim_pose_at_frame(anim, frame, AnimPoseEvaluationOptions())`
  → `get_bone_pose(pose, name, AnimPoseSpaces.WORLD)`。
- ⚠️ **空间单位陷阱**：`get_bone_pose_for_frame` 返回**父级相对(local)**，
  单位是**米**（`hand_r` 局部平移 0.34 = 34cm）；而 `AnimPoseSpaces.WORLD` 的平移读数是 **cm**
  （pelvis X 轴长 20.48 = 20.5cm 髋宽）。**两者差 100×，写轨时必须 ×0.01**
  （`wp_75` 第一版漏了这一步，`root` Z 被抬到 4310cm = 43m）。跨骨架比数字前先确认量纲。
- ⚠️ 骨架「前方」基准（pelvis 局部 X 轴在世界空间的方向）：目标 `SK_Darius_GodKing` = **`(0,−1,0)`**、
  源 `SK_LOL_Darius` = **`+X`**。判「角色朝哪」用这条轴，**别用脚尖**（会被脚型/站姿污染）。
- ⚠️ **披风是纯 Chaos Cloth 模拟**：27 根 `cape_chain_01..09_{l,m,r}` 在**所有**动画里
  跨帧旋转差都是 0.00°（含原生与 Mixamo 线）⇒ 动画不驱动它，Persona 预览不跑解算时看起来穿地是正常的。
- ⚠️ **LoL 的 run 系素材整体下沉**（俯视角素材，高度基准与 UE 地面不一致）：
  `run` 穿地 43cm、`run_fast` 穿地 52~89cm、`run_homeguard` 43cm。修法 = 给 `root` 加恒定 Z 偏移
  （`Scripts/anim/wp_75_lift_root.py`，已 apply）。就"平地走"而言 **`run_homeguard` 最合适**
  （pelvis 跨度仅 16cm，`run` 是 31cm 会显得"跳"）。
- ⚠️ **RTG API 正确名字**：op 栈 `get_num_retarget_ops()` + `get_op_name(i)`（**没有** `get_retarget_op_at_index`）；
  预览网格 `get_preview_mesh(side)`；参考姿态 `IKRigController.get_ref_pose_transform_of_bone`。
- ⚠️ **LoL 源动画整体带 180° yaw**：源 ref pose 脚尖朝 `+Y`，源 idle1 动画脚尖朝 `-Y`。
  **任何「用 ref pose 判朝向/左右/镜像」的结论都是错的**；RTG 的 retarget pose 若 reset 成 ref pose，基准就差 180°。
- ⚠️ 产物必须 `EditorAssetLibrary.save_asset` 落盘；崩溃后可从 `Saved/Autosaves/Game/...` 复制同名 `.uasset` 回 `Content/` 抢救。

## 5. RTG 重定向：定稿配方与「单旋钮无用」结论
- **骨架「前方」基准（2026-09-22 实测，pelvis 局部 X 轴在世界空间的方向）**：
  目标 `SK_Darius_GodKing` = **`(0, −1, 0)`**（原生 jump/walk 系 + Mixamo 线四者完全一致）；
  源 `SK_LOL_Darius` = **`+X`**。**判断「角色朝哪」一律用这条轴，不要用脚尖**（会被脚型/站姿污染）。
- 🔴 **`mirror` 配方的副作用：整体朝向多转 180°**。源 Root 的「世界 yaw180」在修左右镜像的同时
  把整体朝向也转了 ⇒ LoL 线产物朝 `+Y`（背对玩家），而原生/Mixamo 线朝 `−Y`。
  修法 = **事后在产物上补反向旋转**（`Scripts/anim/wp_72_fix_facing.py`）：
  给 `root` 写恒定轨 `q_new = Q_outer_rest⁻¹ ∘ Rz180 ∘ Q_outer_rest ∘ q_root_old`
  （`Q_outer_rest` 实测为单位阵 ⇒ off 就是 Rz180；root 的父是最外层骨、位置 0 ⇒ 绕脚下转，脚不离地）。
  ⚠️ **不要直接改 mirror 配方**：会牵动已验收的 `lr_score` / `hand_score`，要全面重验。
- 验收三件套（世界空间，`Scripts/retarget/rtg_20_fix_verify.py`，mode 写在 `Saved/Attack/rtg_fix_mode.txt`）：
  ① 脚尖朝向与源同向；② `lr_score`（= `dot(foot_l−foot_r, Z×forward)`，朝向无关）与源同号；
  ③ 脚位移幅度与源同量级。源基线 run：脚尖 dot(−Y)=0.766、`lr_score`=+20.95、L 位移 87.74cm。
- **已逐一证伪的旋钮**：`TargetRootSettings.rotation_offset=yaw180`（被 FK op 覆盖）、
  `Pelvis Motion.rotation_offset_global=yaw180`（只挪位置）、关闭 `Run IK Rig`、FK 全链 `ONE_TO_ONE`、
  `auto_align_all_bones(SOURCE, CHAIN_TO_CHAIN)`（只对齐方向，仍 170°）。
- **唯一有效杠杆 = 源 retarget-pose 的朝向**，且**必须两个旋钮合用**（mode=`mirror`）：
  1. **源 `Root` 施加「世界空间 yaw 180°」的局部化偏移** `off = qconj(R_root_refWorld) * (Rz180 * R_root_refWorld)`。
     ⚠️ 直接写 `Rotator(0,180,0)` 会因骨局部轴不齐把角色掀翻（实测 `pelvis_z=−237cm`）；**必须先共轭**。
  2. **全身左右链交叉映射**（腿/脚/臂/锁骨/手指共 26 条）：`Target[LeftLeg] ← Source[RightLeg]` …
  效果：`lr_score` −62 → **+28.6**（与源 +20.95 同号 ✓）、`hand_score` **−44.5**（与源 −52.0 同号 ✓）、
  脚位移 93.09cm ✓、`pelvis_z` 76.3cm（不翻）✓。
- ⚠️ **判朝向别用「单只脚 foot_l 的脚尖」**（交叉映射后该骨由源的另一只脚驱动，指标被污染）。
  可信指标 = `hand_score`（斧手侧）+ 对应脚的脚尖，同号。
- ⚠️ 每次试验前必须把**两侧**（SOURCE 的 `Root`/`Pelvis` + TARGET 的 `root`/`pelvis`）姿态偏移**一起归零**，
  否则上一轮残留会污染下一轮（同一 mode 跑出两套数字）。
- **不要用 `mode=none` 看现状**（会触发基线卫生、抹掉修复）；看现状用只读的 `rtg_31_state_dump.py`。
- 备份 `Saved/Attack/backup_20260921_1740/`；快照 `Saved/Attack/rtg_state_after_fix.json`。
- 完整记录：`Docs/Retarget/RTG_LOL_To_Darius_修复记录_2026-09-21.md`。

### 🔴 RTG 导出后必须紧跟的后处理：删最外层骨的假 scale 轨
- 重定向产物 = **310 轨**，最外层骨被写了一条 **scale = 1**；正常动画只有 309 轨、该骨回落 rest（**100**）。
- 后果：角色渲染成 **1.85cm**（"人物贼小"）+ Cloth 约束距离按 100× 写死 ⇒ **披风被撑爆**。
- 修法：`anim.get_editor_property("controller").remove_bone_track(骨名)` 整条删掉。
  **严禁** legacy 的 `AnimationLibrary.remove_bone_animation`（会把整段动画清成静止）。
  验证必须**同时**验 scale==100 与「不同姿态>1」。脚本 `Scripts/retarget/rtg_41_fix_outer_scale.py`（幂等）。
- 🔴 **骨名列表必须取 `data_model_interface`**：`get_editor_property("model_interface").get_bone_track_names()`
  **不含最外层骨** ⇒ 用整名匹配会一条都删不掉（2026-09-22 实测「删掉假轨 0 条」）。
  正解 = `get_editor_property("data_model_interface").get_bone_track_names()` + 子串 `"lod0_skeleton"` 匹配。
- ⚠️ 每次用 Retargeter 的 "Export Selected Animations" 或任何批量重定向后，**都必须再跑一遍**。
  批量导出 + 修轨已合成一步：`Scripts/anim/wp_60_batch_retarget_all.py`
  （`LOL_Source/` 46 条 → `Animations/LOL_Retarget/`，`A_LOL_Darius_x` → `A_Darius_x`）。
  ⚠️ `turn0/turn_l/turn_r` 是源里的**空片段**（无骨骼数据），重定向后「不同姿态=1」属正常，不是失败。
- ⚠️ **远程脚本日志别用 `| head -N`**：SIGPIPE 会杀掉正在执行的脚本，后半段（落盘）静默不跑。
  重定向到文件再 `tail`。

## 6. 武器（战斧）挂点 —— 2026-09-21 定论
- **骨架自带三个锚点**：`weapon_jnt`（父 **`root`**）/ `weapon_jnt_r`（父 `hand_r`）/ `weapon_jnt_l`（父 **`hand_l`**）。
- 🔴 **l/r 命名与解剖左右相反**（2026-09-21 髋轴投影实测，idle 静止帧）：`hand_l` 在解剖**右**（+45.3）、
  `hand_r` 在解剖**左**（−51.3）；源 `R_Hand` +48.4 / `Weapon` +41.0（解剖右，自证）。
  **禁止靠命名判侧别。**
- **源层级** `Axe_Head ← Weapon ← R_Hand` ⇒ 与源同构的锚点是 **`weapon_jnt_l`**（父 `hand_l` = 解剖右）。
  ⚠️ 此前选 `weapon_jnt_r` 是错的；且斧头原挂 `hand_rSocket`（父 `hand_r`）= 解剖左手，**一直与源相反**。
- 🔴 **已知 bug**：`clean_weapon_chains.py` 把 IK_Darius 的 Weapon 链建在 **`weapon_jnt`**（父 `root`）上，
  而源 `Weapon` 挂 `R_Hand`。层级不对称 ⇒ 产物里 `weapon_jnt` 轨恒定、锚点钉在脚下（离 `hand_r` 108cm）。
  ⇒ 已改为 `weapon_jnt_l`（`Scripts/anim/wp_41_repoint_weapon_chain.py`，备份 `backup_20260921_234112/`）。
- 🔴 **RTG 的 FK op 的 `chains_to_retarget` 不含 Weapon 链** ⇒ 改链后重跑，`weapon_jnt_l`
  **平移与旋转全为 0（完全没被驱动）**，连原来的 `weapon_jnt` 也不写了。
  `rtg_20_fix_verify.py` 只设链映射、不动 FK 链列表。
- ✅ **握法改走离线烘焙，绕开 RTG**（`Scripts/anim/wp_50_bake_weapon_grip.py`）：
  `L_grip(t)=W_R_Hand_src(t)⁻¹∘W_Weapon_src(t)`；`K=(R_hand_l_tgt(t₀)⁻¹∘R_R_Hand_src(t₀), 平移置零, scale 0.01)`；
  写 `L_raw(t)=K∘L_grip(t)` 进 `weapon_jnt_l` 局部轨。
  验收硬指标：`|L_raw(t0)|` 必须等于源 `Weapon↔R_Hand` 距离（17.37/19.51/12.63 cm，实测逐一吻合）。
  🔴 **两个必踩坑**：① `K` 的**平移必须置零**（否则 root 绝对位置差 0.2~1.3m 会灌进锚点）；
  ② **重写前必须 `remove_bone_track`**（否则读到上次烘焙值 ⇒ 复合污染）。
- BP 侧 `WeaponAxe` 相对变换 = 「axe mesh 相对武器骨」的固定偏移：
  `loc=(0,-0.8383,0.1249)`（源 `Axe_Head` 相对 `Weapon` 84.76cm×0.01）、`rot=单位阵`、`scale=0.01`。
- 🖐️ **Parent Socket 确实无 Python API**（`wp_52` 实测 `AttachSocketName` 写不进）⇒ 只能手点；用户已改好并保存在 BP。⚠️ 经 SubobjectData 读 BP 组件可能拿到 **CDO 旧值**（未重编译时），与 PIE/uasset 矛盾时以后者为权威。
- **源是右手武器**（44/46 条 `Weapon` 离 `R_Hand` 更近；仅 `death`(已脱手) 与 `joke_loop` 模糊）。
- **源里握法是动画数据**：46 条片段 **17 条刚性**（idle/walk/run/turn，0.000cm/0.000°）、**29 条有漂移**
  （attack1 42cm/82°、attack2 46cm/90°、spell4_5 54.8cm/140°、death **404cm/179.8°**）。
  ⇒ 只挂 `hand_rSocket` **对这 29 条有损**（攻击发僵），移动类无损。
- ⚠️ **单骨链**（start=end）的 `Direction`/`CHAIN_TO_CHAIN` **从原理上定不出方向**（同 hand/foot 坑），
  retarget pose 必须 `Align Selected` 或视口手转 —— 这也是最终放弃 RTG 驱动、改走离线烘焙的原因。
- 门禁：`Scripts/anim/wp_40_weapon_anchor_recon.py`（只读裁决）、`wp_20_weapon_audit.py`（契约一键门禁）、
  `wp_09_check_weapon_tracks.py`（逐条轨 & 局部平移行程）、`dot`：`Scripts/retarget/rtg_30_weapon_scan.py`（源刚性扫描）。
- 方案文档：`Docs/Attack/斧头挂点修复_weapon_jnt_r_方案.md`。

## 7. 手指骨骼真相（Blender 直查原始 GLB）
- LoL 原版每指只有 **2 节骨、无掌骨**（GLB 179 骨，20 根手指骨直接挂 `L_Hand`/`R_Hand`）。
  ⇒ **源 2 节 → 目标 3 节**的插值分布是**源资产的天花板**，不是管线 bug；净化白名单没删过手指骨。
- 目标每指 4 槽位（`*_metacarpal_l/r` + `*_01/02/03_l/r`，拇指 3 节无掌骨），共 38 根。
- **已修**：源 rig 补 `LeftMiddle`/`RightMiddle` 两条链（39→41）；中指活动量 104–112° → **142–161°**。
- **8 个掌骨（每手 4）无法 1:1 重定向**（源无对应骨）⇒ 保持冻结在参考姿态；近似驱动风险高，勿轻易做。
- 探针：`Scripts/dcc/blender_50_finger_probe.py`、`Scripts/retarget/rtg_50_finger_audit.py`。

## 8. M1 收尾与下一步
- ✅ 武器锚点已收尾（§6）；✅ LoL 动画已接进游戏：Idle → `A_Darius_idle1`、WASD → `A_Darius_run`、
  Shift → `A_Darius_run_fast`（详见 §2 与当日日志）。
- 遗留调优点（不是 bug）：`run`/`run_fast` 的 `RateScale` 尚未与移动速度对齐（脚滑）；
  LoL 素材是**前向原地跑、无方向变体** ⇒ 横移/后退会滑步。
- 下一步：启动 C++ 战斗框架 —— `AFightCharacter`（输入缓冲）→ `UFightMovementComponent`（闪避/冲刺）
  → 命中扫掠（Hitbox Sweep）→ 顿帧与受击反馈（Hit Stop / Bleed）。

## 9. 引擎内改「蓝图图 / 动画图 / BlendSpace / 输入资产」配方（2026-09-22 实测）

### 9.1 通道选择
- 🔴 **不要用 `write_graph_dsl`**。`read_graph_dsl` **不 dump `EnhancedInputAction` 事件的 exec 链**
  （实测 `IA_Move.Triggered` 确实连着 `Move` 函数、`ActionValue_X/Y` 也连着，但 DSL 里那条事件是**空续体**）
  ⇒ 回写「读出来的东西」必丢线。**DSL 也不能用来判断"有没有连线"**。
- ✅ **正解 = 原子操作**：`create_node` → `connect_pins` → `set_pin_value` → `compile_blueprint`。
  验证连线**只能**靠 `get_node_infos` 读 `pin.connected_pins`。
- 入口：`Scripts/anim/mcp.py`（`tools` / `describe` / `call` / `topcall`）；`Scripts/ue_mcp.py` 自带 `init()` 握手与 `batch` 模式。
  ⚠️**自写 HTTP 客户端漏掉 `initialize` 会 400**。

### 9.2 实测 type_id / 引脚
| 需求 | `type_id` | 引脚 |
|---|---|---|
| EnhancedInput 事件（已有 IA） | `Input\|EnhancedActionEvents\|<IA名>` | 出：`Triggered`/`Started`/`Ongoing`/`Canceled`/`Completed`/`ActionValue`/… |
| 取移动组件 | `Variables\|Character\|GetCharacterMovement` | 出：`CharacterMovement` |
| 设移动速度 | `Class\|CharacterMovementComponent\|SetMaxWalkSpeed` | 入：`execute`/`MaxWalkSpeed`/`self`；出：`then` |

### 9.3 读图 / 改动画图
- 列图：`BlueprintEditorLibrary.list_graph_names / list_graphs / find_graph(bp, "EventGraph")`。
  ❌ `bp.get_editor_property("UbergraphPages"/"FunctionGraphs"/"AnimGraph")` **全部失败**。
- **动画图节点**：`AnimationLibrary.get_nodes_of_class(abp, unreal.AnimGraphNode_SequencePlayer)`
  → `get_editor_property("node")` → `set_editor_property("sequence", anim)` → 写回 `n.set_editor_property("node", sub)`
  → `BlueprintEditorLibrary.compile_blueprint(abp)` + `save_loaded_asset`。**实测有效**（`wp_86`）。
- 改图节点必须在**编辑器内**发生；改完 `compile_blueprint` 后还要 `EditorAssetLibrary.save_loaded_asset`。

### 9.4 BlendSpace 可编程
- 轴：`bs.get_editor_property("blend_parameters")` → `BlendParameter` 可写 `min`/`max`/`display_name`/`grid_num`。
- 样本：`unreal.BlendSample()` + `set_editor_property("animation"/"sample_value"(Vector)/"rate_scale")`，
  整体 `set_editor_property("sample_data", [...])`。
- **ABP 引用的是资产对象 ⇒ 只换 BS 内容就够，不用动 ABP 图**。

### 9.5 Enhanced Input 可编程
- 工厂类名**带下划线**：`unreal.InputAction_Factory` / `unreal.InputMappingContext_Factory`
  （`InputActionFactory` / `InputActionFactoryNew` **都不存在**）。
- IMC 映射：`imc.get_editor_property("default_key_mappings").get_editor_property("mappings")`
  （旧的 `mappings` 属性已废弃且读出来是空数组）。追加 `unreal.EnhancedActionKeyMapping()`。
- 🔴 **`unreal.Key()` 只能零参构造**（传字符串会 `TypeError: call() takes at most 0 arguments`）
  ⇒ 从已有 mapping 借一个 FKey struct，改 `key_name` 再用。
- ⚠️ **新建的 IA 不会立刻出现在 BP 的 `EnhancedActionEvents` 列表**（`find_node_types` 仍只有旧的），
  但 `create_node` 直接传 `Input|EnhancedActionEvents|<IA名>` **能建成**（`wp_90` 实测）。
  重扫资产注册表 + 重编译都刷不出缓存；未找到刷新办法。

### 9.6 本轮脚本索引
`wp_80`(资产普查) `wp_81/82`(ABP 结构探针) `wp_83`(BS 可写性) `wp_85`(BS 换 LoL) `wp_86`(ABP Idle 序列)
`wp_87`(输入探针) `wp_88`(IA_Sprint + IMC 绑定) `wp_90`(BP 图接 Sprint) `wp_91/92/93`(复验/接线检查/落盘)。
备份：`BS_Darius_Locomotion_M1_Mixamo` + `Saved/Attack/backup_20260922_002956/`。

## 10. 落地高度 与 披风碰撞体（2026-09-22 血亏换来）

### 10.1 「浮空 / 跳动」的判据与修法
- **判据 = 支撑脚**（每帧两脚中较低者，逐帧全采样，`wp_94_loco_profile.py`）。基准锚点：
  `A_Darius_Walk_Layered` 支撑脚 **10.45 ~ 22.51**（中位 14.24），idle1 **10.06 ~ 10.66**。
- 🔴 **恒定抬升绝不能按「全程最低点归零」**（`wp_75` 的错）：最低点往往只出现在一帧，
  把它归零 = 其余所有帧整体抬高 ⇒ **浮空 30cm+**。要按**支撑脚的典型值/分位**对齐。
- 🔴 **源 LoL 素材本身腿是正常的**（支撑脚 4.74~27.80），**是重定向把腿摆放大 2.7×**
  （脚相对 pelvis 最高点 −43.05 → −20.92，最低点一致）。**别把锅甩给素材。**
- ✅ 修法 `Scripts/anim/wp_97_ground_fix.py`（只动 root/pelvis 平移，不碰旋转）：
  ① 压骨盆起伏 `p_new = p_med + (p_old−p_med)×K`（K=0.70，因为腿是 pelvis 子链，脚高可**纯计算**）；
  ② 逐帧支撑脚吸附 `off(t) = −max(0, smooth(sup(t)) − CEIL)`（CEIL=20，循环移动平均 5 帧，只往下拉）。
  效果：支撑脚中位 41.72→**21.38**、pelvis 峰峰 33.90→**14.73**。模式 `Saved/Attack/wp97_mode.txt`。
- ⚠️ 重定向放大 2.7× 这条**根因尚未修**（要压腿骨旋转或改 RTG 腿链 rotation mode 后重导 46 条）。

### 10.2 披风碰撞体：`SK_Darius_GodKing_Physics`
- `CA_Darius_Cape.physics_asset` = **`SK_Darius_GodKing_Physics`** ⇒ **布料穿模就查这个资产**。
- 🔴 **原来只有 12 个球，球心几乎都在骨骼原点**（pelvis 0.15 / spine_01~03 0.16~0.18 /
  neck 0.10 / head 0.13 / clavicle 0.12 / thigh 0.14 / calf 0.11），
  **`upperarm`/`lowerarm`/`hand`/`foot` 连 body 都没有**。
  骨长实测 **thigh 44.96 / calf 48.71 / upperarm 35.43 / lowerarm 34.01 cm**
  ⇒ 球只能盖长骨的中间，**两端 8~13cm 是空的**，披风从空隙穿过。
- 🔴 **单位 = 骨骼局部「米」**（和 pelvis 局部 1.0967 同一套）。toolset 文档写 cm，实测不是。
- 🔴 **所有骨的「沿骨方向」= 局部 Y**（`wp_100_pa_axis.py` 实测 dot = −1.000）。
- ✅ 修法 `Scripts/anim/wp_101_pa_capsules.py`（本机跑，走 MCP `PhysicsAssetToolset`）：
  删 `col_sphere` → `SetCapsule(radius, length, center=(0, **−骨长/2**, 0), rotation.roll = **−90**)`。
  - `SetCapsule` 的**胶囊长轴 = 应用 rotation 后的局部 Z** ⇒ 用 `roll=−90` 把 Z 转到 Y。
  - **center.y 是负的**（骨方向为局部 −Y）——别照抄 pelvis 那类正值。
- **API**：`GetBodyNames(physicsAsset)` / `GetBodyShapes(physicsAsset, boneName)` /
  `SetSphere` / `SetCapsule` / `RemoveShape` / `AddBody`（toolset = `PhysicsToolsets.PhysicsAssetToolset`）。
  改完记得 `EditorAssetLibrary.save_loaded_asset`，且 **PIE 要重启才读到新碰撞**。
- **PIE 自动化**：`EditorToolset.EditorAppToolset` 有 `StartPIE` / `StopPIE` / `IsPIERunning` /
  `CaptureEditorImage` / `CaptureViewport`（后者 `captureTransform`、`annotations` **都必填**）。
  `PlayerStart` 在 `(0,0,170)` pitch −12。⚠️ 窗口最小化时 `CaptureEditorImage` 报
  `Failed to capture any editor windows`。
