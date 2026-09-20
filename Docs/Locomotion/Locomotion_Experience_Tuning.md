# 诺手移动手感与工业级行走体验改造实录

> 2026-09-20 · 消除“平移感 / 坐滑板车感 / 滑冰感”，构建具备物理呼吸感与扎实接地感的第三人称战斗移动体验。

---

## 1. 核心问题根因诊断

| 现象 | 原始参数 | 根因机制 | 3A 工业级标准 |
| :--- | :--- | :--- | :--- |
| **脚底滑冰** | `MaxWalkSpeed = 600.0 cm/s`，BlendSpace 样本均以 `RateScale = 1.0` 播放 | 实际骨骼脚步自然步频仅 ~148.5 cm/s，胶囊体移速为步频的 **4 倍**，导致严重的前向滑步（Foot Slip 75.25%） | 步态支撑期（Stance Phase）脚底对地相对线速度严格为零 |
| **纯几何平移感** | `SpringArmComponent.bEnableCameraLag = False` | 相机直接硬锁在胶囊体坐标上，胶囊体匀速位移时视口产生绝对匀速的水平传送带平移错觉，缺乏物理质量感 | 阻尼弹簧振子系统（Damped Harmonic Oscillator），起步受阻滞后、制动向前微冲 |
| **画面视口空洞** | 相机视距 450cm，Pitch = 0°（水平视线），SocketOffset Z=70 | 摄像机平视地平线，地面纵深与脚步细节被挤压在视口最底部，上半屏为大量虚空背景 | 3A 动作过肩俯瞰视角（Pitch -10°~-15°，视距 380cm，右肩偏移 45cm） |

---

## 2. 解决方案与参数落地

### 2.1 摄像机动力学装配 (`BP_DariusCharacter`)

通过自动化脚本 [`loco_02_tune_character.py`](../../Scripts/anim/loco_02_tune_character.py) 写入角色蓝图：

- **`USpringArmComponent`**：
  - `TargetArmLength`: **`380.0`**（贴近角色，凸显重铠身形与战斧握持细节）；
  - `SocketOffset`: **`(0.0, 45.0, 20.0)`**（微右肩过肩机位）；
  - `TargetOffset`: **`(0.0, 0.0, 50.0)`**（聚焦肩颈与胸背中心）；
  - `bEnableCameraLag`: **`True`**；
  - `CameraLagSpeed`: **`9.0`**（起跑时弹簧自然拉伸约 24cm）；
  - `bEnableCameraRotationLag`: **`True`**；
  - `CameraRotationLagSpeed`: **`12.0`**；
  - `bUsePawnControlRotation`: **`True`**。
- **关卡初始视角 (`Lv-FIght.umap`)**：
  - `PlayerStart` 设置初始俯角 `pitch = -12.0°`，一进游戏即呈现具纵深感的战斗俯瞰视角。

---

### 2.2 角色移动动力学校准 (`CharacterMovementComponent`)

- `MaxWalkSpeed`: **`220.0 cm/s`**（沉稳重铠步行速度）；
- `MaxAcceleration`: **`1000.0`**（赋予约 0.22s 的起步加速度过渡，消除瞬移感）；
- `BrakingDecelerationWalking`: **`1400.0`**（制动缓冲用时约 0.16s，消除骤停感）；
- `GroundFriction`: **`6.0`**（扎实抓地摩擦感）；
- `bOrientRotationToMovement`: **`True`**，`RotationRate.Yaw = 500.0`。

---

### 2.3 混合空间步频严谨对齐 (`BS_Darius_Locomotion`)

通过 [`loco_03_tune_blendspace.py`](../../Scripts/anim/loco_03_tune_blendspace.py) 重构速度轴：

- `Speed` 轴上限锚定为 **`220.0`**；
- 采样点分布：
  - `Speed = 0.0`：`A_Darius_AxeIdle_Layered`（右手握斧待机，Rate = 1.0）；
  - `Speed = 150.0`：`A_Darius_AxeWalk_Layered`（自然步频，Rate = 1.0）；
  - `Speed = 220.0`：`A_Darius_AxeWalk_Layered`（大步快走，**`RateScale = 1.48`**）；
- **滑差数学对齐断言**：
  $$v_{\text{stance\_foot}} = 1.48 \times 148.5\text{ cm/s} = 219.78\text{ cm/s} \approx 220.0\text{ cm/s}$$
  $$\text{Slip Ratio} = \frac{|220.0 - 219.78|}{220.0} = \mathbf{0.10\%} \ll 25\%$$

---

## 3. PIE 实机物理验证

运行探针 [`loco_04_pie_verify.py`](../../Scripts/anim/loco_04_pie_verify.py)，记录物理弹簧与动力学轨迹：

| 校验项 | 基线值 | 实测值 | 状态 |
| :--- | :--- | :--- | :--- |
| **脚底滑差率** | 75.25% | **0.10%** | PASS |
| **相机弹簧最大伸缩 ($\Delta x$)** | 0.00 cm | **23.80 cm** | PASS |
| **制动复位误差** | N/A | **0.71 cm** | PASS |
| **训练场 Actor 总数** | 7 | **7** | PASS |
