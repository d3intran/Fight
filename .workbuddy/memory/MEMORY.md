# Fight 项目长期硬约束 (MEMORY.md)

> 全景契约见 `AGENTS.md`；手感调优见 `Docs/Locomotion/`；每日日志见 `memory/YYYY-MM-DD.md`。
> 本文件只存**不遵守必返工、不看必踩坑**的长期硬约束。

## 1. 运行环境与执行通道
- Python 一律 `uv run --no-project python`；JS/TS 一律 `deno`。
- UE 远程命令一律走 `Scripts/ue_remote.py`（唯一网关，严禁在脚本 docstring 出现 `xxx.py` 字样）。
- 编辑器启停必须用 `deno task editor:up -- --hold`（停任务 = 杀进程）。
- 关卡基线 **7 个 Actor**：跑完测试必须用 `loco_05_cleanup.py` / `plan_99_clean_temp.py` 复位。

## 2. 核心资产物理与几何契约（严禁破坏）
- **`SK_Darius_GodKing`**：310 骨骼；最外层 `scale=100`；`pelvis` 局部平移基线 `1.0967`。
- **战斧 Socket**：`hand_rSocket` 缩放必须为 **`0.01`**（抵消外层 100x）；局部 `+Y` 为大刃。
- **Section 0 描边壳**：为反向法线整模复制品，披风面与战斧几何已从 DCC 彻底剥离（材质隐藏无效）。
- **披风布料**：Chaos Cloth Asset `CA_Darius_Cape` 绑定 Section 1；固定组名必须为纯文本 `SimVertices3D`，权重映射为 `MaxDistance`。
- **移动动力学真值**：
  - `CharacterMovementComponent.MaxWalkSpeed = 220.0`，`MaxAcceleration = 1000.0`，`BrakingDecelerationWalking = 1400.0`，`GroundFriction = 6.0`。
  - `SpringArm`：`TargetArmLength = 380.0`，`SocketOffset = (0, 45, 20)`，`TargetOffset = (0, 0, 50)`，`CameraLag = 9.0`，`RotLag = 12.0`。
  - `PlayerStart`：初始俯角 `pitch = -12.0°`。
  - `BS_Darius_Locomotion`：Speed 轴 `[0, 220]`，满速 Walk 样本 `RateScale = 1.48`（脚底滑差率 0.10%）。

## 3. 动画与分层合并
- 上下半身合并走 UE 骨骼轨道改写（`AnimationDataController`），不走 Blender。
- 必须校验腿-臂摆动相位（一阶谐波，自然走路 ≈180°，合并产物已通过 185.3° 对齐）。
- `AnimationLibrary.get_raw_track_data` 对压缩动画返回空，一次性获取必须用 `get_bone_poses_for_frame`。
- 动画改写三铁律：改完必须验数值 + 验是否在动；改写前先备份；严禁在 slate post-tick 回调中执行 `destroy_actor`。

## 4. 下一步行动纲领（转向 C++ 核心战斗）
- 资产地基已彻底稳定，下阶段全面启动 C++ 核心战斗框架开发。
- 优先推进：`AFightCharacter`（输入缓冲）→ `UFightMovementComponent`（闪避/冲刺）→ 命中检测扫掠（Hitbox Sweep）→ 顿帧与受击反馈（Hit Stop / Bleed）。
